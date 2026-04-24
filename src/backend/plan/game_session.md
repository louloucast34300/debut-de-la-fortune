# Plan — Sessions de jeu & présence des joueurs

## Principe

La table `sessions` gère uniquement l'authentification.
La présence en jeu et la partie en cours sont gérées séparément.

---

## Tables (implémentées)

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
    status TEXT NOT NULL DEFAULT 'active',   -- active, surrendered
    result TEXT                              -- winner, loser, abandoned (fin de partie)
);
```

---

## Cycle de vie d'une partie

```
Matchmaking accepté (2 joueurs)
    ↓
INSERT games (status='waiting')  ← flush() pour récupérer l'id
INSERT game_participants x2 (status='active')
    ↓
┌─ Joueur abandonne ──────────────────────────────────────────┐
│  POST /api/v1/game/surrender                                │
│  game_participants.status = 'surrendered'                   │
│  redirect → /root/dashboard                                 │
└─────────────────────────────────────────────────────────────┘
┌─ Fin normale (non implémentée) ─────────────────────────────┐
│  game_participants.result = 'winner' | 'loser'              │
│  games.status = 'finished'                                  │
└─────────────────────────────────────────────────────────────┘
```

Les lignes sont **conservées** pour permettre un historique et des stats par joueur.

---

## Présence en temps réel (WebSocket)

- Connexion ouverte dès que l'utilisateur entre dans le layout authentifié (`/root/`)
- Le serveur maintient un dict en mémoire : `connected_users: dict[str, WebSocket] = {}`
- Fenêtre fermée / onglet fermé → `WebSocketDisconnect` → joueur retiré de la file ou du pending match

---

## Matchmaking — File d'attente et acceptation (implémenté)

### Stockage en mémoire

```python
# app/core/state.py
queue: list[str] = []  # user_ids en attente

@dataclass
class PendingMatch:
    players: list[dict]  # [{"id": "...", "accepted": None | True}]

pending_matches: dict[str, PendingMatch] = {}  # proposal_id → PendingMatch
```

### Flux complet

```
[Bouton "Jouer"]
    ↓ WS message: { type: "join_queue" }
queue.append(user_id)
broadcast(queue, { type: "queued", count: len(queue) })  ← TOUS les joueurs en file
    ↓
Dès que len(queue) >= 2 :
    players = queue.pop(0..1)
    proposal_id = uuid4()
    pending_matches[proposal_id] = PendingMatch(players)
    broadcast → 2 joueurs : { type: "match_found", proposal_id, player_ids }
    ↓
[Modale "Match trouvé" + countdown 20s]
    ↓ WS message: { type: "accept_match", proposal_id }
player["accepted"] = True
broadcast → 2 joueurs : { type: "player_accepted", user_id }
    ↓
┌─ Les 2 acceptent ───────────────────────────────────────────┐
│  del pending_matches[proposal_id]                           │
│  INSERT games + game_participants x2 (BDD)                  │
│  broadcast → 2 joueurs : { type: "match_ready", game_id }   │
│  Redirect → /root/room/{game_id}                            │
└─────────────────────────────────────────────────────────────┘
┌─ Refus / timeout / déconnexion ─────────────────────────────┐
│  WS message: { type: "cancel_match", proposal_id }          │
│  (aussi déclenché auto si countdown → 0 ou WebSocketDisconnect) │
│  del pending_matches[proposal_id]                           │
│  Tous sauf le refuseur → re-queués                          │
│  Re-queués reçoivent : { type: "requeued" }                 │
│  Refuseur reçoit : { type: "match_cancelled" }              │
└─────────────────────────────────────────────────────────────┘
```

### WebSocket events (serveur → client)

| Event | Payload | Déclencheur |
|---|---|---|
| `queued` | `{ count }` | Quelqu'un rejoint ou quitte la file (broadcast à tous) |
| `match_found` | `{ proposal_id, player_ids }` | 2 joueurs dispo |
| `player_accepted` | `{ user_id }` | Un joueur vient d'accepter |
| `match_ready` | `{ game_id }` | Les 2 ont accepté |
| `requeued` | `{}` | Match annulé, joueur re-mis en file |
| `match_cancelled` | `{}` | Match annulé, joueur pas re-queué |
| `match_error` | `{ message }` | Erreur BDD à la création de partie |

### Gestion du timeout

Timer 20s géré côté **frontend** (setInterval). À l'expiration, le frontend envoie `cancel_match` via WS.
Même logique exécutée sur `WebSocketDisconnect`.

---

## Routes HTTP jeu

| Méthode | Route | Action |
|---|---|---|
| POST | `/api/v1/game/surrender` | Met `game_participants.status = 'surrendered'` pour l'utilisateur connecté |
