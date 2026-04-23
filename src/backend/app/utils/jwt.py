import os
import jwt



# JWT methods
SECRET_KEY = os.getenv("SECRET_KEY")

def encode_token( payload ):
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

