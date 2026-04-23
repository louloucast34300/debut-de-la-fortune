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

## Proxy Next.js — Protection des routes

### Flux logique

```
requête vers /page-protégée
        ↓
proxy Next.js (proxy.ts)
        ↓
access_token présent ?
   ├── non → redirect /login
   └── oui → expiré ?
              ├── non → laisse passer
              └── oui → refresh_token présent ?
                         ├── non → redirect /login
                         └── oui → appelle POST /auth/refresh
                                    ├── succès → set nouveau cookie access_token → laisse passer
                                    └── échec (refresh expiré) → redirect /login
```

### Décoder le JWT sans SECRET_KEY

Un JWT est composé de `header.payload.signature` encodés en base64. Le payload est **public** — n'importe qui peut le décoder sans la clé. La `SECRET_KEY` sert uniquement à **générer et vérifier la signature** côté backend.

Le proxy se contente de lire l'expiration pour décider quoi faire — la vraie vérification cryptographique se fait quand la requête atteint une route FastAPI protégée.

```ts
// proxy.ts
import { jwtDecode } from 'jwt-decode'
import { NextRequest, NextResponse } from 'next/server'

export async function proxy(request: NextRequest) {
    const accessToken = request.cookies.get('access_token')?.value
    const refreshToken = request.cookies.get('refresh_token')?.value

    // Pas de token → redirect login
    if (!accessToken) {
        return NextResponse.redirect(new URL('/login', request.url))
    }

    // Vérifier l'expiration sans appel réseau
    const { exp } = jwtDecode<{ exp: number }>(accessToken)
    const isExpired = Date.now() >= exp * 1000

    if (!isExpired) {
        return NextResponse.next()
    }

    // access_token expiré → tenter le refresh
    if (!refreshToken) {
        return NextResponse.redirect(new URL('/login', request.url))
    }

    const res = await fetch(`${process.env.BACKEND_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken })
    })

    if (!res.ok) {
        return NextResponse.redirect(new URL('/login', request.url))
    }

    const { access_token } = await res.json()
    const response = NextResponse.next()
    response.cookies.set('access_token', access_token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        maxAge: 60 * 60
    })
    return response
}

export const config = {
    matcher: ['/session/:path*'] // routes à protéger
}
```

---

## "Est connecté ?"

```sql
SELECT 1 FROM sessions WHERE user_id = $1 AND expires_at > NOW();
```

---

## TODO

### Backend
- [x] Ajouter `PyJWT>=2.8.0` et `passlib[bcrypt]>=1.7.4` dans `requirements.txt`
- [x] Hasher le password au register
- [x] Créer la table `sessions` dans `create_tables.sh`
- [x] Créer le modèle ORM `Session`
- [x] Route `POST /auth/login`
- [x] Génération des tokens `access_token` + `refresh_token`
- [ ] Route `POST /auth/refresh`
- [ ] Route `POST /auth/logout`
- [ ] Middleware / dépendance FastAPI pour vérifier l'`access_token` sur les routes protégées

### Frontend
- [x] Formulaire de register
- [x] Server action register
- [x] Formulaire de login
- [x] Server action login + stockage des tokens en cookies `httpOnly`
- [ ] Server action logout (supprime les cookies + appelle `/auth/logout`)
- [ ] Server action refresh (appelle `/auth/refresh` avec le `refresh_token`)
- [ ] Redirection après login/register vers la page protégée
- [ ] Middleware Next.js pour protéger les routes (vérifier la présence de l'`access_token`)
