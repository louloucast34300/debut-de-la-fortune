# SQLAlchemy — Cheatsheet requêtes (async)

## Setup de base

```python
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
```

---

## SELECT

### Un élément par condition
```python
result = await db.execute(select(User).where(User.email == "test@mail.com"))
user = result.scalar_one_or_none()  # None si pas trouvé
user = result.scalar_one()          # lève une exception si pas trouvé
```

### Un élément par clé primaire
```python
user = await db.get(User, user_id)  # None si pas trouvé
```

### Liste d'éléments
```python
result = await db.execute(select(User))
users = result.scalars().all()  # → liste
```

### Avec filtre
```python
result = await db.execute(select(User).where(User.pseudo == "louis"))
users = result.scalars().all()
```

### Avec plusieurs conditions
```python
from sqlalchemy import and_, or_

result = await db.execute(
    select(User).where(
        and_(User.email == "test@mail.com", User.pseudo == "louis")
    )
)
```

### Avec ORDER BY / LIMIT
```python
result = await db.execute(
    select(User).order_by(User.created_at.desc()).limit(10)
)
users = result.scalars().all()
```

### Vérifier l'existence
```python
from sqlalchemy import exists

result = await db.execute(select(exists().where(User.email == "test@mail.com")))
exists_bool = result.scalar()  # True / False
```

---

## INSERT

```python
user = User(id=uuid.uuid4(), email="test@mail.com", pseudo="louis", password="...")
db.add(user)
await db.commit()
await db.refresh(user)  # recharge l'objet depuis la BDD (utile pour récupérer created_at etc.)
```

### Insert multiple
```python
db.add_all([user1, user2, user3])
await db.commit()
```

---

## UPDATE

### Via l'objet ORM (recommandé si déjà chargé)
```python
result = await db.execute(select(User).where(User.id == user_id))
user = result.scalar_one_or_none()
if user:
    user.pseudo = "nouveau_pseudo"
    await db.commit()
```

### Via UPDATE direct (plus performant, sans charger l'objet)
```python
await db.execute(
    update(User)
    .where(User.id == user_id)
    .values(pseudo="nouveau_pseudo")
)
await db.commit()
```

### Update sur la session courante (ex: refresh token)
```python
await db.execute(
    update(Session)
    .where(Session.refresh_token == old_token)
    .values(refresh_token=new_token, expires_at=new_expires_at)
)
await db.commit()
```

---

## DELETE

### Via l'objet ORM
```python
result = await db.execute(select(Session).where(Session.refresh_token == token))
session = result.scalar_one_or_none()
if session:
    await db.delete(session)
    await db.commit()
```

### Via DELETE direct
```python
await db.execute(
    delete(Session).where(Session.refresh_token == token)
)
await db.commit()
```

---

## Jointures

```python
result = await db.execute(
    select(Session, User)
    .join(User, Session.user_id == User.id)
    .where(Session.refresh_token == token)
)
session, user = result.one()
```

---

## Patterns utiles

### Rollback en cas d'erreur
```python
try:
    db.add(user)
    await db.commit()
except Exception:
    await db.rollback()
    raise
```

### Compter des éléments
```python
from sqlalchemy import func

result = await db.execute(select(func.count()).select_from(User))
count = result.scalar()
```
