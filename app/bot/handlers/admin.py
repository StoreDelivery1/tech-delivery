import logging
from datetime import datetime, date, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.bot.keyboards.main_menu import (
    admin_users_menu,
    admin_main_menu,
)
from app.bot.filters.roles import AdminFilter
from app.bot.states.admin import AdminCourierState, AdminManagerState, AdminOrderSearchState
from app.database.session import SessionLocal
from app.models.store import StoreNetwork, Store
from app.models.user import UserRole, User, UserStatus, CourierAvailability
from app.models.order import Order, OrderStatus, OrderPriority
from app.schemas.user import UserCreate
from app.services.store_service import StoreService
from app.services.user_service import UserService
from app.services.activation_service import ActivationService

logger = logging.getLogger(__name__)

router = Router()

NETWORKS = {
    "apple": {
        "label": "🍏 AppleRoom",
        "network": StoreNetwork.APPLE_ROOM,
    },
    "yabko": {
        "label": "🍎 Ябко",
        "network": StoreNetwork.JABKO,
    },
}


def build_manager_network_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=config["label"],
                callback_data=f"admin_manager_network:{network_key}",
            )
        ]
        for network_key, config in NETWORKS.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_manager_store_keyboard(stores: list) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"🏬 {store.name}",
                callback_data=f"admin_manager_store:{store.id}",
            )
        ]
        for store in stores
    ]
    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_manager_back")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_managers_list_keyboard(managers: list, page: int = 0, page_size: int = 10) -> InlineKeyboardMarkup:
    # Sort: active first, then inactive, alphabetically within each group
    active_managers = sorted(
        [m for m in managers if m.telegram_id is not None],
        key=lambda m: m.full_name
    )
    inactive_managers = sorted(
        [m for m in managers if m.telegram_id is None],
        key=lambda m: m.full_name
    )
    sorted_managers = active_managers + inactive_managers
    
    # Pagination
    total_pages = (len(sorted_managers) + page_size - 1) // page_size
    start_idx = page * page_size
    end_idx = start_idx + page_size
    page_managers = sorted_managers[start_idx:end_idx]
    
    buttons = []
    for manager in page_managers:
        store_name = manager.store.name if manager.store else "Не призначен"
        network_label = ""
        if manager.store:
            if manager.store.network.value == "APPLE_ROOM":
                network_label = "🍏 AppleRoom"
            elif manager.store.network.value == "JABKO":
                network_label = "🍎 Ябко"
        
        button_text = f"👤 {manager.full_name}\n🏪 {network_label} {store_name}".strip()
        buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"admin_manager_detail:{manager.id}",
            )
        ])
    
    # Add pagination buttons
    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="◀️ Попередня",
                callback_data=f"admin_managers_page:{page - 1}",
            )
        )
    if page < total_pages - 1:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="Наступна ▶️",
                callback_data=f"admin_managers_page:{page + 1}",
            )
        )
    
    if pagination_buttons:
        buttons.append(pagination_buttons)
    
    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="admin_managers_back",
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_couriers_list_keyboard(couriers: list, page: int = 0, page_size: int = 10) -> InlineKeyboardMarkup:
    # Sort: BUSY → AVAILABLE → OFFLINE, then alphabetically within each group
    busy_couriers = sorted(
        [c for c in couriers if c.availability == CourierAvailability.BUSY],
        key=lambda c: c.full_name
    )
    available_couriers = sorted(
        [c for c in couriers if c.availability == CourierAvailability.AVAILABLE],
        key=lambda c: c.full_name
    )
    offline_couriers = sorted(
        [c for c in couriers if c.availability == CourierAvailability.OFFLINE],
        key=lambda c: c.full_name
    )
    sorted_couriers = busy_couriers + available_couriers + offline_couriers
    
    # Pagination
    total_pages = (len(sorted_couriers) + page_size - 1) // page_size
    start_idx = page * page_size
    end_idx = start_idx + page_size
    page_couriers = sorted_couriers[start_idx:end_idx]
    
    # We need db access to get delivering orders for BUSY couriers
    db = SessionLocal()
    try:
        buttons = []
        for courier in page_couriers:
            status_emoji = ""
            if courier.availability == CourierAvailability.BUSY:
                status_emoji = "🟡 "
            elif courier.availability == CourierAvailability.AVAILABLE:
                status_emoji = "🟢 "
            elif courier.availability == CourierAvailability.OFFLINE:
                status_emoji = "⚫ "
            
            button_text = f"{status_emoji}{courier.full_name}"
            
            # For BUSY couriers, add order number
            if courier.availability == CourierAvailability.BUSY:
                delivering_order = db.query(Order).filter(
                    Order.courier_id == courier.id,
                    Order.status == OrderStatus.DELIVERING
                ).first()
                if delivering_order:
                    button_text += f"\n📦 №{delivering_order.number}"
            
            buttons.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"admin_courier_profile:{courier.id}",
                )
            ])
        
        # Add pagination buttons
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="◀️ Попередня",
                    callback_data=f"admin_couriers_page:{page - 1}",
                )
            )
        if page < total_pages - 1:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="Наступна ▶️",
                    callback_data=f"admin_couriers_page:{page + 1}",
                )
            )
        
        if pagination_buttons:
            buttons.append(pagination_buttons)
        
        buttons.append([
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="admin_couriers_back",
            )
        ])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    finally:
        db.close()


def build_manager_profile_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="🏪 Змінити магазин",
                callback_data="admin_manager_profile_change_store",
            )
        ],
        [
            InlineKeyboardButton(
                text="🔑 Переприв'язати Telegram",
                callback_data="admin_manager_profile_repair_telegram",
            )
        ],
        [
            InlineKeyboardButton(
                text="🚫 Деактивувати",
                callback_data="admin_manager_profile_deactivate",
            )
        ],
        [
            InlineKeyboardButton(
                text="🗑 Видалити",
                callback_data="admin_manager_profile_delete",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="admin_manager_profile_back",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_month_statistics_menu_keyboard(month_offset=0) -> InlineKeyboardMarkup:
    """Build keyboard for month statistics navigation.
    month_offset: 0 = current month, -1 = previous month, etc.
    Only allows going to past months.
    """
    buttons = []
    
    # Previous month button
    buttons.append([
        InlineKeyboardButton(
            text="◀️ Попередній",
            callback_data=f"admin_stats_month:{month_offset-1}",
        )
    ])
    
    # Current month button (always shows current month display)
    buttons.append([
        InlineKeyboardButton(
            text="📆 Поточний місяць" if month_offset == 0 else "📆 Вибрати місяць",
            callback_data="admin_stats_month:0",
        )
    ])
    
    # Next month button (only if not at current month)
    if month_offset < 0:
        buttons.append([
            InlineKeyboardButton(
                text="Наступний ▶️",
                callback_data=f"admin_stats_month:{month_offset+1}",
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="admin_stats_back",
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_orders_menu_keyboard(waiting_count: int, in_progress_count: int, delivered_count: int, canceled_count: int) -> InlineKeyboardMarkup:
    """Build keyboard for orders management with status counters."""
    buttons = [
        [
            InlineKeyboardButton(
                text=f"🟡 Очікують кур'єра ({waiting_count})",
                callback_data="admin_orders_waiting",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🚚 В роботі ({in_progress_count})",
                callback_data="admin_orders_in_progress",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"✅ Доставлені ({delivered_count})",
                callback_data="admin_orders_delivered",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"❌ Скасовані ({canceled_count})",
                callback_data="admin_orders_canceled",
            )
        ],
        [
            InlineKeyboardButton(
                text="────────────",
                callback_data="admin_orders_separator",
            )
        ],
        [
            InlineKeyboardButton(
                text="🔥 Термінові",
                callback_data="admin_orders_urgent",
            )
        ],
        [
            InlineKeyboardButton(
                text="🔍 Пошук заявки",
                callback_data="admin_orders_search",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="admin_orders_back",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_statistics_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="📅 Сьогодні",
                callback_data="admin_stats_today",
            )
        ],
        [
            InlineKeyboardButton(
                text="📆 Цей місяць",
                callback_data="admin_stats_month:0",
            )
        ],
        [
            InlineKeyboardButton(
                text="📈 За весь час",
                callback_data="admin_stats_all_time",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="admin_stats_back",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text == "👥 Користувачі", AdminFilter())
async def admin_users_menu_handler(message: Message):
    await message.answer(
        "👥 Користувачі",
        reply_markup=admin_users_menu(),
    )


@router.message(F.text == "📊 Статистика", AdminFilter())
async def admin_statistics_handler(message: Message):
    await message.answer(
        "📊 Статистика",
        reply_markup=build_statistics_menu_keyboard(),
    )


@router.message(F.text == "📦 Замовлення", AdminFilter())
async def admin_orders_handler(message: Message):
    db = SessionLocal()
    try:
        # Get all orders
        all_orders = db.query(Order).all()
        
        # Count orders by status
        waiting_count = len([o for o in all_orders if o.status == OrderStatus.WAITING_FOR_COURIER])
        in_progress_count = len([o for o in all_orders if o.status in (OrderStatus.ACCEPTED, OrderStatus.PICKED_UP, OrderStatus.DELIVERING)])
        delivered_count = len([o for o in all_orders if o.status == OrderStatus.DELIVERED])
        canceled_count = len([o for o in all_orders if o.status == OrderStatus.CANCELED])
        
        await message.answer(
            "📦 Замовлення",
            reply_markup=build_orders_menu_keyboard(waiting_count, in_progress_count, delivered_count, canceled_count),
        )
    finally:
        db.close()


@router.message(F.text == "👤 Профіль", AdminFilter())
async def admin_profile_handler(message: Message, state: FSMContext):
    db = SessionLocal()
    try:
        # Get current admin user from database using telegram_id
        admin = db.query(User).filter(
            User.telegram_id == message.from_user.id,
            User.role == UserRole.ADMIN
        ).first()
        
        if not admin:
            await message.answer(
                "❌ Не вдалося завантажити профіль.",
                reply_markup=admin_main_menu(),
            )
            return
        
        # Store admin_id in state for profile actions
        await state.update_data(current_admin_id=admin.id)
        
        # Format role name
        role_map = {
            UserRole.ADMIN: "🛡 Адміністратор",
            UserRole.MANAGER: "👨‍💼 Менеджер",
            UserRole.COURIER: "🚴 Кур'єр",
        }
        role_text = role_map.get(admin.role, "—")
        
        # Format username
        username_text = f"@{admin.username}" if admin.username else "Не вказано"
        
        # Format last login
        last_login_text = admin.last_login_at.strftime("%d.%m.%Y %H:%M") if admin.last_login_at else "—"
        
        # Build profile text
        profile_text = (
            f"👤 Профіль\n\n"
            f"👤 {admin.full_name}\n"
            f"{role_text}\n"
            f"🆔 ID: {admin.id}\n"
            f"📱 {username_text}\n"
            f"🟢 Online\n"
            f"🕒 Останній вхід: {last_login_text}\n\n"
            f"────────────"
        )
        
        # Build profile buttons
        buttons = [
            [InlineKeyboardButton(text="🔑 Переприв'язати Telegram", callback_data="admin_profile_repair_telegram")],
            [InlineKeyboardButton(text="📊 Моя статистика", callback_data="admin_profile_my_stats")],
            [InlineKeyboardButton(text="📜 Журнал моїх дій", callback_data="admin_profile_my_log")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_profile_to_main_menu")],
        ]
        
        await message.answer(
            profile_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
    finally:
        db.close()


@router.callback_query(F.data == "admin_profile_repair_telegram", AdminFilter())
async def admin_profile_repair_telegram(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        data = await state.get_data()
        admin_id = data.get("current_admin_id")
        
        if not admin_id:
            await callback.message.answer("❌ Не вдалося визначити адміністратора.")
            await callback.answer()
            return
        
        admin = db.get(User, admin_id)
        if not admin:
            await callback.message.answer("❌ Адміністратора не знайдено.")
            await callback.answer()
            return
        
        # Clear telegram fields to invalidate previous connection
        admin.telegram_id = None
        admin.username = None
        
        # Generate new activation code and set expiration
        ActivationService.assign_activation_code(db, admin)
        
        # Format expiration time
        expiration_time = admin.activation_code_expires_at.strftime("%H:%M") if admin.activation_code_expires_at else "—"
        
        confirmation_text = (
            f"🔑 Новий код\n\n"
            f"{admin.activation_code}\n\n"
            f"Дійсний до:\n{expiration_time}"
        )
        
        await callback.message.answer(
            confirmation_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Згенерувати ще", callback_data="admin_profile_repair_telegram_regenerate")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_profile_back")],
            ])
        )
        await callback.answer()
    except Exception as exc:
        logger.exception("Failed to repair admin telegram")
        await callback.message.answer("❌ Не вдалося переприв'язати Telegram.")
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_profile_repair_telegram_regenerate", AdminFilter())
async def admin_profile_repair_telegram_regenerate(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        data = await state.get_data()
        admin_id = data.get("current_admin_id")
        
        if not admin_id:
            await callback.message.answer("❌ Не вдалося визначити адміністратора.")
            await callback.answer()
            return
        
        admin = db.get(User, admin_id)
        if not admin:
            await callback.message.answer("❌ Адміністратора не знайдено.")
            await callback.answer()
            return
        
        # Generate new activation code (invalidates previous)
        ActivationService.assign_activation_code(db, admin)
        
        # Format expiration time
        expiration_time = admin.activation_code_expires_at.strftime("%H:%M") if admin.activation_code_expires_at else "—"
        
        confirmation_text = (
            f"🔑 Новий код\n\n"
            f"{admin.activation_code}\n\n"
            f"Дійсний до:\n{expiration_time}"
        )
        
        await callback.message.edit_text(
            confirmation_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Згенерувати ще", callback_data="admin_profile_repair_telegram_regenerate")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_profile_back")],
            ])
        )
        await callback.answer()
    except Exception as exc:
        logger.exception("Failed to regenerate admin activation code")
        await callback.message.answer("❌ Не вдалося регенерувати код.")
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_profile_my_stats", AdminFilter())
async def admin_profile_my_stats(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        data = await state.get_data()
        admin_id = data.get("current_admin_id")
        
        if not admin_id:
            await callback.message.answer("❌ Не вдалося завантажити профіль.")
            await callback.answer()
            return
        
        admin = db.get(User, admin_id)
        if not admin:
            await callback.message.answer("❌ Адміністратора не знайдено.")
            await callback.answer()
            return
        
        # Display statistics
        # Note: These statistics are not yet tracked in the database,
        # so we display "—" for all metrics as per requirements
        stats_text = (
            f"📊 Моя статистика\n\n"
            f"👨‍💼 Створено менеджерів: —\n"
            f"🚴 Створено кур'єрів: —\n"
            f"🔑 Переприв'язано Telegram: —\n"
            f"🏪 Змінено магазинів: —\n"
            f"🚫 Деактивовано користувачів: —\n"
            f"🗑 Видалено користувачів: —"
        )
        
        await callback.message.answer(
            stats_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_profile_back")],
            ])
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_profile_my_log", AdminFilter())
async def admin_profile_my_log(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        data = await state.get_data()
        admin_id = data.get("current_admin_id")
        
        if not admin_id:
            await callback.message.answer("❌ Не вдалося завантажити профіль.")
            await callback.answer()
            return
        
        admin = db.get(User, admin_id)
        if not admin:
            await callback.message.answer("❌ Адміністратора не знайдено.")
            await callback.answer()
            return
        
        # Show action log page
        await callback.message.answer(
            "📜 Журнал дій\n\n"
            "Функція буде доступна у наступному оновленні.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_profile_back")],
            ])
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_profile_back", AdminFilter())
async def admin_profile_back(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        data = await state.get_data()
        admin_id = data.get("current_admin_id")
        
        if not admin_id:
            await callback.message.answer("❌ Не вдалося завантажити профіль.")
            await callback.answer()
            return
        
        admin = db.get(User, admin_id)
        if not admin:
            await callback.message.answer("❌ Адміністратора не знайдено.")
            await callback.answer()
            return
        
        # Format role name
        role_map = {
            UserRole.ADMIN: "🛡 Адміністратор",
            UserRole.MANAGER: "👨‍💼 Менеджер",
            UserRole.COURIER: "🚴 Кур'єр",
        }
        role_text = role_map.get(admin.role, "—")
        
        # Format username
        username_text = f"@{admin.username}" if admin.username else "Не вказано"
        
        # Format last login
        last_login_text = admin.last_login_at.strftime("%d.%m.%Y %H:%M") if admin.last_login_at else "—"
        
        # Build profile text
        profile_text = (
            f"👤 Профіль\n\n"
            f"👤 {admin.full_name}\n"
            f"{role_text}\n"
            f"🆔 ID: {admin.id}\n"
            f"📱 {username_text}\n"
            f"🟢 Online\n"
            f"🕒 Останній вхід: {last_login_text}\n\n"
            f"────────────"
        )
        
        # Build profile buttons
        buttons = [
            [InlineKeyboardButton(text="🔑 Переприв'язати Telegram", callback_data="admin_profile_repair_telegram")],
            [InlineKeyboardButton(text="📊 Моя статистика", callback_data="admin_profile_my_stats")],
            [InlineKeyboardButton(text="📜 Журнал моїх дій", callback_data="admin_profile_my_log")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_profile_to_main_menu")],
        ]
        
        await callback.message.edit_text(
            profile_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_profile_to_main_menu", AdminFilter())
async def admin_profile_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "⬅️ Повернутися до головного меню",
        reply_markup=admin_main_menu(),
    )
    await callback.answer()


@router.message(F.text == "👨‍💼 Менеджери", AdminFilter())
async def admin_managers_list_handler(message: Message):
    db = SessionLocal()
    try:
        all_managers = db.query(User).filter(User.role == UserRole.MANAGER).all()
        
        if not all_managers:
            await message.answer(
                "👨‍💼 Менеджери\n\nМенеджерів не знайдено.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_managers_back")],
                ])
            )
        else:
            await message.answer(
                "👨‍💼 Менеджери",
                reply_markup=build_managers_list_keyboard(all_managers, page=0),
            )
    finally:
        db.close()


@router.callback_query(F.data == "admin_managers_back", AdminFilter())
async def admin_managers_back(callback: CallbackQuery):
    await callback.message.answer(
        "👥 Користувачі",
        reply_markup=admin_users_menu(),
    )
    await callback.answer()


@router.message(F.text == "➕ Створити кур'єра", AdminFilter())
async def start_admin_courier_creation(message: Message, state: FSMContext):
    await state.set_state(AdminCourierState.waiting_for_full_name)
    await message.answer("✍️ Введіть ПІБ кур'єра:")


@router.message(F.text == "➕ Створити менеджера", AdminFilter())
async def start_admin_manager_creation(message: Message, state: FSMContext):
    await state.set_state(AdminManagerState.waiting_for_full_name)
    await message.answer("✍️ Введіть ПІБ менеджера:")


@router.message(F.text == "⬅️ Назад", AdminFilter())
async def back_to_admin_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "⬅️ Повернутося до головного меню",
        reply_markup=admin_main_menu(),
    )


@router.message(AdminCourierState.waiting_for_full_name, AdminFilter())
async def admin_full_name_handler(message: Message, state: FSMContext):
    db = SessionLocal()
    try:
        full_name = message.text
        await state.update_data(full_name=full_name)

        courier = UserService.create(
            db=db,
            user=UserCreate(
                full_name=full_name,
                role=UserRole.COURIER,
                store_id=None,
            ),
        )

        await state.clear()
        await message.answer(
            "✅ Кур'єра успішно створено.\n\n"
            f"👤 {courier.full_name}\n\n"
            "🔑 Код активації:\n"
            f"{courier.activation_code}\n\n"
            "⏳ Код дійсний 24 години.\n\n"
            "📲 Передайте цей код кур'єру для активації в Telegram.",
            reply_markup=admin_users_menu(),
        )
    except Exception as exc:
        logger.exception("Failed to create courier")
        await state.clear()
        await message.answer(
            "❌ Не вдалося створити кур'єра.\n\n"
            "Спробуйте ще раз.",
            reply_markup=admin_main_menu(),
        )
    finally:
        db.close()


@router.message(AdminManagerState.waiting_for_full_name, AdminFilter())
async def admin_manager_full_name_handler(message: Message, state: FSMContext):
    full_name = message.text
    await state.update_data(full_name=full_name)
    await state.set_state(AdminManagerState.waiting_for_network)
    await message.answer(
        "🌐 Оберіть мережу магазину:",
        reply_markup=build_manager_network_keyboard(),
    )


@router.callback_query(F.data.startswith("admin_manager_network:"), AdminFilter())
async def admin_manager_select_network(callback: CallbackQuery, state: FSMContext):
    network_key = callback.data.split(":", 1)[1]
    network_config = NETWORKS.get(network_key)

    if network_config is None:
        await callback.answer("❌ Некоректна мережа", show_alert=True)
        return

    await state.update_data(selected_network=network_key)
    await state.set_state(AdminManagerState.waiting_for_store_query)
    await callback.message.edit_text(
        f"🔎 Введіть текст для пошуку магазину в мережі {network_config['label']}"
    )
    await callback.answer()


@router.message(AdminManagerState.waiting_for_store_query, AdminFilter())
async def admin_manager_store_query_handler(message: Message, state: FSMContext):
    db = SessionLocal()
    try:
        data = await state.get_data()
        network_key = data.get("selected_network")
        network_config = NETWORKS.get(network_key)

        if network_config is None:
            await state.clear()
            await message.answer("❌ Спочатку оберіть мережу.", reply_markup=admin_main_menu())
            return

        query = message.text or ""
        stores = StoreService.search_stores(db, query, network_config["network"])

        if not stores:
            await message.answer("❌ Магазини не знайдено. Спробуйте ще раз.")
            return

        await state.update_data(store_candidates=[store.id for store in stores])
        await state.set_state(AdminManagerState.waiting_for_store_selection)
        await message.answer(
            "🏬 Оберіть магазин:",
            reply_markup=build_manager_store_keyboard(stores),
        )
    except Exception as exc:
        logger.exception("Failed to search stores for manager creation")
        await state.clear()
        await message.answer(
            "❌ Не вдалося знайти магазини.",
            reply_markup=admin_main_menu(),
        )
    finally:
        db.close()


@router.callback_query(F.data.startswith("admin_manager_store:"), AdminFilter())
async def admin_manager_select_store(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        store_id = int(callback.data.split(":", 1)[1])
        store = StoreService.get_store(db, store_id)
        data = await state.get_data()
        full_name = data.get("full_name")
        manager_id = data.get("manager_id")

        if full_name:
            # Create flow
            manager = UserService.create(
                db=db,
                user=UserCreate(
                    full_name=full_name,
                    role=UserRole.MANAGER,
                    store_id=store.id,
                ),
            )

            await state.clear()
            await callback.message.answer(
                "✅ Менеджера успішно створено.\n\n"
                f"👤 {manager.full_name}\n\n"
                f"🏬 Магазин:\n{store.name}\n\n"
                f"🔑 Код активації:\n{manager.activation_code}\n\n"
                "⏳ Код дійсний 24 години.\n\n"
                "📲 Передайте цей код менеджеру.",
                reply_markup=admin_users_menu(),
            )
            await callback.message.edit_text("✅ Обрано магазин. Продовжуйте в меню працівників.")
            await callback.answer()
        elif manager_id:
            # Change flow
            manager = db.get(User, manager_id)
            if not manager:
                await state.clear()
                await callback.message.answer("❌ Менеджера не знайдено.", reply_markup=admin_main_menu())
                return
            
            manager.store_id = store.id
            db.add(manager)
            db.commit()
            
            # Reload manager to ensure relationships are fresh
            manager = db.get(User, manager_id)
            
            # Get store info for display
            store_name = manager.store.name if manager.store else "Не призначен"
            network_label = ""
            if manager.store:
                if manager.store.network.value == "APPLE_ROOM":
                    network_label = "🍏 AppleRoom"
                elif manager.store.network.value == "JABKO":
                    network_label = "🍎 Ябко"
            
            profile_text = (
                f"✅ Магазин успішно змінено.\n\n"
                f"👤 {manager.full_name}\n\n"
                f"🟢 Активний\n\n"
                f"🏪 {network_label} {store_name}\n\n"
                f"📞 {'@' + manager.username if manager.username else 'Не прив\'язано'}"
            )
            
            # Keep manager_id in state to show profile again
            await callback.message.edit_text(
                profile_text,
                reply_markup=build_manager_profile_keyboard(),
            )
            await callback.answer()
        else:
            await state.clear()
            await callback.message.answer("❌ Не вдалося визначити операцію.", reply_markup=admin_main_menu())
    except Exception as exc:
        logger.exception("Failed to select store")
        await state.clear()
        await callback.message.answer(
            "❌ Не вдалося завершити операцію.\n\nСпробуйте ще раз.",
            reply_markup=admin_main_menu(),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_manager_back")
async def admin_manager_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "⬅️ Повернутося до головного меню",
        reply_markup=admin_main_menu(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_managers_page:"))
async def managers_page_handler(callback: CallbackQuery):
    db = SessionLocal()
    try:
        page = int(callback.data.split(":", 1)[1])
        all_managers = db.query(User).filter(User.role == UserRole.MANAGER).all()
        
        if not all_managers:
            await callback.message.edit_text(
                "👨‍💼 Менеджери\n\n❌ Менеджерів не знайдено.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_managers_back")],
                ])
            )
        else:
            await callback.message.edit_text(
                "👨‍💼 Менеджери",
                reply_markup=build_managers_list_keyboard(all_managers, page=page),
            )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_managers_list_back")
async def managers_list_back(callback: CallbackQuery):
    db = SessionLocal()
    try:
        all_users = db.query(User).filter(User.role == UserRole.MANAGER).all()
        activated_managers = [u for u in all_users if u.telegram_id is not None]
        non_activated_managers = [u for u in all_users if u.telegram_id is None]
        
        await callback.message.edit_text(
            f"👨‍💼 Менеджери\n\n"
            f"🟢 Активовані: {len(activated_managers)}\n"
            f"⚪ Неактивовані: {len(non_activated_managers)}",
            reply_markup=build_managers_menu_keyboard(len(activated_managers), len(non_activated_managers)),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_managers_back")
async def managers_back(callback: CallbackQuery):
    db = SessionLocal()
    try:
        all_managers = db.query(User).filter(User.role == UserRole.MANAGER).all()
        
        if not all_managers:
            await callback.message.edit_text(
                "👨‍💼 Менеджери\n\n❌ Менеджерів не знайдено.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_managers_back")],
                ])
            )
        else:
            await callback.message.edit_text(
                "👨‍💼 Менеджери",
                reply_markup=build_managers_list_keyboard(all_managers, page=0),
            )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data.startswith("admin_manager_detail:"))
async def manager_profile(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        manager_id = int(callback.data.split(":", 1)[1])
        manager = db.get(User, manager_id)
        
        # Store manager_id in state for profile actions
        await state.update_data(current_manager_id=manager_id)
        
        if not manager or manager.role != UserRole.MANAGER:
            await callback.message.edit_text(
                "❌ Менеджера не знайдено.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_managers_list_back")
                ]])
            )
            await callback.answer()
            return
        
        # Determine status
        status = "🟢 Активний" if manager.telegram_id else "⚪ Неактивний"
        
        # Get store info
        store_info = f"{manager.store.name}" if manager.store else "Не призначен"
        
        # Get telegram username
        telegram_username = f"@{manager.username}" if manager.username else "Не прив'язано"
        
        profile_text = (
            f"👤 {manager.full_name}\n\n"
            f"{status}\n\n"
            f"🏪 {store_info}\n\n"
            f"📞 {telegram_username}"
        )
        
        await callback.message.edit_text(
            profile_text,
            reply_markup=build_manager_profile_keyboard(),
        )
        await callback.answer()
    except Exception as exc:
        logger.exception("Failed to load manager profile")
        await callback.message.edit_text(
            "❌ Не вдалося завантажити профіль менеджера.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_managers_list_back")
            ]])
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_manager_profile_change_store")
async def manager_profile_change_store(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    manager_id = data.get("current_manager_id")
    
    if not manager_id:
        await callback.message.answer("❌ Не вдалося визначити менеджера.")
        await callback.answer()
        return
    
    # Save manager_id for the store selection handler
    await state.update_data(manager_id=manager_id)
    # Set state to start the network selection
    await state.set_state(AdminManagerState.waiting_for_network)
    
    await callback.message.edit_text(
        "🌐 Оберіть нову мережу магазину:",
        reply_markup=build_manager_network_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_manager_profile_repair_telegram")
async def manager_profile_repair_telegram(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        data = await state.get_data()
        manager_id = data.get("current_manager_id")
        
        if not manager_id:
            await callback.message.answer("❌ Не вдалося визначити менеджера.")
            await callback.answer()
            return
        
        manager = db.get(User, manager_id)
        if not manager:
            await callback.message.answer("❌ Менеджера не знайдено.")
            await callback.answer()
            return
        
        # Clear telegram fields
        manager.telegram_id = None
        manager.username = None
        
        # Generate new activation code and set expiration
        ActivationService.assign_activation_code(db, manager)
        
        # Format expiration date
        expiration_date = manager.activation_code_expires_at.strftime("%d.%m.%Y %H:%M") if manager.activation_code_expires_at else "—"
        
        confirmation_text = (
            f"✅ Telegram успішно відв'язано.\n\n"
            f"Новий код:\n{manager.activation_code}\n\n"
            f"Дійсний до:\n{expiration_date}"
        )
        
        await callback.message.answer(confirmation_text)
        await callback.answer()
        
        # Update profile in state and show it
        await state.update_data(current_manager_id=manager_id)
        
        # Determine status
        status = "🟢 Активний" if manager.telegram_id else "⚪ Неактивний"
        
        # Get store info
        store_info = f"{manager.store.name}" if manager.store else "Не призначен"
        
        # Get telegram username
        telegram_username = f"@{manager.username}" if manager.username else "Не прив'язано"
        
        profile_text = (
            f"👤 {manager.full_name}\n\n"
            f"{status}\n\n"
            f"🏪 {store_info}\n\n"
            f"📞 {telegram_username}"
        )
        
        await callback.message.edit_text(
            profile_text,
            reply_markup=build_manager_profile_keyboard(),
        )
    except Exception as exc:
        logger.exception("Failed to repair manager telegram")
        await callback.message.answer(
            "❌ Не вдалося переприв'язати Telegram.\n\nСпробуйте ще раз.",
            reply_markup=admin_main_menu(),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_manager_profile_deactivate")
async def manager_profile_deactivate(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    manager_id = data.get("current_manager_id")
    
    if not manager_id:
        await callback.message.answer("❌ Не вдалося визначити менеджера.")
        await callback.answer()
        return
    
    # Show confirmation
    confirmation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Підтвердити",
                callback_data=f"admin_manager_deactivate_confirm:{manager_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Скасувати",
                callback_data="admin_manager_profile_back",
            )
        ],
    ])
    
    await callback.message.edit_text(
        "⚠️ Ви впевнені?\n\n"
        "Деактивований менеджер не зможе увійти в бот.",
        reply_markup=confirmation_keyboard,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_manager_deactivate_confirm:"))
async def manager_deactivate_confirm(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        manager_id = int(callback.data.split(":", 1)[1])
        manager = db.get(User, manager_id)
        
        if not manager:
            await callback.message.answer("❌ Менеджера не знайдено.")
            await callback.answer()
            return
        
        # Deactivate manager
        manager.status = UserStatus.INACTIVE
        db.add(manager)
        db.commit()
        
        # Reload manager
        manager = db.get(User, manager_id)
        
        # Show confirmation
        await callback.message.answer("✅ Менеджер успішно деактивовано.")
        await callback.answer()
        
        # Update profile in state and show it
        await state.update_data(current_manager_id=manager_id)
        
        # Determine status
        status = "🟢 Активний" if manager.telegram_id else "⚪ Неактивний"
        
        # Get store info
        store_info = f"{manager.store.name}" if manager.store else "Не призначен"
        
        # Get telegram username
        telegram_username = f"@{manager.username}" if manager.username else "Не прив'язано"
        
        profile_text = (
            f"👤 {manager.full_name}\n\n"
            f"{status}\n\n"
            f"🏪 {store_info}\n\n"
            f"📞 {telegram_username}"
        )
        
        await callback.message.edit_text(
            profile_text,
            reply_markup=build_manager_profile_keyboard(),
        )
    except Exception as exc:
        logger.exception("Failed to deactivate manager")
        await callback.message.answer(
            "❌ Не вдалося деактивувати менеджера.\n\nСпробуйте ще раз.",
            reply_markup=admin_main_menu(),
        )
        await callback.answer()
    finally:
        db.close()


@router.message(F.text == "🚴 Кур'єри")
async def admin_couriers_handler(message: Message):
    db = SessionLocal()
    try:
        all_couriers = db.query(User).filter(User.role == UserRole.COURIER).all()
        
        if not all_couriers:
            await message.answer(
                "🚴 Кур'єри\n\n❌ Кур'єрів не знайдено.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_couriers_menu_back")],
                ])
            )
        else:
            await message.answer(
                "🚴 Кур'єри",
                reply_markup=build_couriers_list_keyboard(all_couriers, page=0),
            )
    finally:
        db.close()


@router.callback_query(F.data.startswith("admin_couriers_page:"))
async def couriers_page_handler(callback: CallbackQuery):
    db = SessionLocal()
    try:
        page = int(callback.data.split(":", 1)[1])
        all_couriers = db.query(User).filter(User.role == UserRole.COURIER).all()
        
        await callback.message.edit_text(
            "🚴 Кур'єри",
            reply_markup=build_couriers_list_keyboard(all_couriers, page=page),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data.startswith("admin_courier_profile:"))
async def courier_profile(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        courier_id = int(callback.data.split(":", 1)[1])
        courier = db.get(User, courier_id)
        
        if not courier:
            await callback.message.answer("❌ Кур'єра не знайдено.")
            await callback.answer()
            return
        
        # Store courier_id in state for profile actions
        await state.update_data(current_courier_id=courier_id)
        
        # Determine status
        status_map = {
            CourierAvailability.AVAILABLE: "🟢 На зміні",
            CourierAvailability.BUSY: "🟡 Виконує доставку",
            CourierAvailability.OFFLINE: "⚫ Поза зміною",
        }
        status = status_map.get(courier.availability, "—")
        
        # Get telegram username
        telegram_username = f"@{courier.username}" if courier.username else "Не прив'язано"
        
        profile_text = (
            f"👤 {courier.full_name}\n\n"
            f"{status}\n\n"
            f"📱 {telegram_username}"
        )
        
        # If BUSY, show current order
        if courier.availability == CourierAvailability.BUSY:
            delivering_order = db.query(Order).filter(
                Order.courier_id == courier_id,
                Order.status == OrderStatus.DELIVERING
            ).first()
            
            if delivering_order:
                profile_text += f"\n\n📦 №{delivering_order.number}"
        
        # Build profile keyboard
        buttons = [
            [InlineKeyboardButton(text="🔑 Переприв'язати Telegram", callback_data="admin_courier_profile_repair_telegram")],
            [InlineKeyboardButton(text="🚫 Деактивувати", callback_data="admin_courier_profile_deactivate")],
            [InlineKeyboardButton(text="🗑 Видалити", callback_data="admin_courier_profile_delete")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_courier_profile_back")],
        ]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.edit_text(profile_text, reply_markup=keyboard)
        await callback.answer()
    except Exception as exc:
        logger.exception("Failed to show courier profile")
        await callback.message.answer("❌ Не вдалося завантажити профіль.")
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_courier_profile_repair_telegram")
async def courier_profile_repair_telegram(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        data = await state.get_data()
        courier_id = data.get("current_courier_id")
        
        if not courier_id:
            await callback.message.answer("❌ Не вдалося визначити кур'єра.")
            await callback.answer()
            return
        
        courier = db.get(User, courier_id)
        if not courier:
            await callback.message.answer("❌ Кур'єра не знайдено.")
            await callback.answer()
            return
        
        # Clear telegram fields
        courier.telegram_id = None
        courier.username = None
        
        # Generate new activation code and set expiration
        ActivationService.assign_activation_code(db, courier)
        
        # Format expiration date
        expiration_date = courier.activation_code_expires_at.strftime("%d.%m.%Y %H:%M") if courier.activation_code_expires_at else "—"
        
        confirmation_text = (
            f"✅ Telegram успішно відв'язано.\n\n"
            f"Новий код:\n{courier.activation_code}\n\n"
            f"Дійсний до:\n{expiration_date}"
        )
        
        await callback.message.answer(confirmation_text)
        await callback.answer()
        
        # Return to profile
        await state.update_data(current_courier_id=courier_id)
        
        # Determine status
        status_map = {
            CourierAvailability.AVAILABLE: "🟢 На зміні",
            CourierAvailability.BUSY: "🟡 Виконує доставку",
            CourierAvailability.OFFLINE: "⚫ Поза зміною",
        }
        status = status_map.get(courier.availability, "—")
        
        # Get telegram username
        telegram_username = f"@{courier.username}" if courier.username else "Не прив'язано"
        
        profile_text = (
            f"👤 {courier.full_name}\n\n"
            f"{status}\n\n"
            f"📱 {telegram_username}"
        )
        
        # If BUSY, show current order
        if courier.availability == CourierAvailability.BUSY:
            delivering_order = db.query(Order).filter(
                Order.courier_id == courier_id,
                Order.status == OrderStatus.DELIVERING
            ).first()
            
            if delivering_order:
                profile_text += f"\n\n📦 №{delivering_order.number}"
        
        # Build profile keyboard
        buttons = [
            [InlineKeyboardButton(text="🔑 Переприв'язати Telegram", callback_data="admin_courier_profile_repair_telegram")],
            [InlineKeyboardButton(text="🚫 Деактивувати", callback_data="admin_courier_profile_deactivate")],
            [InlineKeyboardButton(text="🗑 Видалити", callback_data="admin_courier_profile_delete")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_courier_profile_back")],
        ]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.edit_text(profile_text, reply_markup=keyboard)
    except Exception as exc:
        logger.exception("Failed to repair courier telegram")
        await callback.message.answer("❌ Не вдалося виконати операцію.")
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_courier_profile_deactivate")
async def courier_profile_deactivate(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    courier_id = data.get("current_courier_id")
    
    if not courier_id:
        await callback.message.answer("❌ Не вдалося визначити кур'єра.")
        await callback.answer()
        return
    
    # Show confirmation
    confirmation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Підтвердити",
                callback_data=f"admin_courier_deactivate_confirm:{courier_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Скасувати",
                callback_data="admin_courier_profile_back",
            )
        ],
    ])
    
    await callback.message.edit_text(
        "⚠️ Ви впевнені?\n\n"
        "Деактивований кур'єр не зможе увійти в бот.",
        reply_markup=confirmation_keyboard,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_courier_deactivate_confirm:"))
async def courier_deactivate_confirm(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        courier_id = int(callback.data.split(":", 1)[1])
        courier = db.get(User, courier_id)
        
        if not courier:
            await callback.message.answer("❌ Кур'єра не знайдено.")
            await callback.answer()
            return
        
        # Deactivate courier
        courier.status = UserStatus.INACTIVE
        db.add(courier)
        db.commit()
        
        # Reload courier
        courier = db.get(User, courier_id)
        
        # Show confirmation
        await callback.message.answer("✅ Кур'єр успішно деактивовано.")
        await callback.answer()
        
        # Return to profile
        await state.update_data(current_courier_id=courier_id)
        
        # Determine status
        status_map = {
            CourierAvailability.AVAILABLE: "🟢 На зміні",
            CourierAvailability.BUSY: "🟡 Виконує доставку",
            CourierAvailability.OFFLINE: "⚫ Поза зміною",
        }
        status = status_map.get(courier.availability, "—")
        
        # Get telegram username
        telegram_username = f"@{courier.username}" if courier.username else "Не прив'язано"
        
        profile_text = (
            f"👤 {courier.full_name}\n\n"
            f"{status}\n\n"
            f"📱 {telegram_username}"
        )
        
        # If BUSY, show current order
        if courier.availability == CourierAvailability.BUSY:
            delivering_order = db.query(Order).filter(
                Order.courier_id == courier_id,
                Order.status == OrderStatus.DELIVERING
            ).first()
            
            if delivering_order:
                profile_text += f"\n\n📦 №{delivering_order.number}"
        
        # Build profile keyboard
        buttons = [
            [InlineKeyboardButton(text="🔑 Переприв'язати Telegram", callback_data="admin_courier_profile_repair_telegram")],
            [InlineKeyboardButton(text="🚫 Деактивувати", callback_data="admin_courier_profile_deactivate")],
            [InlineKeyboardButton(text="🗑 Видалити", callback_data="admin_courier_profile_delete")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_courier_profile_back")],
        ]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.edit_text(profile_text, reply_markup=keyboard)
    except Exception as exc:
        logger.exception("Failed to deactivate courier")
        await callback.message.answer("❌ Не вдалося деактивувати кур'єра.")
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_courier_profile_delete")
async def courier_profile_delete(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        data = await state.get_data()
        courier_id = data.get("current_courier_id")
        
        if not courier_id:
            await callback.message.answer("❌ Не вдалося визначити кур'єра.")
            await callback.answer()
            return
        
        courier = db.get(User, courier_id)
        if not courier:
            await callback.message.answer("❌ Кур'єра не знайдено.")
            await callback.answer()
            return
        
        # Check for active orders
        active_statuses = [
            OrderStatus.WAITING_FOR_COURIER,
            OrderStatus.ACCEPTED,
            OrderStatus.PICKED_UP,
            OrderStatus.DELIVERING,
        ]
        active_orders = db.query(Order).filter(
            Order.courier_id == courier_id,
            Order.status.in_(active_statuses)
        ).all()
        
        # Show error if any active orders exist
        if active_orders:
            error_message = (
                f"❌ Неможливо видалити кур'єра.\n\n"
                f"🔴 Активних замовлень: {len(active_orders)}\n\n"
                f"Спочатку завершіть всі замовлення."
            )
            
            await callback.message.answer(error_message)
            await callback.answer()
            return
        
        # Show confirmation if no active orders
        confirmation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Видалити",
                    callback_data=f"admin_courier_delete_confirm:{courier_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Скасувати",
                    callback_data="admin_courier_profile_back",
                )
            ],
        ])
        
        await callback.message.edit_text(
            "⚠️ Ви впевнені?\n\n"
            "Кур'єр буде видалено безповоротно.",
            reply_markup=confirmation_keyboard,
        )
        await callback.answer()
    except Exception as exc:
        logger.exception("Failed to check courier for deletion")
        await callback.message.answer("❌ Не вдалося перевірити можливість видалення.")
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data.startswith("admin_courier_delete_confirm:"))
async def courier_delete_confirm(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        courier_id = int(callback.data.split(":", 1)[1])
        courier = db.get(User, courier_id)
        
        if not courier:
            await callback.message.answer("❌ Кур'єра не знайдено.")
            await callback.answer()
            return
        
        # Delete courier
        db.delete(courier)
        db.commit()
        
        # Show confirmation
        await callback.message.answer("✅ Кур'єр успішно видалено.")
        await callback.answer()
        
        # Return to couriers menu
        await callback.message.answer(
            "🚴 Кур'єри",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🟢 На зміні", callback_data="admin_show_available_couriers")],
                [InlineKeyboardButton(text="🟡 Виконують доставку", callback_data="admin_show_busy_couriers")],
                [InlineKeyboardButton(text="⚫ Поза зміною", callback_data="admin_show_offline_couriers")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_couriers_menu_back")],
            ]),
        )
    except Exception as exc:
        logger.exception("Failed to delete courier")
        await callback.message.answer("❌ Не вдалося видалити кур'єра.")
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_courier_profile_back")
async def courier_profile_back(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        data = await state.get_data()
        courier_id = data.get("current_courier_id")
        
        if not courier_id:
            await callback.message.answer("❌ Не вдалося визначити кур'єра.")
            await callback.answer()
            return
        
        courier = db.get(User, courier_id)
        if not courier:
            await callback.message.answer("❌ Кур'єра не знайдено.")
            await callback.answer()
            return
        
        # Determine status
        status_map = {
            CourierAvailability.AVAILABLE: "🟢 На зміні",
            CourierAvailability.BUSY: "🟡 Виконує доставку",
            CourierAvailability.OFFLINE: "⚫ Поза зміною",
        }
        status = status_map.get(courier.availability, "—")
        
        # Get telegram username
        telegram_username = f"@{courier.username}" if courier.username else "Не прив'язано"
        
        profile_text = (
            f"👤 {courier.full_name}\n\n"
            f"{status}\n\n"
            f"📱 {telegram_username}"
        )
        
        # If BUSY, show current order
        if courier.availability == CourierAvailability.BUSY:
            delivering_order = db.query(Order).filter(
                Order.courier_id == courier_id,
                Order.status == OrderStatus.DELIVERING
            ).first()
            
            if delivering_order:
                profile_text += f"\n\n📦 №{delivering_order.number}"
        
        # Build profile keyboard
        buttons = [
            [InlineKeyboardButton(text="🔑 Переприв'язати Telegram", callback_data="admin_courier_profile_repair_telegram")],
            [InlineKeyboardButton(text="🚫 Деактивувати", callback_data="admin_courier_profile_deactivate")],
            [InlineKeyboardButton(text="🗑 Видалити", callback_data="admin_courier_profile_delete")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_courier_profile_back")],
        ]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.edit_text(profile_text, reply_markup=keyboard)
        await callback.answer()
    except Exception as exc:
        logger.exception("Failed to return to courier profile")
        await callback.message.answer("❌ Не вдалося повернутися до профіля.")
        await callback.answer()
    finally:
        db.close()



@router.callback_query(F.data == "admin_couriers_back")
async def couriers_list_back(callback: CallbackQuery):
    db = SessionLocal()
    try:
        all_couriers = db.query(User).filter(User.role == UserRole.COURIER).all()
        
        if not all_couriers:
            await callback.message.edit_text(
                "🚴 Кур'єри\n\n❌ Кур'єрів не знайдено.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_couriers_menu_back")],
                ])
            )
        else:
            await callback.message.edit_text(
                "🚴 Кур'єри",
                reply_markup=build_couriers_list_keyboard(all_couriers, page=0),
            )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_couriers_menu_back")
async def admin_couriers_menu_back(callback: CallbackQuery):
    await callback.message.answer(
        "👥 Користувачі",
        reply_markup=admin_users_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_stats_today")
async def admin_stats_today(callback: CallbackQuery):
    db = SessionLocal()
    try:
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        # Get orders created today
        today_orders = db.query(Order).filter(
            Order.created_at >= datetime.combine(today, datetime.min.time()),
            Order.created_at < datetime.combine(tomorrow, datetime.min.time())
        ).all()
        
        # Count orders by status
        created_count = len(today_orders)
        waiting_count = len([o for o in today_orders if o.status == OrderStatus.WAITING_FOR_COURIER])
        in_progress_count = len([
            o for o in today_orders 
            if o.status in (OrderStatus.ACCEPTED, OrderStatus.PICKED_UP, OrderStatus.DELIVERING)
        ])
        delivered_count = len([o for o in today_orders if o.status == OrderStatus.DELIVERED])
        canceled_count = len([o for o in today_orders if o.status == OrderStatus.CANCELED])
        
        # Get courier statistics
        all_couriers = db.query(User).filter(User.role == UserRole.COURIER).all()
        on_shift_count = len([c for c in all_couriers if c.availability in (CourierAvailability.AVAILABLE, CourierAvailability.BUSY)])
        available_count = len([c for c in all_couriers if c.availability == CourierAvailability.AVAILABLE])
        busy_count = len([c for c in all_couriers if c.availability == CourierAvailability.BUSY])
        
        stats_text = (
            f"📅 Сьогодні\n\n"
            f"📦 Створено заявок: {created_count}\n"
            f"🟡 Очікують кур'єра: {waiting_count}\n"
            f"🚚 В роботі: {in_progress_count}\n"
            f"✅ Доставлено: {delivered_count}\n"
            f"❌ Скасовано: {canceled_count}\n\n"
            f"🚴 Кур'єрів на зміні: {on_shift_count}\n"
            f"🟢 Вільних кур'єрів: {available_count}\n"
            f"🟡 Кур'єрів на доставці: {busy_count}"
        )
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=build_statistics_menu_keyboard(),
        )
        await callback.answer()
    except Exception as exc:
        logger.exception("Failed to load today statistics")
        await callback.message.answer(
            "❌ Не вдалося завантажити статистику.",
            reply_markup=build_statistics_menu_keyboard(),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data.startswith("admin_stats_month"))
async def admin_stats_month(callback: CallbackQuery):
    db = SessionLocal()
    try:
        # Parse month_offset from callback data
        callback_data = callback.data
        if ":" in callback_data:
            month_offset = int(callback_data.split(":")[1])
        else:
            month_offset = 0
        
        today = date.today()
        current_year = today.year
        current_month = today.month
        
        # Calculate target month based on offset
        target_month = current_month + month_offset
        target_year = current_year
        
        # Adjust year if needed
        while target_month > 12:
            target_month -= 12
            target_year += 1
        while target_month < 1:
            target_month += 12
            target_year -= 1
        
        # Don't allow future months
        if target_year > current_year or (target_year == current_year and target_month > current_month):
            month_offset = 0
            target_year = current_year
            target_month = current_month
        
        # First day of target month
        month_start = date(target_year, target_month, 1)
        
        # First day of next month
        if target_month == 12:
            month_end = date(target_year + 1, 1, 1)
        else:
            month_end = date(target_year, target_month + 1, 1)
        
        # Get orders created this month
        month_orders = db.query(Order).filter(
            Order.created_at >= datetime.combine(month_start, datetime.min.time()),
            Order.created_at < datetime.combine(month_end, datetime.min.time())
        ).all()
        
        # Count orders by status
        created_count = len(month_orders)
        delivered_count = len([o for o in month_orders if o.status == OrderStatus.DELIVERED])
        canceled_count = len([o for o in month_orders if o.status == OrderStatus.CANCELED])
        in_progress_count = len([
            o for o in month_orders 
            if o.status in (OrderStatus.ACCEPTED, OrderStatus.PICKED_UP, OrderStatus.DELIVERING)
        ])
        
        # Find most active store
        most_active_store = "—"
        if month_orders:
            store_order_counts = {}
            for order in month_orders:
                if order.from_store_id:
                    store_order_counts[order.from_store_id] = store_order_counts.get(order.from_store_id, 0) + 1
            if store_order_counts:
                most_active_store_id = max(store_order_counts, key=store_order_counts.get)
                store = db.get(Store, most_active_store_id)
                if store:
                    most_active_store = store.name
        
        # Find best courier (most deliveries this month)
        best_courier = "—"
        delivered_orders = [o for o in month_orders if o.status == OrderStatus.DELIVERED]
        if delivered_orders:
            courier_delivery_counts = {}
            for order in delivered_orders:
                if order.courier_id:
                    courier_delivery_counts[order.courier_id] = courier_delivery_counts.get(order.courier_id, 0) + 1
            if courier_delivery_counts:
                best_courier_id = max(courier_delivery_counts, key=courier_delivery_counts.get)
                courier = db.get(User, best_courier_id)
                if courier:
                    best_courier = courier.full_name
        
        # Top 5 couriers by delivered orders
        top_couriers_text = ""
        if delivered_orders:
            courier_delivery_counts = {}
            for order in delivered_orders:
                if order.courier_id:
                    courier_delivery_counts[order.courier_id] = courier_delivery_counts.get(order.courier_id, 0) + 1
            
            # Sort by delivery count descending
            sorted_couriers = sorted(courier_delivery_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            medals = ["🥇", "🥈", "🥉", "4.", "5."]
            top_couriers_text = "\n🚴 Топ кур'єрів:\n"
            for idx, (courier_id, count) in enumerate(sorted_couriers):
                courier = db.get(User, courier_id)
                if courier:
                    top_couriers_text += f"{medals[idx]} {courier.full_name} - {count} доставок\n"
        
        # Top 5 stores by created orders
        top_stores_text = ""
        if month_orders:
            store_order_counts = {}
            for order in month_orders:
                if order.from_store_id:
                    store_order_counts[order.from_store_id] = store_order_counts.get(order.from_store_id, 0) + 1
            
            # Sort by order count descending
            sorted_stores = sorted(store_order_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            medals = ["🥇", "🥈", "🥉", "4.", "5."]
            top_stores_text = "\n🏪 Топ магазинів:\n"
            for idx, (store_id, count) in enumerate(sorted_stores):
                store = db.get(Store, store_id)
                if store:
                    top_stores_text += f"{medals[idx]} {store.name} - {count} заявок\n"
        
        # Format month display
        months_uk = {
            1: "Січень", 2: "Лютий", 3: "Березень", 4: "Квітень",
            5: "Травень", 6: "Червень", 7: "Липень", 8: "Серпень",
            9: "Вересень", 10: "Жовтень", 11: "Листопад", 12: "Грудень"
        }
        month_display = f"{months_uk[target_month]} {target_year}"
        
        stats_text = (
            f"📆 {month_display}\n\n"
            f"📦 Створено заявок: {created_count}\n"
            f"✅ Доставлено: {delivered_count}\n"
            f"❌ Скасовано: {canceled_count}\n"
            f"🟡 Ще в роботі: {in_progress_count}\n\n"
            f"🏪 Найактивніший магазин: {most_active_store}\n"
            f"🚴 Найкращий кур'єр: {best_courier}"
            f"{top_couriers_text}"
            f"{top_stores_text}"
        )
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=build_month_statistics_menu_keyboard(month_offset),
        )
        await callback.answer()
    except Exception as exc:
        logger.exception("Failed to load month statistics")
        await callback.message.answer(
            "❌ Не вдалося завантажити статистику.",
            reply_markup=build_statistics_menu_keyboard(),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_stats_all_time")
async def admin_stats_all_time(callback: CallbackQuery):
    db = SessionLocal()
    try:
        # Get all orders
        all_orders = db.query(Order).all()
        
        # Count orders by status
        created_count = len(all_orders)
        delivered_count = len([o for o in all_orders if o.status == OrderStatus.DELIVERED])
        canceled_count = len([o for o in all_orders if o.status == OrderStatus.CANCELED])
        
        # Find most active store (all time)
        most_active_store = "—"
        if all_orders:
            store_order_counts = {}
            for order in all_orders:
                if order.from_store_id:
                    store_order_counts[order.from_store_id] = store_order_counts.get(order.from_store_id, 0) + 1
            if store_order_counts:
                most_active_store_id = max(store_order_counts, key=store_order_counts.get)
                store = db.get(Store, most_active_store_id)
                if store:
                    most_active_store = store.name
        
        # Find best courier (most deliveries all time)
        best_courier = "—"
        delivered_orders = [o for o in all_orders if o.status == OrderStatus.DELIVERED]
        if delivered_orders:
            courier_delivery_counts = {}
            for order in delivered_orders:
                if order.courier_id:
                    courier_delivery_counts[order.courier_id] = courier_delivery_counts.get(order.courier_id, 0) + 1
            if courier_delivery_counts:
                best_courier_id = max(courier_delivery_counts, key=courier_delivery_counts.get)
                courier = db.get(User, best_courier_id)
                if courier:
                    best_courier = courier.full_name
        
        # Count managers and couriers
        managers_count = db.query(User).filter(User.role == UserRole.MANAGER).count()
        couriers_count = db.query(User).filter(User.role == UserRole.COURIER).count()
        
        stats_text = (
            f"📈 За весь час\n\n"
            f"📦 Всього заявок: {created_count}\n"
            f"✅ Всього доставлено: {delivered_count}\n"
            f"❌ Всього скасовано: {canceled_count}\n\n"
            f"🏪 Найактивніший магазин: {most_active_store}\n"
            f"🚴 Найкращий кур'єр: {best_courier}\n\n"
            f"👨‍💼 Всього менеджерів: {managers_count}\n"
            f"🚴 Всього кур'єрів: {couriers_count}"
        )
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=build_statistics_menu_keyboard(),
        )
        await callback.answer()
    except Exception as exc:
        logger.exception("Failed to load all-time statistics")
        await callback.message.answer(
            "❌ Не вдалося завантажити статистику.",
            reply_markup=build_statistics_menu_keyboard(),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_stats_back")
async def admin_stats_back(callback: CallbackQuery):
    await callback.message.answer(
        "⬅️ Повернутося до головного меню",
        reply_markup=admin_main_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_orders_waiting")
async def admin_orders_waiting(callback: CallbackQuery):
    db = SessionLocal()
    try:
        # Get all waiting orders, sorted by created_at (oldest first)
        waiting_orders = db.query(Order).filter(
            Order.status == OrderStatus.WAITING_FOR_COURIER
        ).order_by(Order.created_at).all()
        
        if not waiting_orders:
            await callback.message.answer(
                "🟡 Очікують кур'єра\n\nЗаявок не знайдено.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")],
                ])
            )
            await callback.answer()
            return
        
        # Build keyboard with pagination
        page = 0
        page_size = 10
        total_pages = (len(waiting_orders) + page_size - 1) // page_size
        start_idx = page * page_size
        end_idx = start_idx + page_size
        page_orders = waiting_orders[start_idx:end_idx]
        
        # Priority emoji mapping
        priority_map = {
            OrderPriority.LOW: "🟢",
            OrderPriority.NORMAL: "🟡",
            OrderPriority.HIGH: "🔴",
            OrderPriority.URGENT: "⭐",
        }
        
        buttons = []
        for order in page_orders:
            from_store = db.get(Store, order.from_store_id)
            to_store = db.get(Store, order.to_store_id)
            from_name = from_store.name if from_store else "—"
            to_name = to_store.name if to_store else "—"
            time_str = order.created_at.strftime("%H:%M") if order.created_at else "—"
            priority_emoji = priority_map.get(order.priority, "🟡")
            
            order_text = f"{priority_emoji} №{order.number}\n{from_name}\n↓\n{to_name}\n{time_str}"
            
            buttons.append([
                InlineKeyboardButton(
                    text=order_text,
                    callback_data=f"admin_order_detail:{order.id}",
                )
            ])
        
        # Add pagination buttons
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(text="◀️ Попередня", callback_data=f"admin_orders_waiting_page:{page-1}")
            )
        pagination_buttons.append(
            InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="admin_orders_waiting_info")
        )
        if page < total_pages - 1:
            pagination_buttons.append(
                InlineKeyboardButton(text="Наступна ▶️", callback_data=f"admin_orders_waiting_page:{page+1}")
            )
        
        if pagination_buttons:
            buttons.append(pagination_buttons)
        
        buttons.append([
            InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")
        ])
        
        await callback.message.answer(
            "🟡 Очікують кур'єра",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data.startswith("admin_orders_waiting_page:"))
async def admin_orders_waiting_page(callback: CallbackQuery):
    db = SessionLocal()
    try:
        page = int(callback.data.split(":")[1])
        
        # Get all waiting orders, sorted by created_at (oldest first)
        waiting_orders = db.query(Order).filter(
            Order.status == OrderStatus.WAITING_FOR_COURIER
        ).order_by(Order.created_at).all()
        
        if not waiting_orders:
            await callback.message.edit_text(
                "🟡 Очікують кур'єра\n\nЗаявок не знайдено.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")],
                ])
            )
            await callback.answer()
            return
        
        # Build keyboard with pagination
        page_size = 10
        total_pages = (len(waiting_orders) + page_size - 1) // page_size
        
        # Ensure page is valid
        if page < 0 or page >= total_pages:
            page = 0
        
        start_idx = page * page_size
        end_idx = start_idx + page_size
        page_orders = waiting_orders[start_idx:end_idx]
        
        # Priority emoji mapping
        priority_map = {
            OrderPriority.LOW: "🟢",
            OrderPriority.NORMAL: "🟡",
            OrderPriority.HIGH: "🔴",
            OrderPriority.URGENT: "⭐",
        }
        
        buttons = []
        for order in page_orders:
            from_store = db.get(Store, order.from_store_id)
            to_store = db.get(Store, order.to_store_id)
            from_name = from_store.name if from_store else "—"
            to_name = to_store.name if to_store else "—"
            time_str = order.created_at.strftime("%H:%M") if order.created_at else "—"
            priority_emoji = priority_map.get(order.priority, "🟡")
            
            order_text = f"{priority_emoji} №{order.number}\n{from_name}\n↓\n{to_name}\n{time_str}"
            
            buttons.append([
                InlineKeyboardButton(
                    text=order_text,
                    callback_data=f"admin_order_detail:{order.id}",
                )
            ])
        
        # Add pagination buttons
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(text="◀️ Попередня", callback_data=f"admin_orders_waiting_page:{page-1}")
            )
        pagination_buttons.append(
            InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="admin_orders_waiting_info")
        )
        if page < total_pages - 1:
            pagination_buttons.append(
                InlineKeyboardButton(text="Наступна ▶️", callback_data=f"admin_orders_waiting_page:{page+1}")
            )
        
        if pagination_buttons:
            buttons.append(pagination_buttons)
        
        buttons.append([
            InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")
        ])
        
        await callback.message.edit_text(
            "🟡 Очікують кур'єра",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_orders_waiting_info")
async def admin_orders_waiting_info(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("admin_order_detail:"))
async def admin_order_detail(callback: CallbackQuery):
    db = SessionLocal()
    try:
        order_id = int(callback.data.split(":")[1])
        order = db.get(Order, order_id)
        
        if not order:
            await callback.message.answer(
                "❌ Заявку не знайдено.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")],
                ])
            )
            await callback.answer()
            return
        
        # Get related objects
        from_store = db.get(Store, order.from_store_id)
        to_store = db.get(Store, order.to_store_id)
        manager = db.get(User, order.created_by)
        courier = db.get(User, order.courier_id) if order.courier_id else None
        
        # Format status
        status_map = {
            OrderStatus.WAITING_FOR_COURIER: "🟡 Очікує кур'єра",
            OrderStatus.ACCEPTED: "✅ Прийнято",
            OrderStatus.PICKED_UP: "📦 Забрано",
            OrderStatus.DELIVERING: "🚚 Доставляється",
            OrderStatus.DELIVERED: "✅ Доставлено",
            OrderStatus.CANCELED: "❌ Скасовано",
        }
        status_text = status_map.get(order.status, "—")
        
        # Format priority
        priority_map = {
            OrderPriority.LOW: "🟢 Низька",
            OrderPriority.NORMAL: "🟡 Звичайна",
            OrderPriority.HIGH: "🔴 Висока",
            OrderPriority.URGENT: "⭐ Терміново",
        }
        priority_text = priority_map.get(order.priority, "🟡 Звичайна")
        
        # Format size
        size_map = {
            "SMALL": "Мала",
            "MEDIUM": "Середня",
            "LARGE": "Велика",
        }
        size_text = size_map.get(order.size, "—") if order.size else "—"
        
        # Format names
        from_name = from_store.name if from_store else "—"
        to_name = to_store.name if to_store else "—"
        manager_name = manager.full_name if manager else "—"
        courier_name = courier.full_name if courier else "—"
        
        # Format timestamps
        created_time = order.created_at.strftime("%H:%M") if order.created_at else "—"
        accepted_time = order.accepted_at.strftime("%H:%M") if order.accepted_at else "—"
        picked_up_time = order.picked_up_at.strftime("%H:%M") if order.picked_up_at else "—"
        delivered_time = order.delivered_at.strftime("%H:%M") if order.delivered_at else "—"
        
        # Build order details text
        order_details = (
            f"📦 Заявка №{order.number}\n"
            f"{status_text}\n\n"
            f"────────────\n\n"
            f"🏪 Від: {from_name}\n"
            f"🏪 До: {to_name}\n\n"
            f"👨‍💼 Менеджер: {manager_name}\n"
            f"🚴 Кур'єр: {courier_name}\n"
            f"📦 Розмір: {size_text}\n"
            f"⭐ Пріоритет: {priority_text}\n"
        )
        
        # Add comment if exists
        if order.manager_comment:
            order_details += f"\n📝 Коментар: {order.manager_comment}\n"
        
        # Add timeline
        order_details += (
            f"\n────────────\n\n"
            f"🕒 Створено: {created_time}\n"
            f"🕒 Прийнято: {accepted_time}\n"
            f"🕒 Забрано: {picked_up_time}\n"
            f"🕒 Доставляється: —\n"
            f"🕒 Доставлено: {delivered_time}"
        )
        
        # Build keyboard
        buttons = [
            [InlineKeyboardButton(text="📜 Історія", callback_data=f"admin_order_history:{order.id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")],
        ]
        
        await callback.message.answer(
            order_details,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data.startswith("admin_order_history:"))
async def admin_order_history(callback: CallbackQuery):
    db = SessionLocal()
    try:
        order_id = int(callback.data.split(":")[1])
        order = db.get(Order, order_id)
        
        if not order:
            await callback.message.answer(
                "❌ Заявку не знайдено.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")],
                ])
            )
            await callback.answer()
            return
        
        # Build timeline events from existing timestamps
        timeline_events = []
        
        if order.created_at:
            timeline_events.append({
                'time': order.created_at,
                'description': 'Менеджер створив заявку'
            })
        
        if order.accepted_at:
            timeline_events.append({
                'time': order.accepted_at,
                'description': 'Кур\'єр прийняв заявку'
            })
        
        if order.picked_up_at:
            timeline_events.append({
                'time': order.picked_up_at,
                'description': 'Кур\'єр забрав товар'
            })
        
        if order.delivered_at:
            timeline_events.append({
                'time': order.delivered_at,
                'description': 'Кур\'єр доставив товар'
            })
        
        # Sort by time (should already be in order, but ensure it)
        timeline_events.sort(key=lambda e: e['time'])
        
        # Build message
        history_text = "📜 Історія заявки\n\n"
        
        if not timeline_events:
            history_text += "Немає подій."
        else:
            for i, event in enumerate(timeline_events):
                time_str = event['time'].strftime("%H:%M")
                history_text += f"{time_str}\n\n{event['description']}"
                
                # Add separator between events (but not after last one)
                if i < len(timeline_events) - 1:
                    history_text += "\n\n────────────\n\n"
        
        await callback.message.answer(
            history_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_order_detail:{order.id}")],
            ])
        )
        await callback.answer()
    finally:
        db.close()



@router.callback_query(F.data == "admin_orders_in_progress")
async def admin_orders_in_progress(callback: CallbackQuery):
    db = SessionLocal()
    try:
        # Get all in-progress orders (ACCEPTED, PICKED_UP, DELIVERING), sorted by accepted_at (oldest first)
        in_progress_orders = db.query(Order).filter(
            Order.status.in_([OrderStatus.ACCEPTED, OrderStatus.PICKED_UP, OrderStatus.DELIVERING])
        ).order_by(Order.accepted_at).all()
        
        if not in_progress_orders:
            await callback.message.answer(
                "🚚 В роботі\n\nЗаявок не знайдено.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")],
                ])
            )
            await callback.answer()
            return
        
        # Build keyboard with pagination
        page = 0
        page_size = 10
        total_pages = (len(in_progress_orders) + page_size - 1) // page_size
        start_idx = page * page_size
        end_idx = start_idx + page_size
        page_orders = in_progress_orders[start_idx:end_idx]
        
        # Status emoji mapping
        status_map = {
            OrderStatus.ACCEPTED: "✅ Прийнято",
            OrderStatus.PICKED_UP: "📦 Забрано",
            OrderStatus.DELIVERING: "🚚 Доставляється",
        }
        
        buttons = []
        for order in page_orders:
            from_store = db.get(Store, order.from_store_id)
            to_store = db.get(Store, order.to_store_id)
            courier = db.get(User, order.courier_id) if order.courier_id else None
            from_name = from_store.name if from_store else "—"
            to_name = to_store.name if to_store else "—"
            courier_name = courier.full_name if courier else "—"
            status_text = status_map.get(order.status, "—")
            
            order_text = f"🟢 №{order.number}\n👤 {courier_name}\n{from_name}\n↓\n{to_name}\n{status_text}"
            
            buttons.append([
                InlineKeyboardButton(
                    text=order_text,
                    callback_data=f"admin_order_detail:{order.id}",
                )
            ])
        
        # Add pagination buttons
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(text="◀️ Попередня", callback_data=f"admin_orders_in_progress_page:{page-1}")
            )
        pagination_buttons.append(
            InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="admin_orders_in_progress_info")
        )
        if page < total_pages - 1:
            pagination_buttons.append(
                InlineKeyboardButton(text="Наступна ▶️", callback_data=f"admin_orders_in_progress_page:{page+1}")
            )
        
        if pagination_buttons:
            buttons.append(pagination_buttons)
        
        buttons.append([
            InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")
        ])
        
        await callback.message.answer(
            "🚚 В роботі",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data.startswith("admin_orders_in_progress_page:"))
async def admin_orders_in_progress_page(callback: CallbackQuery):
    db = SessionLocal()
    try:
        page = int(callback.data.split(":")[1])
        
        # Get all in-progress orders (ACCEPTED, PICKED_UP, DELIVERING), sorted by accepted_at (oldest first)
        in_progress_orders = db.query(Order).filter(
            Order.status.in_([OrderStatus.ACCEPTED, OrderStatus.PICKED_UP, OrderStatus.DELIVERING])
        ).order_by(Order.accepted_at).all()
        
        if not in_progress_orders:
            await callback.message.edit_text(
                "🚚 В роботі\n\nЗаявок не знайдено.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")],
                ])
            )
            await callback.answer()
            return
        
        # Build keyboard with pagination
        page_size = 10
        total_pages = (len(in_progress_orders) + page_size - 1) // page_size
        
        # Ensure page is valid
        if page < 0 or page >= total_pages:
            page = 0
        
        start_idx = page * page_size
        end_idx = start_idx + page_size
        page_orders = in_progress_orders[start_idx:end_idx]
        
        # Status emoji mapping
        status_map = {
            OrderStatus.ACCEPTED: "✅ Прийнято",
            OrderStatus.PICKED_UP: "📦 Забрано",
            OrderStatus.DELIVERING: "🚚 Доставляється",
        }
        
        buttons = []
        for order in page_orders:
            from_store = db.get(Store, order.from_store_id)
            to_store = db.get(Store, order.to_store_id)
            courier = db.get(User, order.courier_id) if order.courier_id else None
            from_name = from_store.name if from_store else "—"
            to_name = to_store.name if to_store else "—"
            courier_name = courier.full_name if courier else "—"
            status_text = status_map.get(order.status, "—")
            
            order_text = f"🟢 №{order.number}\n👤 {courier_name}\n{from_name}\n↓\n{to_name}\n{status_text}"
            
            buttons.append([
                InlineKeyboardButton(
                    text=order_text,
                    callback_data=f"admin_order_detail:{order.id}",
                )
            ])
        
        # Add pagination buttons
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(text="◀️ Попередня", callback_data=f"admin_orders_in_progress_page:{page-1}")
            )
        pagination_buttons.append(
            InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="admin_orders_in_progress_info")
        )
        if page < total_pages - 1:
            pagination_buttons.append(
                InlineKeyboardButton(text="Наступна ▶️", callback_data=f"admin_orders_in_progress_page:{page+1}")
            )
        
        if pagination_buttons:
            buttons.append(pagination_buttons)
        
        buttons.append([
            InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")
        ])
        
        await callback.message.edit_text(
            "🚚 В роботі",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_orders_in_progress_info")
async def admin_orders_in_progress_info(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data == "admin_orders_delivered")
async def admin_orders_delivered(callback: CallbackQuery):
    db = SessionLocal()
    try:
        # Get delivered orders, sorted newest first (by delivered_at or created_at)
        delivered_orders = db.query(Order).filter(
            Order.status == OrderStatus.DELIVERED
        ).order_by(Order.created_at.desc()).all()
        
        if not delivered_orders:
            await callback.message.answer(
                "✅ Доставлені\n\nДоставлених заявок не знайдено.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")],
                ])
            )
            await callback.answer()
            return
        
        # Build keyboard with pagination
        page = 0
        page_size = 10
        total_pages = (len(delivered_orders) + page_size - 1) // page_size
        start_idx = page * page_size
        end_idx = start_idx + page_size
        page_orders = delivered_orders[start_idx:end_idx]
        
        buttons = []
        for order in page_orders:
            from_store = db.get(Store, order.from_store_id)
            to_store = db.get(Store, order.to_store_id)
            from_name = from_store.name if from_store else "—"
            to_name = to_store.name if to_store else "—"
            date_str = order.delivered_at.strftime("%d.%m") if order.delivered_at else "—"
            
            order_text = f"✅ №{order.number}\n{from_name} → {to_name}\n{date_str}"
            
            buttons.append([
                InlineKeyboardButton(
                    text=order_text,
                    callback_data=f"admin_order_detail:{order.id}",
                )
            ])
        
        # Add pagination buttons
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(text="◀️ Попередня", callback_data=f"admin_orders_delivered_page:{page-1}")
            )
        pagination_buttons.append(
            InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="admin_orders_delivered_info")
        )
        if page < total_pages - 1:
            pagination_buttons.append(
                InlineKeyboardButton(text="Наступна ▶️", callback_data=f"admin_orders_delivered_page:{page+1}")
            )
        
        if pagination_buttons:
            buttons.append(pagination_buttons)
        
        buttons.append([
            InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")
        ])
        
        await callback.message.answer(
            "✅ Доставлені",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data.startswith("admin_orders_delivered_page:"))
async def admin_orders_delivered_page(callback: CallbackQuery):
    db = SessionLocal()
    try:
        page = int(callback.data.split(":")[1])
        
        # Get delivered orders, sorted newest first
        delivered_orders = db.query(Order).filter(
            Order.status == OrderStatus.DELIVERED
        ).order_by(Order.created_at.desc()).all()
        
        if not delivered_orders:
            await callback.message.edit_text(
                "✅ Доставлені\n\nДоставлених заявок не знайдено.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")],
                ])
            )
            await callback.answer()
            return
        
        # Build keyboard with pagination
        page_size = 10
        total_pages = (len(delivered_orders) + page_size - 1) // page_size
        
        # Ensure page is valid
        if page < 0 or page >= total_pages:
            page = 0
        
        start_idx = page * page_size
        end_idx = start_idx + page_size
        page_orders = delivered_orders[start_idx:end_idx]
        
        buttons = []
        for order in page_orders:
            from_store = db.get(Store, order.from_store_id)
            to_store = db.get(Store, order.to_store_id)
            from_name = from_store.name if from_store else "—"
            to_name = to_store.name if to_store else "—"
            date_str = order.delivered_at.strftime("%d.%m") if order.delivered_at else "—"
            
            order_text = f"✅ №{order.number}\n{from_name} → {to_name}\n{date_str}"
            
            buttons.append([
                InlineKeyboardButton(
                    text=order_text,
                    callback_data=f"admin_order_detail:{order.id}",
                )
            ])
        
        # Add pagination buttons
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(text="◀️ Попередня", callback_data=f"admin_orders_delivered_page:{page-1}")
            )
        pagination_buttons.append(
            InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="admin_orders_delivered_info")
        )
        if page < total_pages - 1:
            pagination_buttons.append(
                InlineKeyboardButton(text="Наступна ▶️", callback_data=f"admin_orders_delivered_page:{page+1}")
            )
        
        if pagination_buttons:
            buttons.append(pagination_buttons)
        
        buttons.append([
            InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")
        ])
        
        await callback.message.edit_text(
            "✅ Доставлені",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_orders_delivered_info")
async def admin_orders_delivered_info(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data == "admin_orders_canceled")
async def admin_orders_canceled(callback: CallbackQuery):
    db = SessionLocal()
    try:
        # Get canceled orders, sorted newest first
        canceled_orders = db.query(Order).filter(
            Order.status == OrderStatus.CANCELED
        ).order_by(Order.created_at.desc()).all()
        
        if not canceled_orders:
            await callback.message.answer(
                "❌ Скасовані\n\nСкасованих заявок не знайдено.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")],
                ])
            )
            await callback.answer()
            return
        
        # Build keyboard with pagination
        page = 0
        page_size = 10
        total_pages = (len(canceled_orders) + page_size - 1) // page_size
        start_idx = page * page_size
        end_idx = start_idx + page_size
        page_orders = canceled_orders[start_idx:end_idx]
        
        buttons = []
        for order in page_orders:
            from_store = db.get(Store, order.from_store_id)
            to_store = db.get(Store, order.to_store_id)
            from_name = from_store.name if from_store else "—"
            to_name = to_store.name if to_store else "—"
            date_str = order.created_at.strftime("%d.%m") if order.created_at else "—"
            
            order_text = f"❌ №{order.number}\n{from_name} → {to_name}\n{date_str}"
            
            buttons.append([
                InlineKeyboardButton(
                    text=order_text,
                    callback_data=f"admin_order_detail:{order.id}",
                )
            ])
        
        # Add pagination buttons
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(text="◀️ Попередня", callback_data=f"admin_orders_canceled_page:{page-1}")
            )
        pagination_buttons.append(
            InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="admin_orders_canceled_info")
        )
        if page < total_pages - 1:
            pagination_buttons.append(
                InlineKeyboardButton(text="Наступна ▶️", callback_data=f"admin_orders_canceled_page:{page+1}")
            )
        
        if pagination_buttons:
            buttons.append(pagination_buttons)
        
        buttons.append([
            InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")
        ])
        
        await callback.message.answer(
            "❌ Скасовані",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data.startswith("admin_orders_canceled_page:"))
async def admin_orders_canceled_page(callback: CallbackQuery):
    db = SessionLocal()
    try:
        page = int(callback.data.split(":")[1])
        
        # Get canceled orders, sorted newest first
        canceled_orders = db.query(Order).filter(
            Order.status == OrderStatus.CANCELED
        ).order_by(Order.created_at.desc()).all()
        
        if not canceled_orders:
            await callback.message.edit_text(
                "❌ Скасовані\n\nСкасованих заявок не знайдено.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")],
                ])
            )
            await callback.answer()
            return
        
        # Build keyboard with pagination
        page_size = 10
        total_pages = (len(canceled_orders) + page_size - 1) // page_size
        
        # Ensure page is valid
        if page < 0 or page >= total_pages:
            page = 0
        
        start_idx = page * page_size
        end_idx = start_idx + page_size
        page_orders = canceled_orders[start_idx:end_idx]
        
        buttons = []
        for order in page_orders:
            from_store = db.get(Store, order.from_store_id)
            to_store = db.get(Store, order.to_store_id)
            from_name = from_store.name if from_store else "—"
            to_name = to_store.name if to_store else "—"
            date_str = order.created_at.strftime("%d.%m") if order.created_at else "—"
            
            order_text = f"❌ №{order.number}\n{from_name} → {to_name}\n{date_str}"
            
            buttons.append([
                InlineKeyboardButton(
                    text=order_text,
                    callback_data=f"admin_order_detail:{order.id}",
                )
            ])
        
        # Add pagination buttons
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(text="◀️ Попередня", callback_data=f"admin_orders_canceled_page:{page-1}")
            )
        pagination_buttons.append(
            InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="admin_orders_canceled_info")
        )
        if page < total_pages - 1:
            pagination_buttons.append(
                InlineKeyboardButton(text="Наступна ▶️", callback_data=f"admin_orders_canceled_page:{page+1}")
            )
        
        if pagination_buttons:
            buttons.append(pagination_buttons)
        
        buttons.append([
            InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")
        ])
        
        await callback.message.edit_text(
            "❌ Скасовані",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_orders_canceled_info")
async def admin_orders_canceled_info(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data == "admin_orders_separator")
async def admin_orders_separator(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data == "admin_orders_urgent")
async def admin_orders_urgent(callback: CallbackQuery):
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        urgent_orders = []
        
        # Get all orders
        all_orders = db.query(Order).all()
        
        for order in all_orders:
            is_urgent = False
            urgency_score = 0
            wait_time_minutes = 0
            reference_time = None
            
            # Rule 1: HIGH priority orders
            if order.priority == OrderPriority.HIGH:
                is_urgent = True
                urgency_score = 1000  # Highest priority
                reference_time = order.created_at
                wait_time_minutes = int((now - order.created_at).total_seconds() / 60)
            
            # Rule 2: Orders waiting for courier longer than 20 minutes
            elif order.status == OrderStatus.WAITING_FOR_COURIER:
                if order.created_at:
                    wait_time_minutes = int((now - order.created_at).total_seconds() / 60)
                    if wait_time_minutes > 20:
                        is_urgent = True
                        urgency_score = 500 + wait_time_minutes  # Higher score = more urgent
                        reference_time = order.created_at
            
            # Rule 3: Deliveries in progress longer than 60 minutes
            elif order.status in (OrderStatus.ACCEPTED, OrderStatus.PICKED_UP, OrderStatus.DELIVERING):
                if order.accepted_at:
                    wait_time_minutes = int((now - order.accepted_at).total_seconds() / 60)
                    if wait_time_minutes > 60:
                        is_urgent = True
                        urgency_score = 200 + wait_time_minutes  # Higher score = more urgent
                        reference_time = order.accepted_at
            
            if is_urgent:
                urgent_orders.append({
                    'order': order,
                    'urgency_score': urgency_score,
                    'wait_time_minutes': wait_time_minutes,
                    'reference_time': reference_time
                })
        
        # Sort by urgency (highest score first = most urgent first)
        urgent_orders.sort(key=lambda x: x['urgency_score'], reverse=True)
        
        if not urgent_orders:
            await callback.message.answer(
                "🔥 Термінові\n\nТермінових заявок не знайдено.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")],
                ])
            )
            await callback.answer()
            return
        
        # Build keyboard with urgent orders
        buttons = []
        
        for item in urgent_orders[:20]:  # Limit to 20 results
            order = item['order']
            wait_time = item['wait_time_minutes']
            
            # Format status
            status_map = {
                OrderStatus.WAITING_FOR_COURIER: "🟡 Очікує",
                OrderStatus.ACCEPTED: "✅ Прийнято",
                OrderStatus.PICKED_UP: "📦 Забрано",
                OrderStatus.DELIVERING: "🚚 Доставляється",
            }
            status_text = status_map.get(order.status, "—")
            
            # Format wait time
            hours = wait_time // 60
            minutes = wait_time % 60
            if hours > 0:
                wait_text = f"{hours}ч {minutes}хв"
            else:
                wait_text = f"{minutes}хв"
            
            order_text = f"🔴 №{order.number}\n{status_text}\n⏱ {wait_text}"
            
            buttons.append([
                InlineKeyboardButton(
                    text=order_text,
                    callback_data=f"admin_order_detail:{order.id}"
                )
            ])
        
        buttons.append([
            InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")
        ])
        
        await callback.message.answer(
            "🔥 Термінові заявки",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_orders_search")
async def admin_orders_search(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminOrderSearchState.waiting_for_search_query)
    await callback.message.answer(
        "🔍 Пошук заявки\n\nВведіть:\n"
        "• Номер заявки (повний або частковий)\n"
        "• Ім'я менеджера\n"
        "• Ім'я кур'єра\n"
        "• Назву магазину",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Скасувати", callback_data="admin_orders_back")],
        ])
    )
    await callback.answer()


@router.message(AdminOrderSearchState.waiting_for_search_query, AdminFilter())
async def admin_search_query(message: Message, state: FSMContext):
    db = SessionLocal()
    try:
        query = message.text.strip().lower()
        
        if not query:
            await message.answer("❌ Пошуковий запит не може бути порожним.")
            return
        
        # Search orders by multiple criteria
        all_orders = db.query(Order).all()
        matching_orders = []
        
        for order in all_orders:
            # Search by order number (partial match)
            if query in order.number.lower():
                matching_orders.append(order)
                continue
            
            # Search by manager name
            manager = db.get(User, order.created_by)
            if manager and query in manager.full_name.lower():
                matching_orders.append(order)
                continue
            
            # Search by courier name
            if order.courier_id:
                courier = db.get(User, order.courier_id)
                if courier and query in courier.full_name.lower():
                    matching_orders.append(order)
                    continue
            
            # Search by store name (from or to)
            from_store = db.get(Store, order.from_store_id)
            if from_store and query in from_store.name.lower():
                matching_orders.append(order)
                continue
            
            to_store = db.get(Store, order.to_store_id)
            if to_store and query in to_store.name.lower():
                matching_orders.append(order)
                continue
        
        # Remove duplicates while preserving order
        seen = set()
        unique_orders = []
        for order in matching_orders:
            if order.id not in seen:
                seen.add(order.id)
                unique_orders.append(order)
        
        # Display results
        if not unique_orders:
            await message.answer(
                f"❌ За запитом '{message.text}' нічого не знайдено.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔍 Новий пошук", callback_data="admin_orders_search")],
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")],
                ])
            )
        else:
            # Build search results keyboard
            buttons = []
            for order in unique_orders[:20]:  # Limit to 20 results
                from_store = db.get(Store, order.from_store_id)
                to_store = db.get(Store, order.to_store_id)
                from_name = from_store.name if from_store else "—"
                to_name = to_store.name if to_store else "—"
                
                status_map = {
                    OrderStatus.WAITING_FOR_COURIER: "🟡",
                    OrderStatus.ACCEPTED: "✅",
                    OrderStatus.PICKED_UP: "📦",
                    OrderStatus.DELIVERING: "🚚",
                    OrderStatus.DELIVERED: "✅",
                    OrderStatus.CANCELED: "❌",
                }
                status_emoji = status_map.get(order.status, "•")
                
                result_text = f"{status_emoji} №{order.number} ({from_name} → {to_name})"
                buttons.append([
                    InlineKeyboardButton(
                        text=result_text,
                        callback_data=f"admin_order_detail:{order.id}"
                    )
                ])
            
            buttons.append([
                InlineKeyboardButton(text="🔍 Новий пошук", callback_data="admin_orders_search")
            ])
            buttons.append([
                InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders_back")
            ])
            
            result_count = len(unique_orders)
            count_text = f"результатів" if result_count % 10 != 1 else f"результат"
            await message.answer(
                f"🔍 Знайдено {result_count} {count_text}:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            )
        
        await state.clear()
    finally:
        db.close()


@router.callback_query(F.data == "admin_orders_back")
async def admin_orders_back(callback: CallbackQuery):
    db = SessionLocal()
    try:
        # Get all orders
        all_orders = db.query(Order).all()
        
        # Count orders by status
        waiting_count = len([o for o in all_orders if o.status == OrderStatus.WAITING_FOR_COURIER])
        in_progress_count = len([o for o in all_orders if o.status in (OrderStatus.ACCEPTED, OrderStatus.PICKED_UP, OrderStatus.DELIVERING)])
        delivered_count = len([o for o in all_orders if o.status == OrderStatus.DELIVERED])
        canceled_count = len([o for o in all_orders if o.status == OrderStatus.CANCELED])
        
        await callback.message.edit_text(
            "📦 Замовлення",
            reply_markup=build_orders_menu_keyboard(waiting_count, in_progress_count, delivered_count, canceled_count),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_manager_profile_delete")
async def manager_profile_delete(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        data = await state.get_data()
        manager_id = data.get("current_manager_id")
        
        if not manager_id:
            await callback.message.answer("❌ Не вдалося визначити менеджера.")
            await callback.answer()
            return
        
        manager = db.get(User, manager_id)
        if not manager:
            await callback.message.answer("❌ Менеджера не знайдено.")
            await callback.answer()
            return
        
        # Check for created orders (any status)
        created_orders = db.query(Order).filter(Order.created_by == manager_id).all()
        
        # Check for active orders (specific statuses)
        active_statuses = [
            OrderStatus.WAITING_FOR_COURIER,
            OrderStatus.ACCEPTED,
            OrderStatus.PICKED_UP,
            OrderStatus.DELIVERING,
        ]
        active_orders = db.query(Order).filter(
            Order.created_by == manager_id,
            Order.status.in_(active_statuses)
        ).all()
        
        # Check for delivery history (completed orders)
        completed_orders = db.query(Order).filter(
            Order.created_by == manager_id,
            Order.status.in_([OrderStatus.DELIVERED, OrderStatus.CANCELED])
        ).all()
        
        # Show error if any orders exist
        if created_orders:
            error_message = "❌ Неможливо видалити менеджера.\n\n"
            
            if active_orders:
                error_message += f"🔴 Активних замовлень: {len(active_orders)}\n"
            
            if completed_orders:
                error_message += f"✅ Завершених замовлень: {len(completed_orders)}\n"
            
            error_message += "\nСпочатку видаліть або переприв'яжіть всі замовлення."
            
            await callback.message.answer(error_message)
            await callback.answer()
            return
        
        # Show confirmation if no orders
        confirmation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Видалити",
                    callback_data=f"admin_manager_delete_confirm:{manager_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Скасувати",
                    callback_data="admin_manager_profile_back",
                )
            ],
        ])
        
        await callback.message.edit_text(
            "⚠️ Ви впевнені?\n\n"
            "Менеджер буде видалено безповоротно.",
            reply_markup=confirmation_keyboard,
        )
        await callback.answer()
    except Exception as exc:
        logger.exception("Failed to check manager for deletion")
        await callback.message.answer(
            "❌ Не вдалося перевірити можливість видалення.\n\nСпробуйте ще раз.",
            reply_markup=admin_main_menu(),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data.startswith("admin_manager_delete_confirm:"))
async def manager_delete_confirm(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        manager_id = int(callback.data.split(":", 1)[1])
        manager = db.get(User, manager_id)
        
        if not manager:
            await callback.message.answer("❌ Менеджера не знайдено.")
            await callback.answer()
            return
        
        # Delete manager
        db.delete(manager)
        db.commit()
        
        # Show confirmation
        await callback.message.answer("✅ Менеджер успішно видалено.")
        await callback.answer()
        
        # Return to managers list
        db = SessionLocal()
        try:
            all_users = db.query(User).filter(User.role == UserRole.MANAGER).all()
            activated_managers = [u for u in all_users if u.telegram_id is not None]
            non_activated_managers = [u for u in all_users if u.telegram_id is None]
            
            await callback.message.edit_text(
                "👨‍💼 Менеджери",
                reply_markup=build_managers_list_keyboard(all_users, page=0),
            )
        finally:
            db.close()
    except Exception as exc:
        logger.exception("Failed to delete manager")
        await callback.message.answer(
            "❌ Не вдалося видалити менеджера.\n\nСпробуйте ще раз.",
            reply_markup=admin_main_menu(),
        )
        await callback.answer()
    finally:
        db.close()


@router.callback_query(F.data == "admin_manager_profile_back")
async def manager_profile_back(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        data = await state.get_data()
        manager_id = data.get("current_manager_id")
        
        if not manager_id:
            await callback.message.answer("❌ Не вдалося визначити менеджера.")
            await callback.answer()
            return
        
        manager = db.get(User, manager_id)
        if not manager:
            await callback.message.answer("❌ Менеджера не знайдено.")
            await callback.answer()
            return
        
        # Determine status
        status = "🟢 Активний" if manager.telegram_id else "⚪ Неактивний"
        
        # Get store info
        store_info = f"{manager.store.name}" if manager.store else "Не призначен"
        
        # Get telegram username
        telegram_username = f"@{manager.username}" if manager.username else "Не прив'язано"
        
        profile_text = (
            f"👤 {manager.full_name}\n\n"
            f"{status}\n\n"
            f"🏪 {store_info}\n\n"
            f"📞 {telegram_username}"
        )
        
        await callback.message.edit_text(
            profile_text,
            reply_markup=build_manager_profile_keyboard(),
        )
        await callback.answer()
    except Exception as exc:
        logger.exception("Failed to return to manager profile")
        await callback.message.answer(
            "❌ Не вдалося повернутися до профіля.",
            reply_markup=admin_main_menu(),
        )
        await callback.answer()
    finally:
        db.close()
