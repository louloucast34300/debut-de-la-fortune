# Plan — Système d'authentification

## Dépendances à ajouter dans requirements.txt

```
PyJWT>=2.8.0
passlib[bcrypt]>=1.7.4
```

---

## Tokens

### access_token (JWT)
- Durée courte : **15 min**
- Envoyé par le client à chaque requête protégée dans le header : `Authorization: Bearer <token>`
- **Pas stocké en BDD** — c'est l'intérêt du JWT
- Le token contient les données directement encodées en base64 (user_id, expiration...) et est **signé** avec une `SECRET_KEY` connue uniquement du serveur
- Vérification côté serveur :
  ```python
  payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
  # signature invalide ou token expiré → exception automatique
  # sinon → payload["user_id"] est garanti authentique
  ```
- La cryptographie garantit que si la signature est valide, c'est forcément le serveur qui a émis ce token — aucun lookup BDD nécessaire
- ⚠️ Inconvénient : si le token est volé, il reste valide jusqu'à expiration (d'où la durée courte de 15 min)

### refresh_token
- Durée longue : **30 jours**
- Stocké en BDD dans la table `sessions`
- Sert **uniquement** à obtenir un nouvel `access_token` quand celui-ci expire
- Révocable instantanément : un simple `DELETE` en BDD l'invalide (logout, suspicion de vol...)

### Comparaison

| | `access_token` (JWT) | `refresh_token` |
|---|---|---|
| Vérification | Signature crypto, pas de BDD | Lookup en BDD |
| Durée | 15 min | 30 jours |
| Révocable instantanément | ❌ Non | ✅ Oui (DELETE en BDD) |

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
