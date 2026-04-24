from fastapi import WebSocket

connected_users: dict[str, WebSocket] = {}

async def send_to(user_id: str, payload: dict):
    ws = connected_users.get(user_id)
    if ws:
        await ws.send_json(payload)

async def broadcast(user_ids:list[str], payload:dict):
    for uid in user_ids:
        await send_to(uid, payload)