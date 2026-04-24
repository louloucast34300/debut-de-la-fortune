from pydantic import BaseModel


class SurrenderRequest(BaseModel):
    game_id: str