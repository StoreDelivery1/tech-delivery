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
            db=db,
            code=code,
        )

        if user is None:
            await message.answer(
                "❌ Код активації не знайдено.\n\n"
                "Перевірте код та спробуйте ще раз."
            )
            return

        if (
            user.activation_code_expires_at
            and user.activation_code_expires_at
            < datetime.now(timezone.utc)
        ):
            await message.answer(
                "⌛ Термін дії коду закінчився.\n"
                "Зверніться до адміністратора для отримання нового коду."
            )
            return

        try:
            ActivationService.activate(
                db=db,
                user=user,
                telegram_id=message.from_user.id,
                username=message.from_user.username,
            )
        except ValueError as e:
            await message.answer(
                f"❌ {str(e)}"
            )
            return

        await state.clear()

        await message.answer(
            "✅ Акаунт успішно активовано!\n\n"
            f"👤 {user.full_name}\n"
            f"🎭 Роль: {user.role.value}\n\n"
            "Тепер ви можете користуватися ботом."
        )

    finally:
        db.close()