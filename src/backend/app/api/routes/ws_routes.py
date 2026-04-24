from fastapi import APIRouter,Query, WebSocket,Depends, WebSocketDisconnect
from core.connected_users import connected_users, send_to, broadcast
from core.state import queue, try_create_match, cancel_match, pending_matches
from utils.jwt import decode_token
from api.services.game_service import GameService
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db
import jwt

router = APIRouter()
game_service = GameService()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, token: str=Query(...), db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        await websocket.close(code=4001) #code custom "token expiré"
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

        case "join_queue":
            if user_id not in queue:
                queue.append(user_id)
            await send_to(user_id, {"type": "queued", "count": len(queue)})

            result = try_create_match()
            if result:
                proposal_id, match = result
                player_ids = [p["id"] for p in match.players]
                await broadcast(player_ids, {"type": "match_found", "proposal_id": proposal_id})

        case "leave_queue":
            if user_id in queue:
                queue.remove(user_id)

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

        case "cancel_match":
            proposal_id = data.get("proposal_id")
            if not proposal_id:
                return
            requeued = cancel_match(proposal_id, cancelled_by=user_id)
            await broadcast(requeued, {"type": "requeued"})
            await send_to(user_id, {"type": "match_cancelled"})


async def handle_disconnect(user_id: str):
    # Joueur en file → le retirer
    if user_id in queue:
        queue.remove(user_id)

    # Joueur dans un pending match → annuler le match
    for proposal_id, match in list(pending_matches.items()):
        if any(p["id"] == user_id for p in match.players):
            requeued = cancel_match(proposal_id, cancelled_by=user_id)
            await broadcast(requeued, {"type": "requeued"})
            break