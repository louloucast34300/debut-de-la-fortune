from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db
from api.schemas.auth_types import RegisterRequest, LoginRequest, LogoutRequest, RefreshRequest
from api.services.auth_service import AuthService
from core.dependencies import get_current_user


auth_service = AuthService()
router = APIRouter()


@router.post("/register", status_code=201)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.registerUser(db=db, data=request)


@router.post("/login", status_code=201)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.loginUser(db=db, data=request)
    

@router.post("/logout", status_code=201)
async def logout(request: LogoutRequest, db:AsyncSession = Depends(get_db)):
    return await auth_service.logoutUser(db=db, token=request)


@router.post("/refresh", status_code=201)
async def refresh(request: RefreshRequest, db:AsyncSession = Depends(get_db)):
    return await auth_service.refreshTokens(db=db, token=request)


@router.get("/user")
async def get_user(current_user = Depends(get_current_user)):
    return {"success": True, "message": "user ok", "data": {"id": current_user["sub"], "pseudo": current_user["pseudo"]}}