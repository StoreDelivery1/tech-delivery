import logging

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
from app.models.user import MANAGER_ROLES, UserRole, UserStatus
from app.services.activation_service import ActivationService
from app.services.manager_service import ManagerService

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def start_handler(
    message: Message,
    state: FSMContext,
):
    response_text = None
    reply_markup = None
    needs_activation = False
    db = None
    try:
        db = SessionLocal()
        user = ActivationService.get_by_telegram(
            db,
            message.from_user.id,
        )

        if user is None:
            needs_activation = True
        elif user.status != UserStatus.ACTIVE:
            response_text = "Ваш обліковий запис неактивний. Зверніться до адміністратора."
        elif user.role == UserRole.ADMIN:
            response_text = (
                f"👋 Вітаємо, <b>{user.full_name}</b>!\n\n"
                "Ви увійшли як <b>Адміністратор</b>."
            )
            reply_markup = admin_main_menu()
        elif user.role in MANAGER_ROLES:
            if user.store_id is None:
                response_text = (
                    "Ваш обліковий запис знайдено, але магазин не призначено. "
                    "Зверніться до адміністратора."
                )
            else:
                counts_db = None
                try:
                    counts_db = SessionLocal()
                    active, completed = ManagerService.get_my_created_orders(counts_db, user.id)
                    active_count = len(active)
                    all_count = active_count + len(completed)
                except Exception as exc:
                    logger.warning(
                        "Could not load manager menu order counts (%s)",
                        type(exc).__name__,
                    )
                    active_count = all_count = 0
                finally:
                    if counts_db is not None:
                        counts_db.close()

                response_text = (
                    f"👋 Вітаємо, <b>{user.full_name}</b>!\n\n"
                    "Ви увійшли як <b>Менеджер</b>."
                )
                reply_markup = manager_main_menu(
                    active_count=active_count,
                    all_count=all_count,
                )
        elif user.role == UserRole.COURIER:
            response_text = (
                f"👋 Вітаємо, <b>{user.full_name}</b>!\n\n"
                "Ви увійшли як <b>Кур'єр</b>."
            )
            reply_markup = courier_main_menu(user)
        else:
            role_name = user.role.value if user.role is not None else "не визначена"
            response_text = (
                f"Ваш обліковий запис знайдено, але роль «{role_name}» "
                "не має доступу до меню бота. Зверніться до адміністратора."
            )

        if user is not None and response_text and reply_markup is not None:
            ActivationService.update_last_login(db, user)
    except Exception as exc:
        logger.error("Failed to authenticate user during /start (%s)", type(exc).__name__)
        response_text = (
            "Не вдалося перевірити обліковий запис через тимчасову помилку. "
            "Спробуйте пізніше або зверніться до адміністратора."
        )
    finally:
        if db is not None:
            db.close()

    if needs_activation:
        await state.set_state(ActivationState.waiting_for_code)
        await message.answer(
            "👋 <b>Ласкаво просимо до Tech Delivery!</b>\n\n"
            "Для початку роботи введіть код активації, який вам видав адміністратор."
        )
        return

    await state.clear()
    await message.answer(response_text, reply_markup=reply_markup)
