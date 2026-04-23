import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.auth_orm import User, Session
from utils.bcrypt import generate_new_salt, verify_password
from utils.jwt import create_access_token, create_refresh_token
from api.schemas.auth_types import RegisterRequest, LoginRequest, RefreshRequest, LogoutRequest

class AuthService():
    
    async def registerUser(self, db: AsyncSession, data: RegisterRequest):
        h_password = generate_new_salt(data.password)
        user_id = uuid.uuid4()

        access_token = create_access_token(user_id, data.pseudo)
        refresh_token = create_refresh_token(user_id)

        try:
            db.add(User(
                id=user_id,
                email=data.email,
                password=h_password,
                pseudo=data.pseudo
            ))
            await db.flush() 

            db.add(Session(
                id=uuid.uuid4(),
                user_id=user_id,
                refresh_token=refresh_token,
                expires_at=datetime.now(timezone.utc) + timedelta(days=30)
            ))
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            print("IntegrityError:", e.orig)
            return {"success": False, "message": f"Cet email est déjà utilisé"}
        except Exception as e:
            await db.rollback()
            print("Exception:", e)
            return {"success": False, "message": "Erreur lors de l'enregistrement"}

        return {
            "success": True,
            "message": "utilisateur enregistré et connecté",
            "access_token": access_token,
            "refresh_token": refresh_token
        }


    async def loginUser(self, db: AsyncSession, data: LoginRequest):
        result = await db.execute(select(User).where(User.email == data.email))
        user: User = result.scalar_one_or_none()

        if not user:
            return {"success": False, "message": "Email non trouvé"}
        
        if not verify_password(data.password, user.password):
            return {"success": False, "message": "Mot de passe incorrect"}
        
        access_token = create_access_token(user.id, user.pseudo)
        refresh_token = create_refresh_token(user.id)

        db.add(Session(
            id=uuid.uuid4(),
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        ))
        try:
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            print("IntegrityError:", e.orig)
            return {"success": False, "message": f"la session n'a pas pu être créée."}
        except Exception as e:
            await db.rollback()
            print("Exception:", e)
            return {"success": False, "message": "Erreur lors de la connexion."}
        return {
            "success": True,
            "message": "utilisateur authentifié",
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    
    
    async def logoutUser(self, db:AsyncSession, token:LogoutRequest):
        result = await db.execute(select(Session).where(Session.refresh_token == token.refresh_token))
        session:Session = result.scalar_one_or_none()
        if not session:
            return {"success": False, "message": "Session non trouvée."}

        await db.delete(session)
        try:
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            print("IntegrityError:", e.orig)
            return {"success": False, "message": "la session n'a pas pu être supprimée."}
        except Exception as e:
            await db.rollback()
            print("Exception:", e)
            return {"success": False, "message": "Erreur lors de la déconnexion."}
        return {"success": True, "message": "Session supprimée."}
    
    
    async def refreshTokens(self, db:AsyncSession, token:RefreshRequest):
        result = await db.execute(select(Session).where(Session.refresh_token == token.refresh_token))
        session:Session = result.scalar_one_or_none()

        if not session:
            return {"success": False, "message": "Session non trouvée"}
        
        if session.expires_at < datetime.now(timezone.utc):
            return {"success": False, "message": "Session expirée"}

        result_user = await db.execute(select(User).where(User.id == session.user_id))
        user:User = result_user.scalar_one_or_none()

        if not user:
            return {"success": False, "message": "Utilisateur non trouvé"}
        
        access_token = create_access_token(user.id, user.pseudo)
        refresh_token = create_refresh_token(user.id)

        session.refresh_token = refresh_token
        session.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        try:
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            print("IntegrityError:", e.orig)
            return {"success": False, "message": f"la session n'a pas pu être renouvelée."}
        except Exception as e:
            await db.rollback()
            print("Exception:", e)
            return {"success": False, "message": "Erreur lors du refresh des tokens."}

        return {
            "success": True,
            "message": "tokens rafraichis",
            "access_token": access_token,
            "refresh_token": refresh_token
        }




       



