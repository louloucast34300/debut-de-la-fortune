from pydantic import BaseModel

class RegisterRequest(BaseModel):
    pseudo: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email:str
    password:str

class LogoutRequest(BaseModel):
    refresh_token: str

class RefreshRequest(BaseModel):
    refresh_token: str