import uuid
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.auth_orm import User, Session
from utils.bcrypt import generate_new_salt, verify_password
from utils.jwt import encode_token
from api.schemas.auth_types import RegisterRequest, LoginRequest, RefreshRequest

class AuthService():
    async def registerUser(self, db: AsyncSession, data: RegisterRequest):
        h_password = generate_new_salt(data.password)
        db.add(User(
            id=uuid.uuid4(),
            email=data.email,
            password=h_password,
            pseudo=data.pseudo
        ))
        await db.commit()

    async def loginUser(self, db: AsyncSession, data: LoginRequest):
        result = await db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()
        if not user:
            return {"success": False, "message": "Email non trouvé"}
        if not verify_password(data.password, user.password):
            return {"success": False, "message": "Mot de passe incorrect"}

        payload_access = {
            "sub": str(user.id),
            "pseudo": user.pseudo,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
            "iat": datetime.now(timezone.utc)
        }
        access_token = encode_token(payload_access)
        expire_at = datetime.now(timezone.utc) + timedelta(days=30)
        payload_refresh = {
            "sub": str(user.id),
            "exp": expire_at,
        }
        refresh_token = encode_token(payload_refresh)

        db.add(Session(
            id=uuid.uuid4(),
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=expire_at
        ))
        await db.commit()
        return {
            "success": True,
            "message": "utilisateur authentifié",
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    
    async def logoutUser(self, db:AsyncSession, token:LoginRequest):
        result = await db.execute(select(Session).where(Session.refresh_token == token.refresh_token))
        session = result.scalar_one_or_none()
        if not session:
            return {"success": False, "message": "Session non trouvée"}

        await db.delete(session)
        await db.commit()
        return {"success": True, "message": "Session supprimée"}
    
    async def refreshTokens(self, db:AsyncSession, token:RefreshRequest):
        result = await db.execute(select(Session).where(Session.refresh_token == token.refresh_token))
        session = result.scalar_one_or_none()
        if not session:
            return {"success": False, "message": "Session non trouvée"}
        if session.expires_at < datetime.now(timezone.utc):
            return {"success": False, "message": "Session expirée"}

        result_user = await db.execute(select(User).where(User.id == session.user_id))
        user = result_user.scalar_one_or_none()
        if not user:
            return {"success": False, "message": "Utilisateur non trouvé"}

        payload_access = {
            "sub":str(user.id),
            "pseudo":user.pseudo,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
            "iat": datetime.now(timezone.utc)
        }
        access_token = encode_token(payload_access)
        expire_at = datetime.now(timezone.utc) + timedelta(days=30)
        payload_refresh = {
            "sub":str(user.id),
            "exp": expire_at,
        }
        refresh_token = encode_token(payload_refresh)

        session.refresh_token = refresh_token
        session.expires_at = expire_at
        await db.commit()

        return {
            "success": True,
            "message": "tokens rafraichis",
            "access_token": access_token,
            "refresh_token": refresh_token
        }



       



