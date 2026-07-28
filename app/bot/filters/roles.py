"""Role-based filters for router handlers.

These filters prevent routing conflicts by ensuring handlers only
execute for users with the appropriate role.
"""

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from app.database.session import SessionLocal
from app.services.activation_service import ActivationService


class AdminFilter(BaseFilter):
    """Filter that allows only admin users to pass."""

    async def __call__(self, update: Message | CallbackQuery) -> bool:
        db = SessionLocal()
        try:
            admin = ActivationService.get_admin(db, update.from_user.id)
            return admin is not None
        finally:
            db.close()


class ManagerFilter(BaseFilter):
    """Filter that allows only manager users to pass."""

    async def __call__(self, update: Message | CallbackQuery) -> bool:
        db = SessionLocal()
        try:
            manager = ActivationService.get_manager(db, update.from_user.id)
            return manager is not None
        finally:
            db.close()


class CourierFilter(BaseFilter):
    """Filter that allows only courier users to pass."""

    async def __call__(self, update: Message | CallbackQuery) -> bool:
        db = SessionLocal()
        try:
            courier = ActivationService.get_courier(db, update.from_user.id)
            return courier is not None
        finally:
            db.close()
