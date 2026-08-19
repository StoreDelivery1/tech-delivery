from aiogram import Dispatcher

from app.bot.handlers.activation import router as activation_router
from app.bot.handlers.admin import router as admin_router
from app.bot.handlers.admin_delivery_conflicts import router as admin_delivery_conflicts_router
from app.bot.handlers.courier import router as courier_router
from app.bot.handlers.manager import router as manager_router
from app.bot.handlers.manager_delivery_confirmation import router as manager_delivery_confirmation_router
from app.bot.handlers.product_order import router as product_order_router
from app.bot.handlers.start import router as start_router

dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(activation_router)

# Manager delivery confirmation (before other manager handlers)
dp.include_router(manager_delivery_confirmation_router)

# Manager (before admin to ensure manager callbacks are handled first)
dp.include_router(manager_router)
dp.include_router(product_order_router)

# Courier
dp.include_router(courier_router)

# Admin delivery conflicts (before general admin handlers)
dp.include_router(admin_delivery_conflicts_router)

# Admin (after all user-specific routers)
dp.include_router(admin_router)