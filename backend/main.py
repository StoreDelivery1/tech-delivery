from fastapi import FastAPI

from app.routers.users import router as users_router


app = FastAPI(
    title="Tech Delivery API",
    version="1.0.0",
)


app.include_router(users_router)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Tech Delivery API is running",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
    }