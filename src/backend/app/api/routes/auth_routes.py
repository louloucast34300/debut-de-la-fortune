from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db
from api.schemas.auth_types import RegisterRequest, LoginRequest
from api.services.auth_service import AuthService

auth_service = AuthService()
router = APIRouter()


@router.post("/register", status_code=201)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.registerUser(db=db, data=request)


@router.post("/login", status_code=201)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.loginUser(db=db, data=request)
    

