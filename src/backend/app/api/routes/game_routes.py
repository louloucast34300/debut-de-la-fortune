from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db
from core.dependencies import get_current_user
from api.services.game_service import GameService
from api.schemas.game_types import SurrenderRequest


game_service = GameService()
router = APIRouter()

@router.post("/surrender")
async def surrender(request: SurrenderRequest, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    return await game_service.surrenderGame(db=db, game_id=request.game_id, user_id=current_user["sub"])
