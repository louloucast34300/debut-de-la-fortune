# WebSockets — Guide complet pour ce projet

## C'est quoi un WebSocket ?

HTTP classique : le client envoie une requête → le serveur répond → la connexion se ferme.

WebSocket : le client et le serveur ouvrent **une connexion persistante**. Les deux peuvent s'envoyer des messages à tout moment, dans les deux sens, sans que l'autre ait besoin de demander.

```
HTTP :
  Client ──[GET /data]──────────────────▶ Serveur
  Client ◀──[200 OK + données]─────────── Serveur
  (connexion fermée)

WebSocket :
  Client ──[Handshake ws://...]──────────▶ Serveur
  Client ◀──────────────────────────────── Serveur  ← connexion ouverte
  Client ──[message]─────────────────────▶ Serveur
  Client ◀──[message]──────────────────── Serveur
  Client ◀──[message]──────────────────── Serveur  ← le serveur push sans qu'on demande
  ...
```

**Pourquoi en a-t-on besoin ici ?**
- Quand un 3ème joueur rejoint la file → le serveur doit **prévenir les 2 autres** sans qu'ils aient fait de requête
- Quand un match est trouvé → le serveur doit **ouvrir la modale** sur les 3 navigateurs simultanément
- Pendant une partie → les actions d'un joueur doivent apparaître **en temps réel** chez les autres

---

## Backend — FastAPI + WebSockets

### Installation

Rien à installer en plus. FastAPI gère les WebSockets nativement avec `websockets` (déjà une dépendance de `uvicorn`).

### Anatomie d'un endpoint WebSocket

```python
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    # 1. Accepter la connexion (obligatoire, sinon elle reste en attente)
    await websocket.accept()

    # 2. Stocker la connexion pour pouvoir envoyer des messages plus tard
    connected_users[user_id] = websocket

    try:
        # 3. Boucle infinie — on attend les messages du client
        while True:
            data = await websocket.receive_json()
            # data = {"type": "join_queue"} par exemple
            await handle_message(user_id, data)

    except WebSocketDisconnect:
        # 4. Le client a fermé l'onglet ou perdu la connexion
        del connected_users[user_id]
        await handle_disconnect(user_id)
```

### Envoyer un message à UN joueur

```python
# connected_users est le dict de toutes les connexions ouvertes
connected_users: dict[str, WebSocket] = {}

async def send_to(user_id: str, payload: dict):
    ws = connected_users.get(user_id)
    if ws:
        await ws.send_json(payload)
```

### Envoyer un message à PLUSIEURS joueurs (broadcast)

```python
async def broadcast(user_ids: list[str], payload: dict):
    for user_id in user_ids:
        await send_to(user_id, payload)
```

---

## Structure des messages

On utilise une convention `type` pour identifier l'événement, comme dans Redux ou les events du navigateur.

```python
# Serveur → Client
{"type": "queued", "count": 2}
{"type": "match_found", "proposal_id": "abc-123"}
{"type": "match_ready", "game_id": "xyz-456"}
{"type": "requeued"}
{"type": "match_cancelled"}

# Client → Serveur
{"type": "join_queue"}
{"type": "leave_queue"}
{"type": "accept_match", "proposal_id": "abc-123"}
{"type": "cancel_match", "proposal_id": "abc-123"}
```

---

## Implémentation complète pour ce projet

### `app/core/connected_users.py`

```python
from fastapi import WebSocket

connected_users: dict[str, WebSocket] = {}

async def send_to(user_id: str, payload: dict):
    ws = connected_users.get(user_id)
    if ws:
        await ws.send_json(payload)

async def broadcast(user_ids: list[str], payload: dict):
    for uid in user_ids:
        await send_to(uid, payload)
```

### `app/api/routes/ws_routes.py`

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.connected_users import connected_users, send_to, broadcast
from app.core.state import queue, try_create_match, cancel_match

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    connected_users[user_id] = websocket

    try:
        while True:
            data = await websocket.receive_json()
            await handle_message(user_id, data)

    except WebSocketDisconnect:
        del connected_users[user_id]
        await handle_disconnect(user_id)


async def handle_message(user_id: str, data: dict):
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
            match = pending_matches.get(proposal_id)
            if not match:
                return

            for player in match.players:
                if player["id"] == user_id:
                    player["accepted"] = True

            # Tous ont accepté ?
            if all(p["accepted"] is True for p in match.players):
                player_ids = [p["id"] for p in match.players]
                # → créer la partie en BDD ici (appel service)
                # game_id = await game_service.createGame(db, player_ids)
                await broadcast(player_ids, {"type": "match_ready", "game_id": game_id})

        case "cancel_match":
            proposal_id = data.get("proposal_id")
            requeued = cancel_match(proposal_id, cancelled_by=user_id)
            await broadcast(requeued, {"type": "requeued"})
            await send_to(user_id, {"type": "match_cancelled"})


async def handle_disconnect(user_id: str):
    # Joueur en file → le retirer
    if user_id in queue:
        queue.remove(user_id)

    # Joueur dans un pending match → annuler le match
    from app.core.state import pending_matches
    for proposal_id, match in list(pending_matches.items()):
        if any(p["id"] == user_id for p in match.players):
            requeued = cancel_match(proposal_id, cancelled_by=user_id)
            await broadcast(requeued, {"type": "requeued"})
            break
```

### Brancher le router dans `main.py`

```python
from app.api.routes.ws_routes import router as ws_router

app.include_router(ws_router)
```

---

## Sécuriser la connexion WebSocket

Le handshake WebSocket ne peut pas envoyer des headers Authorization classiques depuis le navigateur. Il faut passer le token en **query param** :

```
ws://localhost:8000/ws/USER_ID?token=eyJhbGci...
```

```python
from fastapi import WebSocket, Query, HTTPException
from app.utils.jwt import decode_token
import jwt

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    token: str = Query(...)  # récupéré depuis ?token=...
):
    # Vérifier le token avant d'accepter
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        await websocket.close(code=4001)  # code custom "token expiré"
        return
    except jwt.InvalidTokenError:
        await websocket.close(code=4002)
        return

    # Vérifier que user_id correspond au token
    if payload["sub"] != user_id:
        await websocket.close(code=4003)
        return

    await websocket.accept()
    ...
```

---

## Frontend — React / Next.js

### Principe

Le navigateur a une API WebSocket native, pas besoin de lib. On l'encapsule dans un hook React pour le cycle de vie.

### Hook `useWebSocket`

```typescript
// app/features/matchmaking/useWebSocket.ts
"use client"

import { useEffect, useRef } from "react"
import { useMatchmakingStore } from "@/app/stores/matchmakingStore"

export function useWebSocket(userId: string, accessToken: string) {
  const wsRef = useRef<WebSocket | null>(null)
  const { setQueued, setMatchFound, setMatchReady, setRequeued } = useMatchmakingStore()

  useEffect(() => {
    // Ouverture de la connexion
    const ws = new WebSocket(
      `${process.env.NEXT_PUBLIC_WS_URL}/ws/${userId}?token=${accessToken}`
    )
    wsRef.current = ws

    // Connexion établie
    ws.onopen = () => {
      console.log("WS connecté")
    }

    // Réception d'un message
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      switch (data.type) {
        case "queued":
          setQueued(true, data.count)
          break
        case "match_found":
          setMatchFound(data.proposal_id)
          break
        case "match_ready":
          setMatchReady(data.game_id)
          break
        case "requeued":
          setRequeued()
          break
        case "match_cancelled":
          setQueued(false, 0)
          break
      }
    }

    // Connexion fermée (serveur redémarré, réseau coupé...)
    ws.onclose = (event) => {
      console.log("WS fermé, code:", event.code)
    }

    // Erreur
    ws.onerror = (error) => {
      console.error("WS erreur:", error)
    }

    // Nettoyage quand le composant est démonté
    return () => {
      ws.close()
    }
  }, [userId, accessToken])

  // Exposer une fonction pour envoyer des messages
  const send = (payload: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload))
    }
  }

  return { send }
}
```

### Utilisation dans `layout.tsx`

```typescript
// app/layout.tsx
&"use client"

import { useWebSocket } from "@/app/features/matchmaking/useWebSocket"
import { MatchmakingModal } from "@/app/features/matchmaking/matchmaking"

export default function RootLayout({ children }) {
  // userId + accessToken récupérés depuis les cookies ou un store auth
  const { send } = useWebSocket(userId, accessToken)

  return (
    <html>
      <body>
        <Navbar onJoinQueue={() => send({ type: "join_queue" })} />
        <MatchmakingModal onAccept={(proposalId) => send({ type: "accept_match", proposal_id: proposalId })} />
        {children}
      </body>
    </html>
  )
}
```

### Envoyer un message au serveur

```typescript
// Rejoindre la file
send({ type: "join_queue" })

// Accepter un match
send({ type: "accept_match", proposal_id: proposalId })

// Annuler (timer expiré)
send({ type: "cancel_match", proposal_id: proposalId })

// Quitter la file
send({ type: "leave_queue" })
```

### Store Zustand pour l'état matchmaking

```typescript
// app/stores/matchmakingStore.ts
import { create } from "zustand"

interface MatchmakingStore {
  isInQueue: boolean
  queueCount: number
  proposalId: string | null
  gameId: string | null
  setQueued: (inQueue: boolean, count: number) => void
  setMatchFound: (proposalId: string) => void
  setMatchReady: (gameId: string) => void
  setRequeued: () => void
}

export const useMatchmakingStore = create<MatchmakingStore>((set) => ({
  isInQueue: false,
  queueCount: 0,
  proposalId: null,
  gameId: null,
  setQueued: (inQueue, count) => set({ isInQueue: inQueue, queueCount: count }),
  setMatchFound: (proposalId) => set({ proposalId }),
  setMatchReady: (gameId) => set({ gameId, proposalId: null }),
  setRequeued: () => set({ isInQueue: true, proposalId: null }),
}))
```

---

## Codes de fermeture WebSocket

Les codes `4000+` sont réservés aux applications (non standardisés par le protocole).

| Code | Signification dans ce projet |
|---|---|
| `1000` | Fermeture normale |
| `1001` | Onglet fermé par l'utilisateur |
| `4001` | Token expiré |
| `4002` | Token invalide |
| `4003` | user_id ne correspond pas au token |

---

## Points d'attention

- **`await websocket.accept()`** est obligatoire avant tout échange
- **Ne jamais faire `while True` sans `try/except WebSocketDisconnect`** — sinon une déconnexion crash le serveur
- **`ws.readyState === WebSocket.OPEN`** côté frontend avant chaque `send()` — la connexion peut se fermer à tout moment
- **Reconnexion automatique** : si le serveur redémarre, le client perd la connexion. Il faut implémenter une logique de retry dans `ws.onclose` (backoff exponentiel) — à faire quand ce sera nécessaire
