from fastapi import FastAPI, APIRouter
from api.routes.auth_routes import router as auth_router

api_prefix = "/api/v1"
if api_prefix == "/":
    api_prefix = ""
api_prefix = api_prefix.rstrip("/")

app = FastAPI()

if(api_prefix):
    root_router = APIRouter(prefix=api_prefix)
    root_router.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(root_router)
else:
    app.include_router(auth_router, prefix="/auth", tags=["auth"])


@app.get("/healthy")
def healthy():
    return {"status": "ok"}