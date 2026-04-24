# Plan — Sessions de jeu & présence des joueurs

## Principe

La table `sessions` gère uniquement l'authentification.
La présence en jeu et la partie en cours sont gérées séparément.

---

## Tables à créer

```sql
CREATE TABLE games (
    id UUID PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'waiting',  -- waiting, in_progress, finished
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE game_participants (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    game_id UUID REFERENCES games(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'active',  -- active, finished, abandoned
    result TEXT  -- winner, loser, abandoned (rempli en fin de partie)
);
```

---

## Cycle de vie d'une partie

```
Joueur rejoint
    ↓
INSERT games (status='waiting')
INSERT game_participants (status='active')
    ↓
Partie lance → games.status = 'in_progress'
    ↓
┌─ Joueur abandonne ──────────────────────────────────┐
│  game_participants.status = 'abandoned'             │
│  game_participants.result = 'abandoned'             │
│  games.status = 'finished' (si plus personne actif)│
└─────────────────────────────────────────────────────┘
┌─ Fin normale ───────────────────────────────────────┐
│  game_participants.status = 'finished'              │
│  game_participants.result = 'winner' | 'loser'      │
│  games.status = 'finished'                          │
└─────────────────────────────────────────────────────┘
```

Les lignes sont **conservées** pour permettre un historique et des stats par joueur.

---

## Présence en temps réel (WebSocket)

- Quand un joueur ouvre la page de jeu → il ouvre une connexion WebSocket
- Le serveur maintient un dict en mémoire : `connected_users: dict[str, WebSocket] = {}`
- Connexion ouverte → joueur "en ligne"
- Fenêtre fermée / onglet fermé → `WebSocketDisconnect` → joueur retiré du dict

```python
connected_users: dict[str, WebSocket] = {}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    connected_users[user_id] = websocket
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        del connected_users[user_id]
```

---

## Reconnexion à une partie en cours

Quand un joueur rerouvre la page :

1. Frontend envoie le `refresh_token`
2. Backend vérifie la session → retourne un nouvel `access_token` + `user_id`
3. Backend cherche une partie active :

```sql
SELECT game_id FROM game_participants
WHERE user_id = $1 AND status = 'active'
LIMIT 1;
```

4. Si trouvé → redirection automatique vers la partie en cours

---

## Matchmaking — File d'attente et acceptation

### Principe UX

- Pas de page dédiée — la file d'attente s'affiche via une **modale** + un **indicateur dans la navbar**
- La modale se rouvre automatiquement quand un match est trouvé (3 joueurs)
- Chaque joueur doit **accepter** dans un délai imparti
- Si un joueur n'accepte pas → les autres sont re-queués

### Stockage en mémoire (pas de BDD)

La file et les proposals vivent en mémoire Python. Seule la création de la partie (`games` + `game_participants`) est persistée en BDD.

```python
# app/core/state.py — singleton partagé dans toute l'app FastAPI
from dataclasses import dataclass, field
import time

queue: list[str] = []  # user_ids en attente

@dataclass
class PendingMatch:
    players: list[dict]   # [{"id": "123", "accepted": None}, ...]

pending_matches: dict[str, PendingMatch] = {}  # proposal_id → PendingMatch
```

### Flux complet

```
[Bouton "Jouer" (navbar)]
    ↓ WS message: { type: "join_queue" }
queue.append(user_id)
WS event → joueur: { type: "queued", count: len(queue) }
    ↓
[Tracker navbar : "En attente... (1/3)"]
    ↓
Dès que len(queue) >= 3 :
    players = queue.pop(0..2)   # retire les 3 premiers
    proposal_id = uuid4()
    pending_matches[proposal_id] = PendingMatch(players)
    WS event → 3 joueurs : { type: "match_found", proposal_id }
    ↓
[Modale "Match trouvé — Accepter ?" + timer 30s]
    ↓ WS message: { type: "accept_match", proposal_id }
player["accepted"] = True
    ↓
┌─ Tous acceptent ──────────────────────────────────────┐
│  del pending_matches[proposal_id]                     │
│  INSERT games + game_participants x3  (BDD)           │
│  WS event → 3 joueurs : { type: "match_ready",        │
│                            game_id }                  │
│  Redirect → /game/{game_id}                           │
└───────────────────────────────────────────────────────┘
┌─ Refus explicite ─────────────────────────────────────┐
│  WS message: { type: "cancel_match", proposal_id }    │
│  (aussi déclenché par WebSocketDisconnect)            │
│  del pending_matches[proposal_id]                     │
│  Joueurs avec accepted=True → queue.append(user_id)   │
│  Joueur qui a annulé/déconnecté → pas re-queué        │
│  WS event selon le cas (requeued / match_cancelled)   │
└───────────────────────────────────────────────────────┘
```

### WebSocket events (serveur → client)

| Event | Payload | Déclencheur |
|---|---|---|
| `queued` | `{ count }` | Joueur rejoint la file |
| `queue_update` | `{ count }` | Quelqu'un rejoint/quitte la file |
| `match_found` | `{ proposal_id }` | 3 joueurs dispo |
| `match_ready` | `{ game_id }` | 3 joueurs ont accepté |
| `requeued` | `{}` | Match annulé, joueur re-queué |
| `match_cancelled` | `{}` | Match annulé, joueur pas re-queué |

### Gestion du timeout

Pas de background task. Le timer est **géré côté frontend** (30s).
À l'expiration, le frontend envoie `{ type: "cancel_match", proposal_id }` via WS.

Le même code de cancel est aussi appelé sur `WebSocketDisconnect` :

```python
except WebSocketDisconnect:
    del connected_users[user_id]
    # Si le joueur était dans un pending_match → cancel + requeue les autres
    for proposal_id, match in list(pending_matches.items()):
        ids = [p["id"] for p in match.players]
        if user_id in ids:
            cancel_match(proposal_id, cancelled_by=user_id)
            break
```

### Frontend — structure

```
app/
  features/
    matchmaking/
      matchmaking.tsx          ← modale (s'affiche sur n'importe quelle page)
      matchmaking.type.ts
      matchmaking.scss
  layout.tsx                   ← monte le WebSocket + MatchmakingModal ici
```

### État global (Zustand)

```typescript
interface MatchmakingStore {
  isInQueue: boolean
  queueCount: number
  matchProposalId: string | null
  matchExpiresAt: number | null
  gameId: string | null         // rempli quand match_ready → redirect /game/{id}
}
```

---

## TODO

- [x] Créer les tables `games` et `game_participants` dans `create_tables.sh`
- [x] Créer les modèles ORM `Game` et `GameParticipant`
- [ ] Créer `app/core/state.py` avec `queue`, `pending_matches`
- [ ] Endpoint WebSocket `/ws/{user_id}` avec vérification du `access_token`
- [ ] Logique matchmaking dans le handler WS (`join_queue`, `accept_match`, `cancel_match`)
- [ ] Logique cancel sur `WebSocketDisconnect` (requeue les autres joueurs)
- [ ] Route `GET /game/current` — retourne la partie active du joueur (BDD)
- [ ] Frontend : store Zustand `matchmaking`
- [ ] Frontend : `MatchmakingModal` dans `layout.tsx`
- [ ] Frontend : indicateur navbar (tracker file d'attente)
- [ ] Mettre à jour le `status` du participant quand il se déconnecte (WebSocketDisconnect)
- [ ] Notifier les autres joueurs de la partie quand un joueur se reconnecte/déconnecte
- [ ] Route `POST /queue/accept` — accepter le match, créer la partie si tous OK
- [ ] Background task pour expire les proposals timeout
- [ ] Route `GET /game/current` — retourne la partie active du joueur
- [ ] Frontend : store Zustand `matchmaking`
- [ ] Frontend : `MatchmakingModal` dans `layout.tsx`
- [ ] Frontend : indicateur navbar (tracker file d'attente)
- [ ] Mettre à jour le `status` du participant quand il se déconnecte (WebSocketDisconnect)
- [ ] Notifier les autres joueurs de la partie quand un joueur se reconnecte/déconnecte
