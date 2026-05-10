from fastapi import APIRouter,Query, WebSocket,Depends, WebSocketDisconnect
from core.connected_users import connected_users, send_to, broadcast
import asyncio
from core.state import queue, try_create_match, cancel_match, pending_matches, active_games
from utils.jwt import decode_token
from api.services.game_service import GameService
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db
import jwt
from domains.game import Game, Manche

router = APIRouter()
game_service = GameService()

MATCH_TIMEOUT = 20  # secondes

async def match_timeout(proposal_id: str):
    """Cas n°4 : timeout 20s → les deux joueurs sortent de la recherche sans re-queue."""
    await asyncio.sleep(MATCH_TIMEOUT)
    match = pending_matches.pop(proposal_id, None)
    if match:
        player_ids = [p["id"] for p in match.players]
        await broadcast(player_ids, {"type": "match_cancelled"})

NEW_MANCHE_DELAY = 10  # secondes

async def manche_delay(game_id: str):
    await asyncio.sleep(NEW_MANCHE_DELAY)
    game_instance = active_games.get(game_id)
    if not game_instance or game_instance.game["party"]["step"] != "manche_completed":
        return
    number_manche = len(game_instance.game["manches"]) + 1
    game_instance.add_manche(number_manche)
    game_instance.define_started_player()
    game_instance.game["party"]["step"] = "choosing_wheel_value"
    player_ids = [p["id"] for p in game_instance.game["players"]]
    await broadcast(player_ids, {"type": "game_update", "game": game_instance.game})

@router.websocket("/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, token: str=Query(...), db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        await websocket.close(code=4001)
        return
    except jwt.InvalidTokenError:
        await websocket.close(code=4002)
        return 
    
    if payload["sub"] != user_id:
        await websocket.close(code=4003)
        return 

    await websocket.accept()
    connected_users[user_id] = websocket

    try:
        while True:
            data = await websocket.receive_json()
            await handle_message(user_id, data, db)

    except WebSocketDisconnect:
        del connected_users[user_id]
        await handle_disconnect(user_id)


async def handle_message(user_id: str, data: dict, db:AsyncSession):

    match data.get("type"):

        ## "join-queue"
        case "join_queue":
            if user_id not in queue:
                queue.append(user_id)
            await broadcast(queue, {"type": "queued", "count": len(queue)})

            result = try_create_match()
            if result:
                proposal_id, match = result
                player_ids = [p["id"] for p in match.players]
                await broadcast(player_ids, {"type": "match_found", "proposal_id": proposal_id, "player_ids": player_ids})
                asyncio.create_task(match_timeout(proposal_id))

        ## "leave_queue"
        case "leave_queue":
            if user_id in queue:
                queue.remove(user_id)
            await send_to(user_id, {"type": "match_cancelled"})
            await broadcast(queue, {"type": "queued", "count": len(queue)})

        ## "accept_match"
        case "accept_match":
            proposal_id = data.get("proposal_id")
            if not proposal_id:
                return
            match = pending_matches.get(proposal_id)
            if not match:
                return

            for player in match.players:
                if player["id"] == user_id:
                    player["accepted"] = True

            player_ids = [p["id"] for p in match.players]
            await broadcast(player_ids, {"type": "player_accepted", "user_id": user_id})

            # Tous ont accepté ?
            if all(p["accepted"] is True for p in match.players):
                player_ids = [p["id"] for p in match.players]
                game = await game_service.createGame(db, player_ids)
                if not game["success"]:
                    pending_matches.pop(proposal_id, None)
                    for pid in player_ids:
                        queue.append(pid)
                    await broadcast(player_ids, {"type": "match_error", "message": game["message"]})
                    return
                pending_matches.pop(proposal_id, None)

                game_instance = Game()

                game_instance.add_manche(1)
 

                game_instance.add_players(game["players"])
                
                active_games[game["game_id"]] = game_instance
                await broadcast(player_ids, {"type": "match_ready", "game_id": game["game_id"]})
                
        ## "cancel_match"
        case "cancel_match":
            proposal_id = data.get("proposal_id")
            if not proposal_id:
                return
            match = pending_matches.get(proposal_id)
            if not match:
                return
            # Cas 2 & 3 : refus explicite → tous les autres repartent en recherche
            others = cancel_match(proposal_id, cancelled_by=user_id)
            await send_to(user_id, {"type": "match_cancelled"})
            for pid in others:
                queue.append(pid)
            if others:
                await broadcast(others, {"type": "requeued", "count": len(queue)})
                result = try_create_match()
                if result:
                    new_proposal_id, new_match = result
                    new_player_ids = [p["id"] for p in new_match.players]
                    
                    await broadcast(new_player_ids, {"type": "match_found", "proposal_id": new_proposal_id, "player_ids": new_player_ids})
                    asyncio.create_task(match_timeout(new_proposal_id))

        ## ============ GAME EVENTS ========================= ##
        case "start_game":
            game_id = data.get("game_id")
            if not game_id:
                return
            game_instance = active_games.get(game_id)
            if not game_instance:
                return
            # Rejoin : la partie est déjà en cours, on renvoie l'état courant uniquement au joueur qui reconnecte
            if game_instance.game["party"]["step"] != "":
                await send_to(user_id, {"type": "game_update", "game": game_instance.game})
                return
            # Premier démarrage : on initialise et on broadcast à tous
            player_ids = [p["id"] for p in game_instance.game["players"]]
            game_instance.game["party"]["step"] = "choosing_random_player"
            await broadcast(player_ids, {"type": "game_update", "game": game_instance.game})
        
        case "choose_started_player":
            game_id = data.get("game_id")
            if not game_id:
                return
            game_instance: Game | None = active_games.get(game_id)
            if not game_instance:
                return
            # Idempotent : on n'exécute que si on est encore dans la bonne étape
            if game_instance.game["party"]["step"] != "choosing_random_player":
                return
            game_instance.define_started_player()
            game_instance.game["party"]["step"] = "choosing_wheel_value"
            player_ids = [p["id"] for p in game_instance.game["players"]]
            await broadcast(player_ids, {"type": "game_update", "game": game_instance.game})
        
        case "choose_wheel_value":
            game_id = data.get("game_id")
            current_gain = data.get("current_gain")
            if not game_id or not current_gain:
                return
            game_instance: Game | None = active_games.get(game_id)
            if not game_instance:
                return
            if game_instance.game["party"]["step"] != "choosing_wheel_value":
                return
            if current_gain == "banqueroot":
                current_player = next((p for p in game_instance.game["players"] if p["id"] == user_id), None)
                if not current_player:
                    return
                current_player["cagnotte"] = 0
                game_instance.next_player_action()
                game_instance.game["party"]["step"] = "choosing_wheel_value"
                player_ids = [p["id"] for p in game_instance.game["players"]]
                await broadcast(player_ids, {"type": "game_update", "game": game_instance.game})
            else:
                game_instance.game["party"]["current_gain"] = current_gain
                game_instance.game["party"]["step"] = "choosing_pendu_letter"
                player_ids = [p["id"] for p in game_instance.game["players"]]
                await broadcast(player_ids, {"type": "game_update", "game": game_instance.game})

        case "choose_pendu_letter":
            game_id = data.get("game_id") 
            letter = data.get("letter")
            if not game_id or not letter:
                return
            game_instance: Game | None = active_games.get(game_id)
            if not game_instance:
                return           
            player_ids = [p["id"] for p in game_instance.game["players"]]
            #1) vérifier la lettre 
            idx_finded = [i for i, x in enumerate(list(game_instance.game["party"]["pendu"]["secret_word"])) if x == letter]
            
            if len(idx_finded) == 0:
                message = {
                    "success": False, 
                    "message": "Mauvaise lettre", 
                    "nbr_of_letter_found": 0,
                    "code_error": 1,
                    "word_completed": False
                }
                await broadcast(player_ids, {"type": "letter_result", **message})
                #2) si mauvaise → passer au joueur suivant
                game_instance.next_player_action()
                game_instance.game["party"]["step"] = "choosing_wheel_value"
                await broadcast(player_ids, {"type": "game_update", "game": game_instance.game})
                return

            parsed_word_list = list(game_instance.game["party"]["pendu"]["parsed_word"])
            for i in idx_finded:
                if parsed_word_list[i] != "_":
                    message = {
                        "success": False, 
                        "message": "Lettre déjà utilisée", 
                        "nbr_of_letter_found": 0,
                        "code_error": 2,
                        "word_completed": False
                    }
                    await broadcast(player_ids, {"type": "letter_result", **message})
                                   #2) si mauvaise → passer au joueur suivant
                    game_instance.next_player_action()
                    game_instance.game["party"]["step"] = "choosing_wheel_value"
                    await broadcast(player_ids, {"type": "game_update", "game": game_instance.game})
                    return
                parsed_word_list[i] = letter

            game_instance.game["party"]["pendu"]["parsed_word"] = "".join(parsed_word_list)
            word_completed = "_" not in game_instance.game["party"]["pendu"]["parsed_word"]
            message = {
                "success": True, 
                "message": "Bonne lettre", 
                "nbr_of_letter_found": len(idx_finded),
                "code_error": 0,
                "word_completed": word_completed
            }
            current_player = next((p for p in game_instance.game["players"] if p["id"] == user_id), None)
            if not current_player:
                return
            current_player["cagnotte"] += game_instance.game["party"]["current_gain"] * message["nbr_of_letter_found"]
            # update cagnotte

            await broadcast(player_ids, {"type": "letter_result", **message})

            #3) vérifier si le mot est complété ou non
            if not word_completed:
                # pas complet → même joueur retourne à choosing_pendu_letter
                game_instance.game["party"]["step"] = "choosing_wheel_value"
            elif len(game_instance.game["manches"]) >= 3:
                # 3ème manche terminée → fin de partie
                game_instance.game["party"]["step"] = "game_over"
            else:
                # manche terminée mais pas la dernière → prochaine manche dans NEW_MANCHE_DELAY secondes
                game_instance.game["party"]["step"] = "manche_completed"
                game_instance.finish_manche()
                asyncio.create_task(manche_delay(game_id))

            await broadcast(player_ids, {"type": "game_update", "game": game_instance.game})



            

        

            
            
            



async def handle_disconnect(user_id: str):
    # Joueur en file → le retirer
    if user_id in queue:
        queue.remove(user_id)

    # Joueur dans un pending match → traité comme un refus → les autres repartent en recherche
    for proposal_id, match in list(pending_matches.items()):
        if any(p["id"] == user_id for p in match.players):
            others = cancel_match(proposal_id, cancelled_by=user_id)
            for pid in others:
                queue.append(pid)
            if others:
                await broadcast(others, {"type": "requeued", "count": len(queue)})
                result = try_create_match()
                if result:
                    new_proposal_id, new_match = result
                    new_player_ids = [p["id"] for p in new_match.players]
                    await broadcast(new_player_ids, {"type": "match_found", "proposal_id": new_proposal_id, "player_ids": new_player_ids})
                    asyncio.create_task(match_timeout(new_proposal_id))
            break