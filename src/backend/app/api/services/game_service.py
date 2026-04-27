import uuid
from api.models.auth_orm import Game, GameParticipants, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

class GameService():

    async def createGame(self,db:AsyncSession,player_ids:list[str]):
        try:
            game = Game(id=uuid.uuid4(), status="waiting")
            db.add(game)
            await db.flush()
            players = []
            for user_id in player_ids:
                result = await db.execute(select(User).where(User.id == user_id))
                user: User | None = result.scalar_one_or_none()

                if not user:
                    await db.rollback()
                    return {"success": False, "message": "Utilisateur introuvable"}
                
                players.append({"id": str(user.id), "pseudo": user.pseudo})
                
                db.add(GameParticipants(
                    id=uuid.uuid4(),
                    user_id=uuid.UUID(user_id),
                    pseudo=user.pseudo,
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
        
        return {"success":True, "game_id":str(game.id),"players":players}

    async def surrenderGame(self, db: AsyncSession, game_id: str, user_id: str):
        result = await db.execute(
            select(GameParticipants).where(
                GameParticipants.game_id == uuid.UUID(game_id),
                GameParticipants.user_id == uuid.UUID(user_id)
            )
        )
        participant = result.scalar_one_or_none()
        if not participant:
            return {"success": False, "message": "Participant introuvable"}

        participant.status = "surrendered"
        try:
            await db.commit()
        except Exception as e:
            await db.rollback()
            print("Exception", e)
            return {"success": False, "message": "Erreur lors de l'abandon"}

        return {"success": True}