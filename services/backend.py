from fastapi import FastAPI

app = FastAPI(title="Backend A")


@app.get("/hello")
async def hello():
    return {"backend": "backend-a", "message": "Hello from backend-a"}