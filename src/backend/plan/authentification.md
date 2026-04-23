# Authentification — Documentation

## Stack

- **PyJWT** : génération et décodage des JWT
- **passlib[bcrypt]** : hashage des mots de passe
- **SQLAlchemy async** : persistance des sessions

---

## Tokens

### access_token (JWT)
- Durée : **1h**
- Payload : `sub` (user UUID), `pseudo`, `exp`, `iat`
- Signé avec `SECRET_KEY` (HS256)
- **Non stocké en BDD** — vérification cryptographique uniquement
- Stocké côté client en cookie `httpOnly`

### refresh_token (JWT)
- Durée : **30 jours**
- Payload : `sub` (user UUID), `exp`
- Stocké en BDD dans la table `sessions`
- Révocable instantanément par DELETE en BDD
- Stocké côté client en cookie `httpOnly`

### Comparaison

| | `access_token` | `refresh_token` |
|---|---|---|
| Vérification | Signature crypto, pas de BDD | Lookup en BDD |
| Durée | 1h | 30 jours |
| Révocable | ❌ Non | ✅ Oui (DELETE) |
| Stocké en BDD | ❌ Non | ✅ Oui |

---

## Logique du service (`AuthService`)

### `registerUser`
1. Hasher le password (`generate_new_salt`)
2. Générer `access_token` + `refresh_token` avant l'insertion
3. `db.add(User)` → `flush()` — insère le user en BDD sans clore la transaction (nécessaire pour satisfaire la FK de Session)
4. `db.add(Session)` → `commit()`
5. Gestion d'erreurs dans le `try/catch` global :
   - `IntegrityError` : email déjà utilisé (contrainte UNIQUE)
   - `Exception` : erreur BDD générique → rollback

```python
try:
    db.add(User(...))
    await db.flush()   # ← obligatoire avant Session (FK user_id)
    db.add(Session(...))
    await db.commit()
except IntegrityError:
    await db.rollback()
except Exception:
    await db.rollback()
```

### `loginUser`
1. Chercher le user par email (early return si absent)
2. Vérifier le password hashé (early return si incorrect)
3. Générer `access_token` + `refresh_token`
4. Insérer une nouvelle `Session` en BDD
5. Retourner les deux tokens

### `logoutUser`
1. Chercher la session par `refresh_token` (early return si absente)
2. `db.delete(session)` → `commit()`
3. La session est invalidée instantanément

### `refreshTokens`
1. Chercher la session par `refresh_token` (early return si absente)
2. Vérifier `expires_at > now()` (early return si expirée)
3. Charger le user depuis `session.user_id`
4. Générer un nouveau `access_token` + `refresh_token` (rotation)
5. Mettre à jour `session.refresh_token` et `session.expires_at` sur la ligne existante
6. Retourner les deux tokens

---

## Proxy Next.js (`proxy.ts`)

S'exécute avant chaque page protégée (sauf `/register` et assets).

```
requête
    ↓
proxy.ts
    ↓
header `next-action` présent ? → laisser passer (server actions)
    ↓
access_token présent ?
    ├── non → redirect /register
    └── oui → expiré ?
               ├── non → laisser passer
               └── oui → refresh_token présent ?
                          ├── non → redirect /register
                          └── oui → POST /auth/refresh
                                     ├── succès → set cookies → laisser passer
                                     └── échec → redirect /register
```

> Le proxy appelle le backend **directement** (pas via server action) pour pouvoir poser les cookies sur le `NextResponse`.

> `jwtDecode` lit le payload JWT sans vérifier la signature — pas besoin de `SECRET_KEY` côté frontend.

---

## Tables BDD

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    pseudo TEXT,
    email TEXT UNIQUE NOT NULL,
    password TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    refresh_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## Vérification du Bearer Token sur les routes protégées

FastAPI utilise une **dépendance** injectée dans les routes. Elle lit le header `Authorization: Bearer <token>`, vérifie la signature et l'expiration, et injecte le payload dans la route.

```python
# core/dependencies.py
import jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import SECRET_KEY

bearer_scheme = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    token = credentials.credentials  # extrait le token du header
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload  # {"sub": "uuid", "pseudo": "...", "exp": ...}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")
```

```python
# utilisation dans une route protégée
@router.get("/game")
async def get_game(current_user = Depends(get_current_user)):
    user_id = current_user["sub"]
    ...
```

**Ce qui se passe :**
1. FastAPI lit automatiquement `Authorization: Bearer <token>`
2. `jwt.decode()` vérifie la **signature** (SECRET_KEY) ET l'**expiration** — exception si invalide
3. Si valide → payload injecté dans la route, pas de requête BDD
4. Si invalide → `401` automatique

---

## TODO

### Backend
- [x] `PyJWT`, `passlib[bcrypt]` dans `requirements.txt`
- [x] Hashage du password au register
- [x] Table `sessions`
- [x] Modèle ORM `Session`
- [x] Route `POST /auth/register`
- [x] Route `POST /auth/login`
- [x] Route `POST /auth/logout`
- [x] Route `POST /auth/refresh`
- [ ] Dépendance FastAPI pour vérifier l'`access_token` sur les routes protégées (middleware pour le bearer)

### Frontend
- [x] Formulaire register + server action
- [x] Formulaire login + server action + cookies `httpOnly`
- [x] Server action logout
- [x] Proxy `proxy.ts` avec refresh automatique
- [ ] Redirection post-login vers la page de jeu

