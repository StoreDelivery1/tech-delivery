from fastapi import FastAPI

from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.couriers import router as couriers_router
from app.routers.managers import router as managers_router
from app.routers.orders import router as orders_router
from app.routers.stores import router as stores_router
from app.routers.users import router as users_router

app = FastAPI(
    title="Tech Delivery API",
    version="1.0.0",
)

app.include_router(auth_router)

app.include_router(admin_router)

app.include_router(users_router)
app.include_router(stores_router)
app.include_router(orders_router)

app.include_router(managers_router)
app.include_router(couriers_router)


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