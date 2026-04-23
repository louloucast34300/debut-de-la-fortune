import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.auth_orm import User, Session
from utils.bcrypt import generate_new_salt, verify_password
from utils.jwt import encode_token
from api.schemas.auth_types import RegisterRequest, LoginRequest

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
        #find user by email 
        result = await db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()
        if user:
            # verify password
            check_decrypt_password =  verify_password(data.password, user.password)
            if check_decrypt_password:
                # generate access_token
                payload_access = {
                    "sub":str(user.id),
                    "pseudo":user.pseudo,
                    "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
                    "iat": datetime.now(timezone.utc)
                }
                access_token = encode_token(payload_access)
                # generate refresh_token
                expire_at = datetime.now(timezone.utc) + timedelta(days=30)
                payload_refresh = {
                    "sub":str(user.id),
                    "exp": expire_at,
                }
                refresh_token = encode_token(payload_refresh)
                # create session
                db.add(Session(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    refresh_token=refresh_token,
                    expires_at=expire_at
                ))
                await db.commit()
                return {
                    "success": True, 
                    "message":"utilisateur authentifié", 
                    "access_token":access_token,
                    "refresh_token":refresh_token
                    }
            else:
                return {"success": False, "message":"Mot de passe incorrect"}
        else:
            return {"success": False, "message":"Email non trouvé"}
    
    async def logoutUser(self, db:AsyncSession, token:LoginRequest):
        #delete user session 
        result = await db.execute(select(Session).where(Session.refresh_token == token.refresh_token))
        session = result.scalar_one_or_none()
        if session:
            await db.delete(session)
            await db.commit()
            return {"success": True, "message": "Session supprimée"}
        else:
            return {"success": False, "message":"Session non trouvée"}


