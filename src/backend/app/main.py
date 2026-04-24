from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from api.routes.auth_routes import router as auth_router
from api.routes.ws_routes import router as ws_router
from api.routes.game_routes import router as game_router

import os

api_prefix = "/api/v1"
if api_prefix == "/":
    api_prefix = ""
api_prefix = api_prefix.rstrip("/")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if(api_prefix):
    root_router = APIRouter(prefix=api_prefix)
    root_router.include_router(auth_router, prefix="/auth", tags=["auth"])
    root_router.include_router(ws_router,prefix="/ws",tags=["ws"])
    root_router.include_router(game_router, prefix="/game", tags=["game"])
    app.include_router(root_router)
else:
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(ws_router, prefix="/ws", tags=["ws"])
    app.include_router(game_router, prefix="/game", tags=["game"])



@app.get("/healthy")
def healthy():
    return {"status": "ok"}