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
    status TEXT NOT NULL DEFAULT 'active'  -- active, disconnected, finished
);
```

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

## TODO

- [ ] Créer les tables `games` et `game_participants` dans `create_tables.sh`
- [ ] Créer les modèles ORM `Game` et `GameParticipant`
- [ ] Endpoint WebSocket `/ws/{user_id}` avec vérification du `access_token`
- [ ] Route `GET /game/current` — retourne la partie active du joueur
- [ ] Mettre à jour le `status` du participant quand il se déconnecte (WebSocketDisconnect)
- [ ] Notifier les autres joueurs de la partie quand un joueur se reconnecte/déconnecte
