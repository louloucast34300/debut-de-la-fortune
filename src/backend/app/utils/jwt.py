import os
import jwt
from datetime import datetime, timedelta, timezone


# JWT methods
SECRET_KEY = os.getenv("SECRET_KEY")

def encode_token( payload ):
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def decode_token( payload ):
     return jwt.decode(payload, SECRET_KEY, algorithms=["HS256"])


def create_access_token(user_id, pseudo):
    payload_access = {
        "sub":str(user_id),
        "pseudo":pseudo,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        "iat": datetime.now(timezone.utc)
    }
    token = encode_token(payload_access)
    return token

def create_refresh_token(user_id):
      payload_refresh = {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(days=30),
        }
      token = encode_token(payload_refresh)
      return token

