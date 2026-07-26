from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards.main_menu import (
    admin_main_menu,
    courier_main_menu,
    manager_main_menu,
)
from app.bot.states.activation import ActivationState
from app.database.session import SessionLocal
from app.models.user import UserRole
from app.services.activation_service import ActivationService

router = Router()


@router.message(CommandStart())
async def start_handler(
    message: Message,
    state: FSMContext,
):
    print(f"ROUTER: start | {message.text}")
    print(f"Telegram ID: {message.from_user.id}")
    print(f"Username: {message.from_user.username}")

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

            await state.clear()

            if user.role == UserRole.ADMIN:

                await message.answer(
                    f"👋 Вітаємо, <b>{user.full_name}</b>!\n\n"
                    "Ви увійшли як <b>Адміністратор</b>.",
                    reply_markup=admin_main_menu(),
                )

                return

            if user.role == UserRole.MANAGER:

                await message.answer(
                    f"👋 Вітаємо, <b>{user.full_name}</b>!\n\n"
                    "Ви увійшли як <b>Менеджер</b>.",
                    reply_markup=manager_main_menu(),
                )

                return

            if user.role == UserRole.COURIER:

                await message.answer(
                    f"👋 Вітаємо, <b>{user.full_name}</b>!\n\n"
                    "Ви увійшли як <b>Кур'єр</b>.",
                    reply_markup=courier_main_menu(),
                )

                return

            await message.answer(
                f"👋 Вітаємо, <b>{user.full_name}</b>!"
            )

            return

        await state.set_state(
            ActivationState.waiting_for_code,
        )

        await message.answer(
            "👋 <b>Ласкаво просимо до Tech Delivery!</b>\n\n"
            "Для початку роботи введіть код активації, який вам видав адміністратор."
        )

    finally:
        db.close()
