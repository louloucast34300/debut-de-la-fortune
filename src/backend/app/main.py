from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/healthy")
def healthy():
    return {"status": "ok"}