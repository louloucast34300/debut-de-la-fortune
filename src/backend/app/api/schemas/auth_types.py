from pydantic import BaseModel

class RegisterRequest(BaseModel):
    pseudo: str
    email: str
    password: str