# CLAUDE.md — Conventions du projet

## Stack

- **Frontend** : Next.js (TypeScript)
- **Backend** : FastAPI (Python 3.12)
- **BDD** : PostgreSQL (via SQLAlchemy async + asyncpg)
- **Orchestration** : Docker Compose

---

## Architecture Backend (`src/backend/app/`)

```
app/
  api/
    routes/       ← routes FastAPI (HTTP uniquement, délègue aux services)
    models/
      orm/        ← modèles SQLAlchemy (mapping BDD)
      types/      ← modèles Pydantic (validation requêtes/réponses)
  core/           ← config, connexion BDD, dépendances FastAPI (get_db...)
  domain/         ← logique métier pure (classes Game, Player, PenduGame...)
                     aucun import SQLAlchemy ou FastAPI ici
  services/       ← orchestration : charge l'état BDD, appelle le domaine, sauvegarde
  utils/          ← fonctions utilitaires pures sans état
  main.py         ← point d'entrée FastAPI
```

### Règles
- Les routes ne contiennent pas de logique métier — elles délèguent aux services
- Le domaine ne sait pas que FastAPI ou SQLAlchemy existent
- Les imports sont absolus (pas de `from .module import ...`), la racine est `app/`

### Conventions pour un service (`services/`)

Un service est une classe qui orchestre les interactions BDD et retourne toujours un dict `{"success": bool, "message": str, ...}`.

**Pattern early return** : traiter les cas d'erreur en haut, le chemin nominal coule sans imbrication.

```python
async def monService(self, db: AsyncSession, data: MonSchema):
    result = await db.execute(select(User).where(...))
    user = result.scalar_one_or_none()
    if not user:
        return {"success": False, "message": "Non trouvé"}

    # chemin nominal sans else
    ...
    return {"success": True, ...}
```

**Gestion des écritures BDD** : toujours wrapper dans `try/except` avec `rollback()`.

```python
try:
    db.add(...)
    await db.commit()
except IntegrityError as e:
    await db.rollback()
    return {"success": False, "message": "Contrainte BDD violée"}
except Exception as e:
    await db.rollback()
    return {"success": False, "message": "Erreur BDD"}
```

**Ordre d'insertion avec FK** : utiliser `flush()` pour insérer le parent avant l'enfant dans la même transaction.

```python
try:
    db.add(Parent(...))
    await db.flush()   # rend le parent visible pour la FK
    db.add(Enfant(parent_id=parent_id, ...))
    await db.commit()
except ...
```

---

## Architecture Frontend (`src/frontend/app/`)

```
app/
  features/       ← une feature = un dossier (auth, game, profile...)
    auth/
        login.tsx         ← composant principal 1
        register.tsx      ← composant principal 2
        auth.server.ts    ← server actions Next.js
        auth.schema.ts    ← validation (zod)
        auth.type.ts      ← types TypeScript
  (pages)/        ← pages Next.js (App Router)
  styles/         ← styles
  layout.tsx
  page.tsx
```

### Règles
- Chaque feature contient tous ses fichiers au même endroit (colocation)
- Si un composant n'a pas de logique métier et devient réutilisable entre features, il migre vers un dossier `components/` global
- Les appels API vers le backend se font dans les fichiers `.server.ts` (server actions)
