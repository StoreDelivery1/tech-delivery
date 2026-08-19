import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot.bot import bot
from app.bot.filters.roles import ManagerFilter
from app.bot.keyboards.main_menu import manager_main_menu
from app.bot.states.product_order import ProductOrderState
from app.bot.utils.store_formatter import format_store_name
from app.database.session import SessionLocal
from app.models.order import OrderSize
from app.services.activation_service import ActivationService
from app.services.distribution_service import DistributionService
from app.services.manager_service import ManagerService
from app.services.notification_service import NotificationService
from app.services.order_service import OrderService
from app.services.order_status_service import OrderStatusService
from app.services.store_service import StoreService

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(ManagerFilter())
router.callback_query.filter(ManagerFilter())


def build_product_store_keyboard(stores: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=format_store_name(store),
                callback_data=f"product_source_store:{store.id}",
            )]
            for store in stores
        ]
    )


def build_product_size_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Мале", callback_data="product_size:SMALL")],
        [InlineKeyboardButton(text="🟡 Середнє", callback_data="product_size:MEDIUM")],
        [InlineKeyboardButton(text="🔴 Велике", callback_data="product_size:LARGE")],
    ])


def build_product_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Підтвердити", callback_data="product_order:confirm"),
        InlineKeyboardButton(text="❌ Скасувати", callback_data="product_order:cancel"),
    ]])


def format_product_size(size: OrderSize) -> str:
    return {
        OrderSize.SMALL: "Мале",
        OrderSize.MEDIUM: "Середнє",
        OrderSize.LARGE: "Велике",
    }[size]


def format_product_confirmation(data: dict) -> str:
    return (
        "🛒 <b>Замовлення товару</b>\n\n"
        f"📍 <b>Звідки:</b> {format_store_name(data['source_store'])}\n"
        f"📍 <b>Куди:</b> {format_store_name(data['destination_store'])}\n"
        f"📦 <b>Що перевезти:</b> {data['description']}\n"
        f"📏 <b>Розмір:</b> {format_product_size(data['size'])}"
    )


@router.message(F.text == "🛒 Замовити товар", ManagerFilter())
async def start_product_order(message: Message, state: FSMContext):
    db = SessionLocal()
    try:
        manager = ActivationService.get_manager(db, message.from_user.id)
        if manager is None or manager.store_id is None:
            await state.clear()
            await message.answer("❌ Ви не прив'язані до жодного магазину.")
            return

        stores = [store for store in StoreService.get_stores(db) if store.is_active and store.id != manager.store_id]
        if not stores:
            await message.answer("❌ Немає доступних магазинів-відправників.")
            return

        await state.set_state(ProductOrderState.waiting_for_source_store)
        await state.update_data(destination_store_id=manager.store_id)
        await message.answer(
            "🏪 Оберіть магазин, звідки забрати товар:",
            reply_markup=build_product_store_keyboard(stores),
        )
    finally:
        db.close()


@router.callback_query(ProductOrderState.waiting_for_source_store, F.data.startswith("product_source_store:"))
async def select_product_source_store(callback: CallbackQuery, state: FSMContext):
    store_id = int(callback.data.split(":", 1)[1])
    db = SessionLocal()
    try:
        store = StoreService.get_store(db, store_id)
        if not store.is_active:
            await callback.answer("❌ Магазин недоступний", show_alert=True)
            return
        await state.update_data(source_store_id=store.id, source_store=store)
        await state.set_state(ProductOrderState.waiting_for_description)
        await callback.message.edit_text(f"✅ Обрано магазин\n\n{format_store_name(store)}")
        await callback.message.answer("📦 Опишіть одним повідомленням, що потрібно перевезти")
        await callback.answer()
    finally:
        db.close()


@router.message(ProductOrderState.waiting_for_description)
async def process_product_description(message: Message, state: FSMContext):
    description = (message.text or "").strip()
    if not description:
        await message.answer("❌ Введіть опис товару одним повідомленням.")
        return
    await state.update_data(description=description)
    await state.set_state(ProductOrderState.waiting_for_size)
    await message.answer("📏 Оберіть розмір доставки:", reply_markup=build_product_size_keyboard())


@router.callback_query(ProductOrderState.waiting_for_size, F.data.startswith("product_size:"))
async def select_product_size(callback: CallbackQuery, state: FSMContext):
    try:
        size = OrderSize[callback.data.split(":", 1)[1]]
    except KeyError:
        await callback.answer("❌ Некоректний розмір", show_alert=True)
        return

    data = await state.get_data()
    db = SessionLocal()
    try:
        data["size"] = size
        data["source_store"] = StoreService.get_store(db, data["source_store_id"])
        data["destination_store"] = StoreService.get_store(db, data["destination_store_id"])
        await state.update_data(size=size)
        await state.set_state(ProductOrderState.waiting_for_confirmation)
        await callback.message.edit_text(
            format_product_confirmation(data),
            parse_mode="HTML",
            reply_markup=build_product_confirmation_keyboard(),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(ProductOrderState.waiting_for_confirmation, F.data == "product_order:cancel")
async def cancel_product_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Замовлення товару скасовано.")
    await callback.answer()


@router.callback_query(ProductOrderState.waiting_for_confirmation, F.data == "product_order:confirm")
async def confirm_product_order(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        data = await state.get_data()
        manager = ActivationService.get_manager(db, callback.from_user.id)
        if manager is None or manager.store_id != data.get("destination_store_id"):
            await callback.answer("❌ Магазин отримувач змінився. Почніть знову.", show_alert=True)
            await state.clear()
            return

        order = OrderService.create_order_with_stores(
            db=db,
            current_user=manager,
            from_store_id=data["source_store_id"],
            to_store_id=manager.store_id,
            description=data["description"],
            size=data["size"],
        )
        order = OrderStatusService._ensure_order_loaded(db, order)
        message_id = await NotificationService.notify_order_created(bot, order)
        if message_id:
            order.manager_chat_id = manager.telegram_id
            order.manager_message_id = message_id
            db.add(order)
            db.commit()

        distributed = await DistributionService.distribute_order(
            bot=bot,
            db=db,
            order=order,
            manager_telegram_id=manager.telegram_id or 0,
        )
        await callback.message.edit_text(
            "✅ Замовлення товару створено.\n"
            + ("Заявку розіслано кур'єрам." if distributed else "Вільних кур'єрів зараз немає.")
        )
        active, completed = ManagerService.get_my_created_orders(db, manager.id)
        incoming_count = ManagerService.get_incoming_delivery_count(db, manager.id)
        await callback.message.answer(
            "📋 Головне меню",
            reply_markup=manager_main_menu(
                active_count=len(active),
                all_count=len(active) + len(completed),
                incoming_count=incoming_count,
            ),
        )
        await state.clear()
        await callback.answer()
    except Exception as exc:
        logger.exception("Failed to create product order")
        await callback.message.answer(f"❌ {exc}")
        await state.clear()
        await callback.answer()
    finally:
        db.close()