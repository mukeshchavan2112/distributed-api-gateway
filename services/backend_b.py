from fastapi import FastAPI

app = FastAPI(title="Backend B")


@app.get("/hello")
async def hello():
    return {"backend": "backend-b", "message": "Hello from backend-b"}