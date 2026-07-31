import logging
import math
from datetime import datetime, timedelta, date

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

from app.bot.bot import bot
from app.bot.filters.roles import ManagerFilter
from app.bot.keyboards.main_menu import manager_main_menu
from app.bot.states.manager import ManagerOrderState, ManagerDeliveryConfirmationState
from app.database.session import SessionLocal
from app.models.order import Order, OrderPriority, OrderSize, OrderStatus
from app.models.store import StoreNetwork
from app.models.user import CourierAvailability
from app.schemas.order import ManagerOrderCreate
from app.services.activation_service import ActivationService
from app.services.distribution_service import DistributionService
from app.services.manager_service import ManagerService
from app.services.notification_service import NotificationService
from app.services.order_status_service import OrderStatusService
from app.services.store_service import StoreService

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(ManagerFilter())
router.callback_query.filter(ManagerFilter())

_MY_ORDERS_PAGE_SIZE = 10

NETWORKS = {
    "apple": {
        "label": "🍏 AppleRoom",
        "network": StoreNetwork.APPLE_ROOM,
    },
    "yabko": {
        "label": "🍏 Ябко",
        "network": StoreNetwork.JABKO,
    },
}


def get_manager_order_error(manager) -> str:
    if getattr(manager, "store_id", None) is None:
        return "❌ Ви не прив'язані до жодного магазину.\n\nБудь ласка, зверніться до адміністратора."

    return ""


def is_priority_control_message(text: str | None) -> bool:
    if not text:
        return False

    return text in {"⬅️ Змінити мережу"}


def build_network_keyboard(db) -> InlineKeyboardMarkup:
    buttons = []

    for network_key, config in NETWORKS.items():
        count = len(StoreService.get_stores_by_network(db, config["network"]))
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{config['label']} ({count})",
                    callback_data=f"manager_network:{network_key}",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_store_keyboard(stores: list) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"🏬 {store.name}",
                callback_data=f"manager_select_store:{store.id}",
            )
        ]
        for store in stores
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_search_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Змінити мережу")]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def build_size_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="🟢 Мале (0,2–5 кг)",
                callback_data="manager_size:SMALL",
            )
        ],
        [
            InlineKeyboardButton(
                text="🟡 Середнє (5,1–15 кг)",
                callback_data="manager_size:MEDIUM",
            )
        ],
        [
            InlineKeyboardButton(
                text="🔴 Габарит (понад 15 кг)",
                callback_data="manager_size:LARGE",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_priority_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="🔴 Високий",
                callback_data="manager_priority:HIGH",
            )
        ],
        [
            InlineKeyboardButton(
                text="🟡 Звичайний",
                callback_data="manager_priority:NORMAL",
            )
        ],
        [
            InlineKeyboardButton(
                text="🟢 Низький",
                callback_data="manager_priority:LOW",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="manager_back_to_size",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text == "📦 Створити заявку", ManagerFilter())
async def start_manager_order(message: Message, state: FSMContext):
    db = SessionLocal()
    try:
        manager = ActivationService.get_manager(db, message.from_user.id)

        error_message = get_manager_order_error(manager)
        if error_message:
            await state.clear()
            await message.answer(error_message)
            return

        await state.set_state(ManagerOrderState.waiting_for_destination_store)
        await state.update_data(selected_network=None, destination_store_candidates=None)
        await message.answer("🏢 Оберіть мережу", reply_markup=build_network_keyboard(db))
    finally:
        db.close()


@router.callback_query(F.data.startswith("manager_network:"))
async def select_network(callback: CallbackQuery, state: FSMContext):
    network_key = callback.data.split(":", 1)[1]
    await state.update_data(selected_network=network_key, destination_store_candidates=None)
    await callback.message.edit_text(
        "🔎 Введіть частину назви магазину\n\n"
        "Приклади:\n"
        "фор\n"
        "гор\n"
        "гал\n"
        "шев\n"
        "vict\n"
        "king"
    )
    await callback.message.answer("🔙 Змінити мережу", reply_markup=build_search_keyboard())
    await callback.answer()


@router.message(ManagerOrderState.waiting_for_destination_store)
async def process_destination_store(message: Message, state: FSMContext):
    if message.text == "🔙 Змінити мережу":
        await state.update_data(selected_network=None, destination_store_candidates=None)
        db = SessionLocal()
        try:
            await message.answer("🏢 Оберіть мережу", reply_markup=build_network_keyboard(db))
        finally:
            db.close()
        return

    db = SessionLocal()
    try:
        data = await state.get_data()
        candidate_ids = data.get("destination_store_candidates") or []

        if candidate_ids and message.text:
            stores = StoreService.get_stores(db)
            selected_store = next(
                (
                    store
                    for store in stores
                    if store.id in candidate_ids and store.name == message.text.strip()
                ),
                None,
            )
            if selected_store is not None:
                await state.update_data(
                    destination_store_id=selected_store.id,
                    destination_store_candidates=None,
                )
                await state.set_state(ManagerOrderState.waiting_for_description)
                await message.answer(f"✅ Обрано магазин\n\n🏬 {selected_store.name}")
                await message.answer("📝 Введіть опис замовлення")
                return

        selected_network = data.get("selected_network")
        if not selected_network:
            await message.answer("🏢 Спочатку оберіть мережу")
            return

        network_value = NETWORKS.get(selected_network, {}).get("network")
        if network_value is None:
            await message.answer("🏢 Спочатку оберіть мережу")
            return

        user_text = message.text.strip()
        matches = StoreService.search_stores(db, user_text, network_value)

        if not matches:
            await message.answer("❌ Магазин не знайдено.\nСпробуйте ще раз.")
            return

        if len(matches) == 1:
            selected_store = matches[0]
            await state.update_data(destination_store_id=selected_store.id, destination_store_candidates=None)
            await state.set_state(ManagerOrderState.waiting_for_description)
            await message.answer(f"✅ Обрано магазин\n\n🏬 {selected_store.name}")
            await message.answer("📝 Введіть опис замовлення")
            return

        await state.update_data(destination_store_candidates=[store.id for store in matches])
        await message.answer(
            f"🔍 Знайдено {len(matches)} магазинів",
            reply_markup=build_store_keyboard(matches),
        )
    except Exception as exc:
        await message.answer(f"❌ {exc}")
    finally:
        db.close()


@router.callback_query(F.data.startswith("manager_select_store:"))
async def select_store(callback: CallbackQuery, state: FSMContext):
    store_id = int(callback.data.split(":", 1)[1])
    db = SessionLocal()
    try:
        store = StoreService.get_store(db, store_id)
        await state.update_data(destination_store_id=store.id, destination_store_candidates=None)
        await state.set_state(ManagerOrderState.waiting_for_description)
        await callback.message.edit_text(f"✅ Обрано магазин\n\n🏬 {store.name}")
        await callback.message.answer("📝 Введіть опис замовлення")
        await callback.answer()
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
    finally:
        db.close()


@router.message(ManagerOrderState.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(ManagerOrderState.waiting_for_size)
    await message.answer("📏 Оберіть розмір замовлення:", reply_markup=build_size_keyboard())


@router.callback_query(F.data.startswith("manager_size:"))
async def select_size(callback: CallbackQuery, state: FSMContext):
    size_key = callback.data.split(":", 1)[1]
    try:
        size_value = OrderSize[size_key]
    except KeyError:
        await callback.answer("❌ Некоректний розмір", show_alert=True)
        return

    await state.update_data(size=size_value)
    await state.set_state(ManagerOrderState.waiting_for_priority)
    await callback.message.edit_text(
        "⭐ Оберіть пріоритет",
        reply_markup=build_priority_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("manager_priority:"))
async def select_priority(callback: CallbackQuery, state: FSMContext):
    priority_key = callback.data.split(":", 1)[1]
    try:
        priority_value = OrderPriority[priority_key]
    except KeyError:
        await callback.answer("❌ Некоректний пріоритет", show_alert=True)
        return

    await state.update_data(priority=priority_value)
    
    # Create the order
    db = SessionLocal()
    try:
        data = await state.get_data()

        manager = ActivationService.get_manager(
            db,
            callback.from_user.id,
        )

        if manager is None:
            await callback.message.answer("❌ Користувача не знайдено")
            await state.clear()
            await callback.answer()
            return

        error_message = get_manager_order_error(manager)
        if error_message:
            await callback.message.answer(error_message)
            await state.clear()
            await callback.answer()
            return

        order = ManagerService.create_order(
            db=db,
            user_id=manager.id,
            data=ManagerOrderCreate(
                to_store_id=data["destination_store_id"],
                description=data["description"],
                size=data.get("size"),
                priority=priority_value,
            ),
        )

        # Ensure order relationships are loaded before notification
        order = OrderStatusService._ensure_order_loaded(db, order)

        # Send initial notification to manager and save message_id
        message_id = await NotificationService.notify_order_created(bot, order)
        if message_id:
            order.manager_chat_id = manager.telegram_id
            order.manager_message_id = message_id
            db.add(order)
            db.commit()
            logger.info(
                "Order created and initial notification sent | order_id=%s order_number=%s manager_id=%s message_id=%s",
                order.id,
                order.number,
                manager.id,
                message_id,
            )

        # Try to distribute order to available couriers
        distributed = await DistributionService.distribute_order(
            bot=bot,
            db=db,
            order=order,
            manager_telegram_id=manager.telegram_id or 0,
        )

        if distributed:
            await callback.message.answer("✅ Замовлення успішно створено.\n\nОрдер розіслано доступним кур'єрам.")
        else:
            await callback.message.answer(
                "🟡 Замовлення створено.\n\n"
                "Зараз немає вільних кур'єрів.\n"
                "Вона буде автоматично запропонована, щойно хтось стане доступним."
            )
        
        # Return to main menu
        active, completed = ManagerService.get_my_created_orders(db, manager.id)
        active_count = len(active)
        all_count = len(active) + len(completed)
        incoming_count = ManagerService.get_incoming_delivery_count(db, manager.id)
        
        await callback.message.answer(
            "📋 Головне меню",
            reply_markup=manager_main_menu(active_count=active_count, all_count=all_count, incoming_count=incoming_count),
        )
        await state.clear()

    except Exception as exc:
        await callback.message.answer(f"❌ {str(exc)}")
        await state.clear()
    finally:
        db.close()

    await callback.answer()


@router.callback_query(F.data == "manager_back_to_size")
async def back_to_size(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ManagerOrderState.waiting_for_size)
    await callback.message.edit_text(
        "📏 Оберіть розмір замовлення:",
        reply_markup=build_size_keyboard(),
    )
    await callback.answer()


@router.message(ManagerOrderState.waiting_for_priority)
async def process_priority_fallback(message: Message, state: FSMContext):
    """Fallback handler for unexpected messages in priority selection state."""
    await message.answer(
        "⭐ Оберіть пріоритет",
        reply_markup=build_priority_keyboard(),
    )


# ── Order details callback ───────────────────────────────────────────────

_SIZE_LABELS = {
    OrderSize.SMALL:  "Мале",
    OrderSize.MEDIUM: "Середнє",
    OrderSize.LARGE:  "Габарит",
}

_PRIORITY_LABELS = {
    OrderPriority.LOW:    "Низький",
    OrderPriority.NORMAL: "Звичайний",
    OrderPriority.HIGH:   "Високий",
    OrderPriority.URGENT: "Терміновий",
}

_STATUS_LABELS = {
    "WAITING_FOR_COURIER": "Очікує кур'єра",
    "ACCEPTED":            "Прийнято",
    "PICKED_UP":           "Забрано",
    "DELIVERING":          "В дорозі",
    "DELIVERED":           "Доставлено",
    "CANCELED":            "Скасовано",
}

_STATUS_EMOJI = {
    "WAITING_FOR_COURIER": "🟡",
    "ACCEPTED":            "🟢",
    "PICKED_UP":           "🟠",
    "DELIVERING":          "🔵",
    "DELIVERED":           "✅",
    "CANCELED":            "❌",
}


def _get_status_emoji(status: str) -> str:
    """Return emoji indicator for order status."""
    return _STATUS_EMOJI.get(status, "◻️")


def _fmt_dt(dt) -> str:
    return dt.strftime("%d.%m.%Y %H:%M") if dt else "—"


@router.callback_query(F.data.startswith("order_details:"))
async def order_details_callback(callback: CallbackQuery):
    db = SessionLocal()
    try:
        order_id = int(callback.data.split(":", 1)[1])
        order: Order | None = db.get(Order, order_id)

        if order is None:
            await callback.answer("❌ Заявку не знайдено", show_alert=True)
            return

        from_store   = order.from_store.name if order.from_store else "—"
        to_store     = order.to_store.name   if order.to_store   else "—"
        courier_name = order.courier.full_name if order.courier  else "Не призначений"
        size_label     = _SIZE_LABELS.get(order.size, "—")          if order.size     else "—"
        priority_label = _PRIORITY_LABELS.get(order.priority, "—")  if order.priority else "—"
        status_label   = _STATUS_LABELS.get(order.status, order.status)
        status_emoji   = _get_status_emoji(order.status)
        comment        = order.manager_comment or "—"

        text = (
            f"📦 Заявка №<b>{order.number}</b>\n\n"
            f"📍 Звідки:\n{from_store}\n\n"
            f"📍 Куди:\n{to_store}\n\n"
            f"👤 Кур'єр:\n{courier_name}\n\n"
            f"📦 Розмір:\n{size_label}\n\n"
            f"⭐ Пріоритет:\n{priority_label}\n\n"
            f"📝 Коментар:\n{comment}\n\n"
            f"{status_emoji} Статус:\n{status_label}\n\n"
            f"🕒 Створено:    {_fmt_dt(order.created_at)}\n"
            f"✅ Прийнято:    {_fmt_dt(order.accepted_at)}\n"
            f"📦 Забрано:      {_fmt_dt(order.picked_up_at)}\n"
            f"🎉 Доставлено:  {_fmt_dt(order.delivered_at)}"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="⬅️ До списку",
                callback_data="manager_orders:0",
            )
        ]])

        await callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer()

    except (ValueError, TypeError):
        await callback.answer("❌ Некоректний ідентифікатор заявки", show_alert=True)
    finally:
        db.close()


# ── My Orders (� Активні замовлення) ────────────────────────────────────────────────

def _order_card_text(order) -> str:
    from_store   = order.from_store.name  if order.from_store else "—"
    to_store     = order.to_store.name    if order.to_store   else "—"
    status       = _STATUS_LABELS.get(order.status, order.status)
    return (
        f"🟡 <b>№{order.number}</b>\n"
        f"{from_store}\n"
        f"↓\n"
        f"{to_store}\n"
        f"{status}"
    )


def _build_my_orders_message(
    active: list,
    completed: list,
    page: int,
) -> tuple[str, InlineKeyboardMarkup | None]:
    if not active:
        return "🟡 <b>Активні замовлення</b>\n\nУ вас немає активних замовлень.", None

    total_pages = max(1, math.ceil(len(active) / _MY_ORDERS_PAGE_SIZE))
    page        = max(0, min(page, total_pages - 1))
    start       = page * _MY_ORDERS_PAGE_SIZE
    page_slice  = active[start : start + _MY_ORDERS_PAGE_SIZE]

    lines: list[str] = ["� <b>Активні замовлення</b>\n"]
    keyboard_rows: list[list[InlineKeyboardButton]] = []

    # ── Active orders ──────────────────────────────────────────────
    if len(active) > 0:
        header = f"({len(active)} замовлень"
        if total_pages > 1:
            header += f", сторінка {page + 1} з {total_pages}"
        header += ")"
        lines.append(header)
        lines.append("")

        for order in page_slice:
            lines.append(_order_card_text(order))
            lines.append("―――――――――")
            emoji = _get_status_emoji(order.status)
            keyboard_rows.append([
                InlineKeyboardButton(
                    text=f"{emoji} №{order.number}",
                    callback_data=f"order_details:{order.id}",
                )
            ])

        if total_pages > 1:
            nav: list[InlineKeyboardButton] = []
            if page > 0:
                nav.append(InlineKeyboardButton(
                    text="◀️ Попередня",
                    callback_data=f"manager_orders:{page - 1}",
                ))
            if start + _MY_ORDERS_PAGE_SIZE < len(active):
                nav.append(InlineKeyboardButton(
                    text="Наступна ▶️",
                    callback_data=f"manager_orders:{page + 1}",
                ))
            if nav:
                keyboard_rows.append(nav)

    # Back button
    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="manager_back_to_menu",
        )
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows) if keyboard_rows else None
    return "\n".join(lines), keyboard

def _build_all_orders_message(
    all_orders: list,
    page: int,
) -> tuple[str, InlineKeyboardMarkup | None]:
    """Build message for displaying all orders (all statuses)."""
    if not all_orders:
        return "📋 <b>Всі замовлення</b>\n\nУ вас немає замовлень.", None

    total_pages = max(1, math.ceil(len(all_orders) / _MY_ORDERS_PAGE_SIZE))
    page        = max(0, min(page, total_pages - 1))
    start       = page * _MY_ORDERS_PAGE_SIZE
    page_slice  = all_orders[start : start + _MY_ORDERS_PAGE_SIZE]

    lines: list[str] = ["📋 <b>Всі замовлення</b>\n"]
    keyboard_rows: list[list[InlineKeyboardButton]] = []

    # ── All orders ──────────────────────────────────────────────
    if len(all_orders) > 0:
        header = f"({len(all_orders)} замовлень"
        if total_pages > 1:
            header += f", сторінка {page + 1} з {total_pages}"
        header += ")"
        lines.append(header)
        lines.append("")

        for order in page_slice:
            status = _STATUS_LABELS.get(order.status, order.status)
            created = _fmt_dt(order.created_at)
            order_text = (
                f"№<b>{order.number}</b>\n"
                f"{status}\n"
                f"📅 {created}"
            )
            lines.append(order_text)
            lines.append("―――――――――")
            emoji = _get_status_emoji(order.status)
            keyboard_rows.append([
                InlineKeyboardButton(
                    text=f"{emoji} №{order.number}",
                    callback_data=f"order_details:{order.id}",
                )
            ])

        if total_pages > 1:
            nav: list[InlineKeyboardButton] = []
            if page > 0:
                nav.append(InlineKeyboardButton(
                    text="◀️ Попередня",
                    callback_data=f"manager_all_orders:{page - 1}",
                ))
            if start + _MY_ORDERS_PAGE_SIZE < len(all_orders):
                nav.append(InlineKeyboardButton(
                    text="Наступна ▶️",
                    callback_data=f"manager_all_orders:{page + 1}",
                ))
            if nav:
                keyboard_rows.append(nav)

    # Back button
    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="manager_back_to_menu",
        )
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows) if keyboard_rows else None
    return "\n".join(lines), keyboard

@router.message(F.text.startswith("🟡 Активні замовлення"), ManagerFilter())
async def my_orders_handler(message: Message):
    db = SessionLocal()
    try:
        manager = ActivationService.get_manager(db, message.from_user.id)

        active, completed = ManagerService.get_my_created_orders(db, manager.id)
        text, keyboard = _build_my_orders_message(active, completed, page=0)
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

    finally:
        db.close()


@router.callback_query(F.data.startswith("manager_orders:"), ManagerFilter())
async def my_orders_page_callback(callback: CallbackQuery):
    db = SessionLocal()
    try:
        page = int(callback.data.split(":", 1)[1])

        manager = ActivationService.get_manager(db, callback.from_user.id)

        active, completed = ManagerService.get_my_created_orders(db, manager.id)
        text, keyboard = _build_my_orders_message(active, completed, page=page)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer()

    except (ValueError, TypeError):
        await callback.answer("❌ Некоректна сторінка", show_alert=True)
    finally:
        db.close()


@router.message(F.text.startswith("📋 Всі замовлення"), ManagerFilter())
async def all_orders_handler(message: Message):
    db = SessionLocal()
    try:
        manager = ActivationService.get_manager(db, message.from_user.id)

        active, completed = ManagerService.get_my_created_orders(db, manager.id)
        all_orders = active + completed
        # Sort by created_at descending (newest first)
        all_orders = sorted(all_orders, key=lambda o: o.created_at or datetime.min, reverse=True)
        
        text, keyboard = _build_all_orders_message(all_orders, page=0)
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

    finally:
        db.close()


@router.callback_query(F.data.startswith("manager_all_orders:"), ManagerFilter())
async def all_orders_page_callback(callback: CallbackQuery):
    db = SessionLocal()
    try:
        page = int(callback.data.split(":", 1)[1])

        manager = ActivationService.get_manager(db, callback.from_user.id)

        active, completed = ManagerService.get_my_created_orders(db, manager.id)
        all_orders = active + completed
        # Sort by created_at descending (newest first)
        all_orders = sorted(all_orders, key=lambda o: o.created_at or datetime.min, reverse=True)
        
        text, keyboard = _build_all_orders_message(all_orders, page=page)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer()

    except (ValueError, TypeError):
        await callback.answer("❌ Некоректна сторінка", show_alert=True)
    finally:
        db.close()


@router.callback_query(F.data == "manager_back_to_menu", ManagerFilter())
async def manager_back_to_menu(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        manager = ActivationService.get_manager(db, callback.from_user.id)

        active, completed = ManagerService.get_my_created_orders(db, manager.id)
        active_count = len(active)
        all_count = len(active) + len(completed)
        incoming_count = ManagerService.get_incoming_delivery_count(db, manager.id)

        await state.clear()
        await callback.message.answer(
            "📋 Головне меню",
            reply_markup=manager_main_menu(active_count=active_count, all_count=all_count, incoming_count=incoming_count),
        )
        await callback.answer()
    finally:
        db.close()


# ── Manager Statistics ──────────────────────────────────────────────────────
# Active order statuses (only for this manager's orders)
_MANAGER_ACTIVE_STATUSES = [
    OrderStatus.WAITING_FOR_COURIER,
    OrderStatus.ACCEPTED,
    OrderStatus.PICKED_UP,
    OrderStatus.DELIVERING,
]


def _get_manager_orders_for_date_range(db, manager_id: int, date_range: str) -> list:
    """Get all orders created by this manager, filtered by date range.
    
    Only returns orders where Order.created_by == manager_id.
    Never includes global or other managers' statistics.
    """
    from app.models.user import User
    
    today = date.today()
    
    # Base query: only orders created by this manager
    query = db.query(Order).filter(Order.created_by == manager_id)
    
    if date_range == "today":
        # Only orders created today
        query = query.filter(
            Order.created_at.isnot(None),
            Order.created_at >= datetime.combine(today, datetime.min.time()),
            Order.created_at < datetime.combine(today + timedelta(days=1), datetime.min.time()),
        )
    elif date_range == "month":
        # Only orders created this month
        month_start = today.replace(day=1)
        query = query.filter(
            Order.created_at.isnot(None),
            Order.created_at >= datetime.combine(month_start, datetime.min.time()),
        )
    # else: date_range == "all" - return all orders for this manager
    
    return query.order_by(Order.created_at.desc()).all()


def _calculate_manager_statistics(orders: list) -> dict:
    """Calculate order statistics for this manager only.
    
    Statistics include:
    - total: total orders created by this manager
    - active: orders in active states (waiting, accepted, picked up, delivering)
    - delivered: orders successfully delivered
    - canceled: orders that were canceled
    """
    total = len(orders)
    active = sum(1 for o in orders if o.status in _MANAGER_ACTIVE_STATUSES)
    delivered = sum(1 for o in orders if o.status == OrderStatus.DELIVERED)
    canceled = sum(1 for o in orders if o.status == OrderStatus.CANCELED)
    
    return {
        "total": total,
        "active": active,
        "delivered": delivered,
        "canceled": canceled,
    }


def _build_manager_statistics_message(stats: dict, date_range: str) -> str:
    """Build formatted manager statistics message.
    
    Shows only this manager's statistics, never global or other managers.
    """
    range_label = {
        "today": "📅 Сьогодні",
        "month": "📆 Цей місяць",
        "all": "🏆 За весь час",
    }.get(date_range, "🏆 За весь час")
    
    return (
        f"📊 <b>Статистика мене</b>\n\n"
        f"{range_label}\n\n"
        f"📦 Всього створено заявок: <b>{stats['total']}</b>\n"
        f"🟡 Активні заявки: <b>{stats['active']}</b>\n"
        f"✅ Доставлено: <b>{stats['delivered']}</b>\n"
        f"❌ Скасовано: <b>{stats['canceled']}</b>"
    )


def _build_manager_statistics_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for manager statistics date range selection.
    
    Uses dedicated manager_stats callbacks to ensure complete isolation
    from any admin panel routing.
    """
    buttons = [
        [
            InlineKeyboardButton(
                text="📅 Сьогодні",
                callback_data="manager_stats:today",
            )
        ],
        [
            InlineKeyboardButton(
                text="📆 Цей місяць",
                callback_data="manager_stats:month",
            )
        ],
        [
            InlineKeyboardButton(
                text="🏆 За весь час",
                callback_data="manager_stats:all",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="manager_stats_back",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text == "📊 Статистика", ManagerFilter())
async def statistics_handler(message: Message):
    """Display manager's statistics for all time by default."""
    db = SessionLocal()
    try:
        manager = ActivationService.get_manager(db, message.from_user.id)

        # Get all orders created by this manager for all time
        manager_orders = _get_manager_orders_for_date_range(db, manager.id, "all")
        
        # Calculate statistics for this manager only
        stats = _calculate_manager_statistics(manager_orders)
        
        text = _build_manager_statistics_message(stats, "all")
        keyboard = _build_manager_statistics_keyboard()
        
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

    finally:
        db.close()


@router.callback_query(F.data.startswith("manager_stats:"), ManagerFilter())
async def statistics_callback(callback: CallbackQuery):
    """Handle manager statistics date range selection."""
    db = SessionLocal()
    try:
        date_range = callback.data.split(":", 1)[1]
        
        manager = ActivationService.get_manager(db, callback.from_user.id)

        # Get orders created by this manager for the selected date range
        manager_orders = _get_manager_orders_for_date_range(db, manager.id, date_range)
        
        # Calculate statistics for this manager only
        stats = _calculate_manager_statistics(manager_orders)
        
        text = _build_manager_statistics_message(stats, date_range)
        keyboard = _build_manager_statistics_keyboard()
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer()

    finally:
        db.close()


@router.callback_query(F.data == "manager_stats_back")
async def manager_stats_back(callback: CallbackQuery, state: FSMContext):
    """Return to Manager Main Menu from Statistics.
    
    Uses dedicated manager_stats_back callback to ensure complete isolation
    from admin panel routing.
    """
    db = SessionLocal()
    try:
        manager = ActivationService.get_manager(db, callback.from_user.id)
        if manager is None:
            await callback.answer("❌ Користувача не знайдено", show_alert=True)
            return

        active, completed = ManagerService.get_my_created_orders(db, manager.id)
        active_count = len(active)
        all_count = len(active) + len(completed)
        incoming_count = ManagerService.get_incoming_delivery_count(db, manager.id)

        await state.clear()
        await callback.message.answer(
            "📋 Головне меню",
            reply_markup=manager_main_menu(active_count=active_count, all_count=all_count, incoming_count=incoming_count),
        )
        await callback.answer()
    finally:
        db.close()


# ── Manager Couriers ───────────────────────────────────────────────────────

def _get_couriers_by_availability(db, availability: CourierAvailability) -> list:
    """Get all couriers filtered by availability status."""
    from app.models.user import User, UserRole
    return (
        db.query(User)
        .filter(
            User.role == UserRole.COURIER,
            User.availability == availability,
            User.telegram_id.isnot(None),
        )
        .order_by(User.full_name)
        .all()
    )


def _get_busy_courier_current_order(db, courier_id: int) -> Order | None:
    """Get the current active order for a BUSY courier."""
    return (
        db.query(Order)
        .filter(
            Order.courier_id == courier_id,
            Order.status.in_([
                OrderStatus.ACCEPTED,
                OrderStatus.PICKED_UP,
                OrderStatus.DELIVERING,
            ]),
        )
        .order_by(Order.id.desc())
        .first()
    )


def _build_couriers_category_message() -> str:
    """Build message for couriers category selection."""
    return (
        "👥 <b>Кур'єри</b>\n\n"
        "Оберіть категорію, щоб переглянути кур'єрів:"
    )


def _build_couriers_category_keyboard(db) -> InlineKeyboardMarkup:
    """Build keyboard for couriers category selection."""
    available_count = len(_get_couriers_by_availability(db, CourierAvailability.AVAILABLE))
    busy_count = len(_get_couriers_by_availability(db, CourierAvailability.BUSY))
    offline_count = len(_get_couriers_by_availability(db, CourierAvailability.OFFLINE))
    
    buttons = [
        [
            InlineKeyboardButton(
                text=f"🟢 На зміні ({available_count})",
                callback_data="manager_couriers:available",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🟡 Доставляє ({busy_count})",
                callback_data="manager_couriers:busy",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"⚫ Не онлайн ({offline_count})",
                callback_data="manager_couriers:offline",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="manager_back_to_menu",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_couriers_list_message(couriers: list, availability: str, db) -> str:
    """Build message for displaying couriers list."""
    availability_labels = {
        "available": "На зміні",
        "busy": "Доставляє",
        "offline": "Не онлайн",
    }
    
    label = availability_labels.get(availability, availability)
    
    if not couriers:
        return f"👥 <b>Кур'єри ({label})</b>\n\nКур'єрів немає."
    
    lines = [f"👥 <b>Кур'єри ({label})</b>\n"]
    lines.append(f"({len(couriers)} кур'єрів)\n")
    
    for courier in couriers:
        lines.append(f"👤 {courier.full_name}")
        
        # For BUSY couriers, show current order number
        if availability == "busy":
            current_order = _get_busy_courier_current_order(db, courier.id)
            if current_order:
                lines.append(f"   📦 Замовлення: №{current_order.number}")
        
        lines.append("")
    
    return "\n".join(lines)


def _build_couriers_back_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for going back from couriers list."""
    buttons = [
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="manager_couriers_back",
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text == "👥 Кур'єри", ManagerFilter())
async def couriers_handler(message: Message):
    db = SessionLocal()
    try:
        manager = ActivationService.get_manager(db, message.from_user.id)
        
        text = _build_couriers_category_message()
        keyboard = _build_couriers_category_keyboard(db)
        
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

    finally:
        db.close()


@router.callback_query(F.data.startswith("manager_couriers:"))
async def couriers_category_callback(callback: CallbackQuery):
    db = SessionLocal()
    try:
        category = callback.data.split(":", 1)[1]
        
        # Map category to availability status
        availability_map = {
            "available": CourierAvailability.AVAILABLE,
            "busy": CourierAvailability.BUSY,
            "offline": CourierAvailability.OFFLINE,
        }
        
        availability = availability_map.get(category)
        if availability is None:
            await callback.answer("❌ Невідома категорія", show_alert=True)
            return
        
        # Get couriers for this category
        couriers = _get_couriers_by_availability(db, availability)
        
        text = _build_couriers_list_message(couriers, category, db)
        keyboard = _build_couriers_back_keyboard()
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer()

    finally:
        db.close()


@router.callback_query(F.data == "manager_couriers_back")
async def couriers_back_callback(callback: CallbackQuery):
    db = SessionLocal()
    try:
        text = _build_couriers_category_message()
        keyboard = _build_couriers_category_keyboard(db)
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer()

    finally:
        db.close()


# ── Manager Profile ───────────────────────────────────────────────────────

def _get_store_network_name(network: "StoreNetwork") -> str:
    """Get display name for store network."""
    from app.models.store import StoreNetwork
    network_labels = {
        StoreNetwork.APPLE_ROOM: "🍏 AppleRoom",
        StoreNetwork.JABKO: "🍏 Ябко",
    }
    return network_labels.get(network, str(network))


def _fmt_last_login(last_login_at) -> str:
    """Format last login datetime."""
    if not last_login_at:
        return "Ніколи"
    return last_login_at.strftime("%d.%m.%Y %H:%M")


def _build_profile_message(manager, store) -> str:
    """Build profile message with manager information."""
    username = manager.username or "Не вказано"
    status_label = "✅ Активний" if manager.status.value == "ACTIVE" else "❌ Неактивний"
    last_login = _fmt_last_login(manager.last_login_at)
    network_name = _get_store_network_name(store.network) if store else "—"
    store_name = store.name if store else "—"
    
    return (
        f"👤 <b>Профіль</b>\n\n"
        f"👤 ПІБ:\n{manager.full_name}\n\n"
        f"🏪 Магазин:\n{store_name}\n\n"
        f"🏢 Мережа:\n{network_name}\n\n"
        f"📱 Telegram:\n@{username}\n\n"
        f"🟢 Статус:\n{status_label}\n\n"
        f"🕒 Останній вхід:\n{last_login}\n\n"
        f"────────────────\n\n"
        f"🔒 <i>Зміна персональних даних здійснюється адміністратором.</i>"
    )


def _build_profile_keyboard() -> InlineKeyboardMarkup:
    """Build profile page keyboard."""
    buttons = [
        [
            InlineKeyboardButton(
                text="🏪 Мій магазин",
                callback_data="manager_profile:store",
            )
        ],
        [
            InlineKeyboardButton(
                text="ℹ️ Про акаунт",
                callback_data="manager_profile:account",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="manager_back_to_menu",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_store_info_message(store) -> str:
    """Build detailed store information message."""
    if not store:
        return "🏪 <b>Мій магазин</b>\n\nМагазин не призначений."
    
    network_name = _get_store_network_name(store.network)
    
    return (
        f"🏪 <b>Мій магазин</b>\n\n"
        f"<b>Назва:</b> {store.name}\n\n"
        f"<b>Мережа:</b> {network_name}\n\n"
        f"<b>Адреса:</b>\n{store.address}\n\n"
        f"<b>Місто:</b> {store.city}\n\n"
        f"<b>Координати:</b>\n{store.latitude}, {store.longitude}"
    )


def _build_account_info_message(manager) -> str:
    """Build account information message."""
    return (
        "ℹ️ <b>Про акаунт</b>\n\n"
        "Ваш акаунт керується адміністратором системи.\n\n"
        "<b>Для:</b>\n\n"
        "• зміни магазину;\n"
        "• переприв'язки Telegram;\n"
        "• відновлення доступу;\n"
        "• зміни персональних даних;\n\n"
        "зверніться до адміністратора."
    )


def _build_profile_back_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for going back from profile subpages."""
    buttons = [
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="manager_profile_back",
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_incoming_deliveries_keyboard(
    orders: list[Order],
    page: int = 0,
    page_size: int = _MY_ORDERS_PAGE_SIZE,
) -> InlineKeyboardMarkup:
    """Build keyboard for incoming deliveries list with pagination."""
    start = page * page_size
    end = start + page_size
    visible_orders = orders[start:end]

    buttons = []
    for order in visible_orders:
        from_store = order.from_store.name if order.from_store else "—"
        status_icon = "✅" if order.status == OrderStatus.DELIVERED else "📦"
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{status_icon} {order.number} | {from_store}",
                    callback_data=f"manager_incoming_detail:{order.id}",
                )
            ]
        )

    # Add pagination buttons
    total_pages = math.ceil(len(orders) / page_size)
    if total_pages > 1:
        nav = []
        if page > 0:
            nav.append(
                InlineKeyboardButton(
                    text="◀️ Попередня",
                    callback_data=f"manager_incoming_orders:{page - 1}",
                )
            )
        if end < len(orders):
            nav.append(
                InlineKeyboardButton(
                    text="Наступна ▶️",
                    callback_data=f"manager_incoming_orders:{page + 1}",
                )
            )
        if nav:
            buttons.append(nav)

    # Add back button
    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ До меню",
                callback_data="manager_incoming_back_to_menu",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_incoming_delivery_detail_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Build keyboard for incoming delivery detail view."""
    buttons = [
        [
            InlineKeyboardButton(
                text="📋 История статуса",
                callback_data=f"manager_incoming_timeline:{order_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ До списку",
                callback_data="manager_incoming_back_to_list",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_incoming_deliveries_history_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for incoming deliveries history date range selection."""
    buttons = [
        [
            InlineKeyboardButton(
                text="📅 Сьогодні",
                callback_data="manager_incoming_history:today",
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 7 днів",
                callback_data="manager_incoming_history:week",
            )
        ],
        [
            InlineKeyboardButton(
                text="📈 30 днів",
                callback_data="manager_incoming_history:month",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ До меню",
                callback_data="manager_incoming_back_to_menu",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_incoming_deliveries_message(
    orders: list[Order],
    page: int = 0,
    page_size: int = _MY_ORDERS_PAGE_SIZE,
) -> str:
    """Build message for incoming deliveries list."""
    if not orders:
        return "📥 До нас їдуть\n\nЗараз немає активних доставок."

    start = page * page_size
    end = start + page_size
    visible_orders = orders[start:end]
    total_pages = math.ceil(len(orders) / page_size)

    lines = [f"📥 До нас їдуть ({len(orders)})"]
    lines.append("")

    for idx, order in enumerate(visible_orders, start=start + 1):
        from_store = order.from_store.name if order.from_store else "—"
        courier = order.courier.full_name if order.courier else "Немає"
        status_label = order.status.value if hasattr(order.status, 'value') else str(order.status)

        lines.append(f"{idx}. <b>{order.number}</b>")
        lines.append(f"   🏪 З: {from_store}")
        lines.append(f"   👤 Курьєр: {courier}")
        lines.append(f"   📍 Статус: {status_label}")
        lines.append("")

    if total_pages > 1:
        lines.append(f"Сторінка {page + 1} з {total_pages}")

    return "\n".join(lines)


def _build_incoming_delivery_detail_message(order: Order) -> str:
    """Build message for incoming delivery detail view."""
    from_store = order.from_store.name if order.from_store else "—"
    to_store = order.to_store.name if order.to_store else "—"
    courier = order.courier.full_name if order.courier else "Не призначено"
    priority = order.priority.value if hasattr(order.priority, 'value') else str(order.priority)
    status = order.status.value if hasattr(order.status, 'value') else str(order.status)
    created_time = order.created_at.strftime("%d.%m.%Y %H:%M") if order.created_at else "—"

    lines = [
        f"📦 <b>{order.number}</b>",
        "",
        f"🏪 <b>З магазину:</b> {from_store}",
        f"🏪 <b>В магазин:</b> {to_store}",
        f"👤 <b>Курьєр:</b> {courier}",
        f"⭐ <b>Пріоритет:</b> {priority}",
        f"📍 <b>Статус:</b> {status}",
        f"⏰ <b>Створено:</b> {created_time}",
    ]

    if order.manager_comment:
        lines.append(f"💬 <b>Коментар:</b> {order.manager_comment}")

    return "\n".join(lines)


@router.message(F.text == "👤 Профіль", ManagerFilter())
async def profile_handler(message: Message):
    from app.models.store import Store
    db = SessionLocal()
    try:
        manager = ActivationService.get_manager(db, message.from_user.id)
        
        # Get manager's store
        store = None
        if manager.store_id:
            store = db.get(Store, manager.store_id)
        
        text = _build_profile_message(manager, store)
        keyboard = _build_profile_keyboard()
        
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

    finally:
        db.close()


@router.callback_query(F.data.startswith("manager_profile:"), ManagerFilter())
async def profile_category_callback(callback: CallbackQuery):
    from app.models.store import Store
    db = SessionLocal()
    try:
        category = callback.data.split(":", 1)[1]
        
        manager = ActivationService.get_manager(db, callback.from_user.id)
        
        if category == "store":
            # Get manager's store
            store = None
            if manager.store_id:
                store = db.get(Store, manager.store_id)
            
            text = _build_store_info_message(store)
            keyboard = _build_profile_back_keyboard()
            
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
            await callback.answer()
        
        elif category == "account":
            text = _build_account_info_message(manager)
            keyboard = _build_profile_back_keyboard()
            
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
            await callback.answer()
        
        else:
            await callback.answer("❌ Невідома категорія", show_alert=True)

    finally:
        db.close()


@router.callback_query(F.data == "manager_profile_back", ManagerFilter())
async def profile_back_callback(callback: CallbackQuery):
    from app.models.store import Store
    db = SessionLocal()
    try:
        manager = ActivationService.get_manager(db, callback.from_user.id)
        
        # Get manager's store
        store = None
        if manager.store_id:
            store = db.get(Store, manager.store_id)
        
        text = _build_profile_message(manager, store)
        keyboard = _build_profile_keyboard()
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer()

    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
# INCOMING DELIVERIES MODULE
# ═══════════════════════════════════════════════════════════════════════════


@router.message(F.text.startswith("📥 До нас їдуть"), ManagerFilter())
async def incoming_deliveries_handler(message: Message):
    """Display incoming deliveries for manager's store."""
    db = SessionLocal()
    try:
        manager = ActivationService.get_manager(db, message.from_user.id)
        
        # Get active incoming deliveries
        orders = ManagerService.get_incoming_active_deliveries(db, manager.id)
        
        text = _build_incoming_deliveries_message(orders, page=0)
        keyboard = _build_incoming_deliveries_keyboard(orders, page=0)
        
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

    except ValueError as exc:
        await message.answer(f"❌ {exc}")

    finally:
        db.close()


@router.callback_query(F.data.startswith("manager_incoming_orders:"), ManagerFilter())
async def incoming_deliveries_page_callback(callback: CallbackQuery):
    """Handle incoming deliveries pagination."""
    db = SessionLocal()
    try:
        page = int(callback.data.split(":", 1)[1])
        
        manager = ActivationService.get_manager(db, callback.from_user.id)
        
        # Get active incoming deliveries
        orders = ManagerService.get_incoming_active_deliveries(db, manager.id)
        
        text = _build_incoming_deliveries_message(orders, page=page)
        keyboard = _build_incoming_deliveries_keyboard(orders, page=page)
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer()

    except ValueError as exc:
        await callback.answer(f"❌ {exc}", show_alert=True)

    finally:
        db.close()


@router.callback_query(F.data.startswith("manager_incoming_detail:"), ManagerFilter())
async def incoming_delivery_detail_callback(callback: CallbackQuery):
    """Show incoming delivery detail view."""
    db = SessionLocal()
    try:
        order_id = int(callback.data.split(":", 1)[1])
        order = db.get(Order, order_id)

        if order is None:
            await callback.answer("❌ Замовлення не знайдено", show_alert=True)
            return

        manager = ActivationService.get_manager(db, callback.from_user.id)

        # Verify that this delivery is to manager's store
        if order.to_store_id != manager.store_id:
            await callback.answer("❌ У вас немає доступу до цієї доставки", show_alert=True)
            return

        text = _build_incoming_delivery_detail_message(order)
        keyboard = _build_incoming_delivery_detail_keyboard(order_id)

        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer()

    except ValueError as exc:
        await callback.answer(f"❌ {exc}", show_alert=True)

    finally:
        db.close()


@router.callback_query(F.data == "manager_incoming_back_to_list", ManagerFilter())
async def incoming_delivery_back_to_list_callback(callback: CallbackQuery):
    """Return to incoming deliveries list from detail view."""
    db = SessionLocal()
    try:
        manager = ActivationService.get_manager(db, callback.from_user.id)
        
        # Get active incoming deliveries
        orders = ManagerService.get_incoming_active_deliveries(db, manager.id)
        
        text = _build_incoming_deliveries_message(orders, page=0)
        keyboard = _build_incoming_deliveries_keyboard(orders, page=0)
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer()

    finally:
        db.close()


@router.callback_query(F.data == "manager_incoming_back_to_menu", ManagerFilter())
async def incoming_delivery_back_to_menu_callback(callback: CallbackQuery):
    """Return to manager main menu from incoming deliveries."""
    db = SessionLocal()
    try:
        manager = ActivationService.get_manager(db, callback.from_user.id)
        
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
        await callback.answer()

    finally:
        db.close()


@router.callback_query(F.data.startswith("manager_incoming_timeline:"), ManagerFilter())
async def incoming_delivery_timeline_callback(callback: CallbackQuery):
    """Show order status timeline for incoming delivery."""
    db = SessionLocal()
    try:
        order_id = int(callback.data.split(":", 1)[1])
        order = db.get(Order, order_id)

        if order is None:
            await callback.answer("❌ Замовлення не знайдено", show_alert=True)
            return

        manager = ActivationService.get_manager(db, callback.from_user.id)

        # Verify access
        if order.to_store_id != manager.store_id:
            await callback.answer("❌ У вас немає доступу до цієї доставки", show_alert=True)
            return

        lines = [f"📅 <b>История статуса #{order.number}</b>", ""]

        if order.created_at:
            lines.append(f"📝 Створено: {order.created_at.strftime('%d.%m.%Y %H:%M')}")

        if order.accepted_at:
            lines.append(f"✅ Прийнято: {order.accepted_at.strftime('%d.%m.%Y %H:%M')}")

        if order.picked_up_at:
            lines.append(f"📦 Забрано: {order.picked_up_at.strftime('%d.%m.%Y %H:%M')}")

        if order.delivered_at:
            lines.append(f"🎉 Доставлено: {order.delivered_at.strftime('%d.%m.%Y %H:%M')}")

        text = "\n".join(lines)
        keyboard = _build_incoming_delivery_detail_keyboard(order_id)

        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer()

    finally:
        db.close()
