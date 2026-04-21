# Plan — Système d'authentification

## Dépendances à ajouter dans requirements.txt

```
PyJWT>=2.8.0
passlib[bcrypt]>=1.7.4
```

---

## Tokens

- **`access_token`** (JWT) — durée courte (15 min), envoyé en header `Authorization: Bearer <token>`. Vérifié par signature, **pas stocké en BDD**.
- **`refresh_token`** — durée longue (7-30j), stocké en BDD dans la table `sessions`. Sert uniquement à obtenir un nouvel `access_token`.

---

## Table `sessions` à créer

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    refresh_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## Flux

### Register
- Hasher le password avec `passlib[bcrypt]` avant l'INSERT en BDD.

### Login
1. Récupérer le user par email
2. Vérifier le password hashé (`passlib.verify`)
3. Générer `access_token` (JWT, exp 15min) + `refresh_token` (UUID ou JWT, exp 30j)
4. INSERT dans `sessions` (user_id, refresh_token, expires_at)
5. Retourner les deux tokens

### Requête protégée
1. Client envoie `Authorization: Bearer <access_token>`
2. FastAPI vérifie la signature JWT (via `PyJWT`)
3. Si valide → accès autorisé (pas de requête BDD)

### Refresh
1. Client envoie le `refresh_token`
2. FastAPI cherche la session en BDD : `SELECT * FROM sessions WHERE refresh_token = $1 AND expires_at > NOW()`
3. Si trouvée → générer un nouvel `access_token`

### Logout
1. DELETE de la ligne dans `sessions` correspondant au `refresh_token`
2. Le `refresh_token` est invalidé immédiatement

---

## "Est connecté ?"

```sql
SELECT 1 FROM sessions WHERE user_id = $1 AND expires_at > NOW();
```

---

## TODO

- [ ] Ajouter `PyJWT>=2.8.0` et `passlib[bcrypt]>=1.7.4` dans `requirements.txt`
- [ ] Hasher le password au register
- [ ] Créer la table `sessions` dans `create_tables.sh`
- [ ] Créer le modèle ORM `Session`
- [ ] Route `POST /auth/login`
- [ ] Route `POST /auth/refresh`
- [ ] Route `POST /auth/logout`
- [ ] Middleware / dépendance FastAPI pour vérifier l'`access_token` sur les routes protégées
