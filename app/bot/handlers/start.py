from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.activation import ActivationState
from app.database.session import SessionLocal
from app.services.activation_service import ActivationService

router = Router()


@router.message(CommandStart())
async def start_handler(
    message: Message,
    state: FSMContext,
):
    db = SessionLocal()

    try:
        user = ActivationService.get_by_telegram(
            db,
            message.from_user.id,
        )

        if user is not None:
            ActivationService.update_last_login(
                db,
                user,
            )

            await message.answer(
                f"👋 Вітаємо назад, <b>{user.full_name}</b>!"
            )

            return

        await state.set_state(
            ActivationState.waiting_for_code,
        )

        await message.answer(
            "👋 <b>Вітаємо у Tech Delivery!</b>\n\n"
            "🔑 Введіть код активації."
        )

    finally:
        db.close()