import uuid
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db
from api.models.auth_orm import User
from api.schemas.auth_types import RegisterRequest
router = APIRouter()


@router.post("/register", status_code=201)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    print("toto",request.pseudo)
    db.add(User(
        id=uuid.uuid4(),
        email=request.email,
        password=request.password,
        pseudo=request.pseudo
    ))
    await db.commit()
    return {"success": True}
