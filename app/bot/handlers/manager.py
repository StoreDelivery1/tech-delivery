from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.manager import ManagerOrderState
from app.database.session import SessionLocal
from app.models.order import OrderPriority
from app.schemas.order import ManagerOrderCreate
from app.services.activation_service import ActivationService
from app.services.manager_service import ManagerService

router = Router()


@router.message(F.text == "📦 Створити заявку")
async def start_manager_order(message: Message, state: FSMContext):
    await state.set_state(ManagerOrderState.waiting_for_destination_store)
    await message.answer("🏪 Введіть ID магазину призначення:")


@router.message(ManagerOrderState.waiting_for_destination_store)
async def process_destination_store(message: Message, state: FSMContext):
    try:
        await state.update_data(destination_store_id=int(message.text))
        await state.set_state(ManagerOrderState.waiting_for_description)
        await message.answer("📝 Введіть опис замовлення:")
    except (TypeError, ValueError):
        await message.answer("❌ Введіть коректний ID магазину")


@router.message(ManagerOrderState.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(ManagerOrderState.waiting_for_weight)
    await message.answer("⚖️ Введіть вагу (або залиште порожнім):")


@router.message(ManagerOrderState.waiting_for_weight)
async def process_weight(message: Message, state: FSMContext):
    weight_text = message.text.strip()
    weight = None if not weight_text else float(weight_text)
    await state.update_data(weight=weight)
    await state.set_state(ManagerOrderState.waiting_for_priority)
    await message.answer("🎯 Введіть пріоритет (LOW, NORMAL, HIGH, URGENT):")


@router.message(ManagerOrderState.waiting_for_priority)
async def process_priority(message: Message, state: FSMContext):
    db = SessionLocal()
    try:
        priority = OrderPriority(message.text.strip().upper())
        data = await state.get_data()

        manager = ActivationService.get_by_telegram(
            db,
            message.from_user.id,
        )

        if manager is None:
            await message.answer("❌ Користувача не знайдено")
            return

        ManagerService.create_order(
            db=db,
            user_id=manager.id,
            data=ManagerOrderCreate(
                to_store_id=data["destination_store_id"],
                description=data["description"],
                estimated_weight=data.get("weight"),
                priority=priority,
            ),
        )

        await message.answer("✅ Замовлення успішно створено.")
        await state.clear()

    except (ValueError, TypeError) as e:
        await message.answer(f"❌ {str(e)}")
    finally:
        db.close()
