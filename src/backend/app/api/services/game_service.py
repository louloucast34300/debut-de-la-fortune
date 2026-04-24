import uuid
from api.models.auth_orm import Game, GameParticipants
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

class GameService():

    async def createGame(self,db:AsyncSession,player_ids:list[str]):
        try:
            game = Game(id=uuid.uuid4(), status="waiting")
            db.add(game)
            await db.flush()

            for user_id in player_ids:
                db.add(GameParticipants(
                    id=uuid.uuid4(),
                    user_id=uuid.UUID(user_id),
                    game_id=game.id
                ))
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            print("IntegrityError", e.orig)
            return {"success":False, "message":"Les données de la partie ne sont pas conformes."}
        except Exception as e:
            await db.rollback()
            print("Exception", e)
            return {"success":False, "message":"La partie n'a pas pu être enregistrée."}
        
        return {"success":True, "game_id":str(game.id)}