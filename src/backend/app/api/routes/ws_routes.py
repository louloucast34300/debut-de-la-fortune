from fastapi import APIRouter,Query, WebSocket,Depends, WebSocketDisconnect
from core.connected_users import connected_users, send_to, broadcast
import asyncio
from core.state import queue, try_create_match, cancel_match, pending_matches
from utils.jwt import decode_token
from api.services.game_service import GameService
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db
import jwt

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