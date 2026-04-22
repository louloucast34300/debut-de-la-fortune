import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.auth_orm import User
from utils.bcrypt import generate_new_salt, verify_password
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
                return {"success": True, "message":"utilisateur authentifié"}
            else:
                return {"success": False, "message":"Mot de passe incorrect"}
        else:
            return {"success": False, "message":"Email non trouvé"}
