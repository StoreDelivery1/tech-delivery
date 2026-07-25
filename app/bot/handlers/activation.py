from datetime import datetime, timezone

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.activation import ActivationState
from app.database.session import SessionLocal
from app.services.activation_service import ActivationService

router = Router()


@router.message(
    ActivationState.waiting_for_code,
)
async def activation_handler(
    message: Message,
    state: FSMContext,
):
    db = SessionLocal()

    try:
        code = message.text.strip().upper()

        user = ActivationService.get_by_code(
            db,
            code,
        )

        if user is None:
            await message.answer(
                "❌ Код не знайдено."
            )
            return

        if (
            user.activation_code_expires_at
            and user.activation_code_expires_at
            < datetime.now(timezone.utc)
        ):
            await message.answer(
                "⌛ Код прострочений."
            )
            return

        ActivationService.activate(
            db=db,
            user=user,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )

        await state.clear()

        await message.answer(
            f"✅ Акаунт активовано!\n\n"
            f"Вітаємо, <b>{user.full_name}</b> 🎉"
        )

    finally:
        db.close()