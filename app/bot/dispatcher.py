from aiogram import Dispatcher

from app.bot.handlers.activation import router as activation_router
from app.bot.handlers.admin import router as admin_router
from app.bot.handlers.courier import router as courier_router
from app.bot.handlers.manager import router as manager_router
from app.bot.handlers.start import router as start_router

dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(activation_router)
dp.include_router(admin_router)

# Courier
dp.include_router(courier_router)

# Manager
dp.include_router(manager_router)