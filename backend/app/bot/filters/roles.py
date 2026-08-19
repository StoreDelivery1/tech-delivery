"""Role-based filters for router handlers.

These filters prevent routing conflicts by ensuring handlers only
execute for users with the appropriate role.
"""

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from app.database.session import SessionLocal
from app.models.user import UserStatus
from app.services.activation_service import ActivationService


INACTIVE_ACCOUNT_MESSAGE = (
    "Ваш обліковий запис неактивний. Зверніться до адміністратора."
)


async def _notify_inactive(update: Message | CallbackQuery) -> None:
    if isinstance(update, CallbackQuery) or hasattr(update, "message"):
        await update.answer(
            INACTIVE_ACCOUNT_MESSAGE,
            show_alert=True,
        )
        return

    await update.answer(INACTIVE_ACCOUNT_MESSAGE)


async def _is_inactive_user(update: Message | CallbackQuery, db) -> bool:
    if update.from_user is None:
        return True

    user = ActivationService.get_by_telegram(db, update.from_user.id)
    if user is not None and user.status == UserStatus.INACTIVE:
        await _notify_inactive(update)
        return True

    return False


class AdminFilter(BaseFilter):
    """Filter that allows only admin users to pass."""

    async def __call__(self, update: Message | CallbackQuery) -> bool:
        db = SessionLocal()
        try:
            if await _is_inactive_user(update, db):
                return False

            if update.from_user is None:
                return False

            admin = ActivationService.get_admin(db, update.from_user.id)
            return admin is not None
        finally:
            db.close()


class ManagerFilter(BaseFilter):
    """Filter that allows only manager users to pass."""

    async def __call__(self, update: Message | CallbackQuery) -> bool:
        db = SessionLocal()
        try:
            if await _is_inactive_user(update, db):
                return False

            if update.from_user is None:
                return False

            manager = ActivationService.get_manager(db, update.from_user.id)
            return manager is not None
        finally:
            db.close()


class CourierFilter(BaseFilter):
    """Filter that allows only courier users to pass."""

    async def __call__(self, update: Message | CallbackQuery) -> bool:
        db = SessionLocal()
        try:
            if await _is_inactive_user(update, db):
                return False

            if update.from_user is None:
                return False

            courier = ActivationService.get_courier(db, update.from_user.id)
            return courier is not None
        finally:
            db.close()
