from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards.main_menu import (
    admin_couriers_menu,
    admin_main_menu,
)
from app.bot.states.admin import AdminCourierState
from app.database.session import SessionLocal
from app.models.user import UserRole
from app.schemas.user import UserCreate
from app.services.store_service import StoreService
from app.services.user_service import UserService

router = Router()


@router.message(F.text == "🚚 Кур'єри")
async def admin_couriers_menu_handler(message: Message):
    await message.answer(
        "🧑‍🔧 Управління кур'єрами",
        reply_markup=admin_couriers_menu(),
    )


@router.message(F.text == "➕ Додати кур'єра")
async def start_admin_courier_creation(message: Message, state: FSMContext):
    await state.set_state(AdminCourierState.waiting_for_full_name)
    await message.answer("✍️ Введіть ПІБ кур'єра:")


@router.message(F.text == "⬅️ Назад")
async def back_to_admin_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "⬅️ Повернутося до головного меню",
        reply_markup=admin_main_menu(),
    )


@router.message(AdminCourierState.waiting_for_full_name)
async def admin_full_name_handler(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(AdminCourierState.waiting_for_store)
    await message.answer("🏪 Введіть ID магазину для кур'єра:")


@router.message(AdminCourierState.waiting_for_store)
async def admin_store_handler(message: Message, state: FSMContext):
    db = SessionLocal()
    try:
        store_id = int(message.text)
        StoreService.get_store(db, store_id)

        data = await state.get_data()
        full_name = data["full_name"]

        courier = UserService.create(
            db=db,
            user=UserCreate(
                full_name=full_name,
                role=UserRole.COURIER,
                store_id=store_id,
            ),
        )

        await message.answer(
            "✅ Кур'єра створено!\n\n"
            f"👤 ПІБ: {courier.full_name}\n"
            f"🏪 Магазин ID: {courier.store_id}\n"
            f"🔑 Код активації: {courier.activation_code}"
        )
        await state.clear()

    except ValueError as e:
        await message.answer(f"❌ {str(e)}")
    except (TypeError, ValueError):
        await message.answer("❌ Введіть коректний ID магазину")
    finally:
        db.close()
