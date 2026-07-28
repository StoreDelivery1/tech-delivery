import logging
from datetime import datetime, timedelta, date

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot.bot import bot
from app.bot.filters.roles import CourierFilter
from app.bot.keyboards.main_menu import courier_main_menu
from app.bot.keyboards.order_inline import (
    accept_order_keyboard,
    delivered_keyboard,
    delivering_keyboard,
    picked_up_keyboard,
)
from app.bot.utils.order_formatter import format_order
from app.database.session import SessionLocal
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.services.activation_service import ActivationService
from app.services.courier_service import CourierService
from app.services.distribution_service import DistributionService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)
router = Router()


def is_free_orders_button(text: str | None) -> bool:
    return text in {"📦 Вільні заявки", "📦 Вільні замовлення"}


@router.message(F.text.in_({"📦 Вільні заявки", "📦 Вільні замовлення"}), CourierFilter())
async def free_orders_handler(message: Message):
    print(f"ROUTER: courier | {message.text}")
    db = SessionLocal()

    try:
        courier = ActivationService.get_courier(
            db,
            message.from_user.id,
        )

        open_orders = CourierService.get_open_orders(db)

        if not open_orders:
            await message.answer("📭 Наразі немає доступних заявок.")
            return

        for order in open_orders:
            await message.answer(
                format_order(order),
                reply_markup=accept_order_keyboard(order.id),
            )

    except ValueError as e:
        await message.answer(f"❌ {str(e)}")
    finally:
        db.close()


@router.message(F.text == "📋 Мої замовлення", CourierFilter())
async def my_orders_handler(message: Message):
    db = SessionLocal()

    try:
        courier = ActivationService.get_courier(
            db,
            message.from_user.id,
        )

        my_orders = CourierService.get_orders(db, courier.id)

        if not my_orders:
            await message.answer("📭 У вас немає активних замовлень.")
            return

        for order in my_orders:
            keyboard = None
            if order.status == OrderStatus.ACCEPTED:
                keyboard = picked_up_keyboard(order.id)
            elif order.status == OrderStatus.PICKED_UP:
                keyboard = delivering_keyboard(order.id)
            elif order.status == OrderStatus.DELIVERING:
                keyboard = delivered_keyboard(order.id)

            await message.answer(
                format_order(order),
                reply_markup=keyboard,
            )

    except ValueError as e:
        await message.answer(f"❌ {str(e)}")
    finally:
        db.close()


@router.callback_query(lambda callback: callback.data and callback.data.startswith("accept:"), CourierFilter())
async def accept_order_callback(callback: CallbackQuery):
    db = SessionLocal()

    try:
        order_id = int(callback.data.split(":", 1)[1])

        courier = ActivationService.get_courier(
            db,
            callback.from_user.id,
        )

        order = CourierService.accept_order(
            db=db,
            order_id=order_id,
            courier_id=courier.id,
        )

        logger.info(
            "Order accepted | order_id=%s order_number=%s courier_id=%s order_status=%s order.creator=%s",
            order.id,
            order.number,
            courier.id,
            order.status,
            order.creator,
        )
        await NotificationService.notify_order_accepted(bot, order)
        db.add(order)
        db.commit()

        await callback.message.edit_text(
            "✅ Замовлення успішно прийнято.",
            reply_markup=None,
        )
        await callback.answer()

    except ValueError as e:
        error_msg = str(e)
        if "cannot be accepted" in error_msg.lower():
            await callback.answer("❌ Цю заявку вже прийняв інший кур'єр.", show_alert=True)
        else:
            await callback.answer(f"❌ {error_msg}", show_alert=True)
    except TypeError as e:
        await callback.answer(f"❌ {str(e)}", show_alert=True)
    finally:
        db.close()


# ── Shift Management ────────────────────────────────────────────────────────

@router.message(F.text == "🟢 Почати зміну", CourierFilter())
async def start_shift_handler(message: Message):
    db = SessionLocal()
    try:
        courier = ActivationService.get_courier(db, message.from_user.id)

        courier = CourierService.start_shift(db, courier.id)
        await message.answer(
            "✅ Ви розпочали зміну.\n\n"
            "Тепер ви будете отримувати нові заявки.",
            reply_markup=courier_main_menu(courier),
        )

        # Try to distribute a waiting order to this newly available courier
        await DistributionService.distribute_next_waiting_order(bot, db, courier)

    except ValueError as e:
        await message.answer(f"❌ {str(e)}")
    finally:
        db.close()


@router.message(F.text == "🔴 Завершити зміну", CourierFilter())
async def end_shift_handler(message: Message):
    db = SessionLocal()
    try:
        courier = ActivationService.get_courier(db, message.from_user.id)

        courier = CourierService.end_shift(db, courier.id)
        await message.answer(
            "✅ Зміну завершено.",
            reply_markup=courier_main_menu(courier),
        )

    except ValueError as e:
        await message.answer(f"❌ {e}")
    finally:
        db.close()


@router.callback_query(lambda callback: callback.data and callback.data.startswith("pickup:"), CourierFilter())
async def pickup_order_callback(callback: CallbackQuery):
    db = SessionLocal()

    try:
        order_id = int(callback.data.split(":", 1)[1])

        courier = ActivationService.get_courier(
            db,
            callback.from_user.id,
        )

        order = CourierService.change_status(
            db=db,
            order_id=order_id,
            courier_id=courier.id,
            new_status=OrderStatus.PICKED_UP,
        )

        logger.info(
            "Order picked up | order_id=%s order_number=%s courier_id=%s order_status=%s order.creator=%s",
            order.id,
            order.number,
            courier.id,
            order.status,
            order.creator,
        )
        await NotificationService.notify_order_picked_up(bot, order)
        db.add(order)
        db.commit()

        await callback.message.edit_text("✅ Статус оновлено.", reply_markup=None)
        await callback.answer()

    except (ValueError, TypeError) as e:
        await callback.answer(f"❌ {str(e)}", show_alert=True)
    finally:
        db.close()


@router.callback_query(lambda callback: callback.data and callback.data.startswith("delivering:"), CourierFilter())
async def delivering_order_callback(callback: CallbackQuery):
    db = SessionLocal()

    try:
        order_id = int(callback.data.split(":", 1)[1])

        courier = ActivationService.get_courier(
            db,
            callback.from_user.id,
        )

        order = CourierService.change_status(
            db=db,
            order_id=order_id,
            courier_id=courier.id,
            new_status=OrderStatus.DELIVERING,
        )

        logger.info(
            "Order delivering | order_id=%s order_number=%s courier_id=%s order_status=%s order.creator=%s",
            order.id,
            order.number,
            courier.id,
            order.status,
            order.creator,
        )
        await NotificationService.notify_order_delivering(bot, order)
        db.add(order)
        db.commit()

        await callback.message.edit_text("✅ Статус оновлено.", reply_markup=None)
        await callback.answer()

    except (ValueError, TypeError) as e:
        await callback.answer(f"❌ {str(e)}", show_alert=True)
    finally:
        db.close()


@router.callback_query(lambda callback: callback.data and callback.data.startswith("delivered:"), CourierFilter())
async def delivered_order_callback(callback: CallbackQuery):
    db = SessionLocal()

    try:
        order_id = int(callback.data.split(":", 1)[1])

        courier = ActivationService.get_courier(
            db,
            callback.from_user.id,
        )

        order = CourierService.change_status(
            db=db,
            order_id=order_id,
            courier_id=courier.id,
            new_status=OrderStatus.AWAITING_CONFIRMATION,
        )

        logger.info(
            "Order marked as awaiting confirmation | order_id=%s order_number=%s courier_id=%s order_status=%s",
            order.id,
            order.number,
            courier.id,
            order.status,
        )

        # Notify courier that goods were transferred
        await NotificationService.notify_courier_goods_transferred(bot, order)

        # Notify all destination store managers to confirm delivery
        await NotificationService.notify_delivery_confirmation_request(db, bot, order)

        db.add(order)
        db.commit()

        # After transfer, try to distribute a waiting order if courier is now AVAILABLE
        courier_updated = db.get(User, courier.id)
        if courier_updated:
            await DistributionService.distribute_next_waiting_order(bot, db, courier_updated)

        await callback.message.edit_text("📍 Передано магазину.", reply_markup=None)
        await callback.answer()

    except (ValueError, TypeError) as e:
        await callback.answer(f"❌ {str(e)}", show_alert=True)
    finally:
        db.close()


# ── Courier Statistics ────────────────────────────────────────────────────────

_COURIER_ACTIVE_STATUSES = [
    OrderStatus.ACCEPTED,
    OrderStatus.PICKED_UP,
    OrderStatus.DELIVERING,
]


def _get_courier_orders_for_date_range(db, courier_id: int, date_range: str) -> list:
    """Get all orders assigned to this courier, filtered by date range.
    
    Only returns orders where Order.courier_id == courier_id.
    Never includes other couriers' statistics.
    """
    today = date.today()
    
    # Base query: only orders assigned to this courier
    query = db.query(Order).filter(Order.courier_id == courier_id)
    
    if date_range == "today":
        # Only orders accepted/started today
        query = query.filter(
            Order.created_at.isnot(None),
            Order.created_at >= datetime.combine(today, datetime.min.time()),
            Order.created_at < datetime.combine(today + timedelta(days=1), datetime.min.time()),
        )
    elif date_range == "month":
        # Only orders accepted/started this month
        month_start = today.replace(day=1)
        query = query.filter(
            Order.created_at.isnot(None),
            Order.created_at >= datetime.combine(month_start, datetime.min.time()),
        )
    # else: date_range == "all" - return all orders for this courier
    
    return query.order_by(Order.created_at.desc()).all()


def _calculate_courier_statistics(orders: list) -> dict:
    """Calculate delivery statistics for this courier only.
    
    Statistics include:
    - completed: orders successfully delivered (COMPLETED or DELIVERED for backward compatibility)
    - active: orders in active states (accepted, picked up, delivering)
    """
    completed = sum(1 for o in orders if o.status in (OrderStatus.COMPLETED, OrderStatus.DELIVERED))
    active = sum(1 for o in orders if o.status in _COURIER_ACTIVE_STATUSES)
    
    return {
        "completed": completed,
        "active": active,
    }


def _build_courier_statistics_message(stats: dict, date_range: str) -> str:
    """Build formatted courier statistics message.
    
    Shows only this courier's statistics, never other couriers or system stats.
    """
    range_label = {
        "today": "📅 Сьогодні",
        "month": "📆 Цього місяця",
        "all": "🏆 За весь час",
    }.get(date_range, "🏆 За весь час")
    
    return (
        f"📊 <b>Моя статистика</b>\n\n"
        f"{range_label}\n\n"
        f"📦 <b>Виконано доставок:</b> {stats['completed']}\n"
        f"� <b>Активних доставок:</b> {stats['active']}"
    )


def _build_courier_statistics_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for courier statistics date range selection.
    
    Uses dedicated courier_stats callbacks to ensure complete isolation.
    """
    buttons = [
        [
            InlineKeyboardButton(
                text="📅 Сьогодні",
                callback_data="courier_stats:today",
            )
        ],
        [
            InlineKeyboardButton(
                text="📆 Цей місяць",
                callback_data="courier_stats:month",
            )
        ],
        [
            InlineKeyboardButton(
                text="🏆 За весь час",
                callback_data="courier_stats:all",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="courier_stats_back",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text == "📊 Статистика", CourierFilter())
async def courier_statistics_handler(message: Message):
    """Display courier's delivery statistics for all time by default."""
    db = SessionLocal()
    try:
        courier = ActivationService.get_courier(db, message.from_user.id)

        # Get all orders assigned to this courier for all time
        courier_orders = _get_courier_orders_for_date_range(db, courier.id, "all")
        
        # Calculate statistics for this courier only
        stats = _calculate_courier_statistics(courier_orders)
        
        text = _build_courier_statistics_message(stats, "all")
        keyboard = _build_courier_statistics_keyboard()
        
        logger.info(f"[TRACE] Sending message: Statistics report with {len(courier_orders)} orders")
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

    finally:
        db.close()


@router.callback_query(F.data.startswith("courier_stats:"), CourierFilter())
async def courier_statistics_callback(callback: CallbackQuery):
    """Handle courier statistics date range selection."""
    db = SessionLocal()
    try:
        date_range = callback.data.split(":", 1)[1]
        
        courier = ActivationService.get_courier(db, callback.from_user.id)

        # Get orders for selected date range
        courier_orders = _get_courier_orders_for_date_range(db, courier.id, date_range)
        
        # Calculate statistics for this courier only
        stats = _calculate_courier_statistics(courier_orders)
        
        text = _build_courier_statistics_message(stats, date_range)
        keyboard = _build_courier_statistics_keyboard()
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer()

    finally:
        db.close()


@router.callback_query(F.data == "courier_stats_back", CourierFilter())
async def courier_stats_back(callback: CallbackQuery):
    """Return to courier main menu from statistics."""
    db = SessionLocal()
    try:
        courier = ActivationService.get_courier(db, callback.from_user.id)
        
        await callback.message.answer(
            "📋 Головне меню",
            reply_markup=courier_main_menu(courier),
        )
        await callback.answer()

    finally:
        db.close()


# ── Courier Profile ───────────────────────────────────────────────────────────


def _fmt_availability(availability) -> str:
    """Format courier availability status."""
    status_map = {
        "AVAILABLE": "🟢 На зміні",
        "BUSY": "🟡 Виконує доставку",
        "OFFLINE": "⚫ Поза зміною",
    }
    return status_map.get(availability, "—")


def _fmt_last_login(last_login_at) -> str:
    """Format last login timestamp."""
    if not last_login_at:
        return "Ніколи"
    return last_login_at.strftime("%d.%m.%Y %H:%M")


def _build_courier_profile_message(courier) -> str:
    """Build courier profile message (simplified, no store information)."""
    telegram_username = f"@{courier.username}" if courier.username else "Не вказано"
    availability = _fmt_availability(courier.availability.value if courier.availability else None)
    last_login = _fmt_last_login(courier.last_login_at)
    
    return (
        f"👤 <b>Профіль</b>\n\n"
        f"👤 ПІБ: {courier.full_name}\n\n"
        f"🆔 ID: {courier.id}\n\n"
        f"📱 Telegram: {telegram_username}\n\n"
        f"{availability}\n\n"
        f"🕒 Останній вхід: {last_login}\n\n"
        f"────────────────\n\n"
        f"🔒 Персональні дані змінюються адміністратором."
    )


def _build_courier_profile_keyboard() -> InlineKeyboardMarkup:
    """Build courier profile keyboard."""
    buttons = [
        [
            InlineKeyboardButton(
                text="ℹ️ Про акаунт",
                callback_data="courier_profile:account",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="courier_back_to_menu",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text == "👤 Профіль", CourierFilter())
async def courier_profile_handler(message: Message):
    """Display courier profile (simplified, without store information)."""
    db = SessionLocal()
    try:
        courier = ActivationService.get_courier(db, message.from_user.id)
        
        text = _build_courier_profile_message(courier)
        keyboard = _build_courier_profile_keyboard()
        
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

    finally:
        db.close()


@router.callback_query(F.data.startswith("courier_profile:"), CourierFilter())
async def courier_profile_callback(callback: CallbackQuery):
    """Handle courier profile sub-pages."""
    db = SessionLocal()
    try:
        category = callback.data.split(":", 1)[1]
        
        courier = ActivationService.get_courier(db, callback.from_user.id)
        
        if category == "account":
            text = (
                "ℹ️ <b>Про акаунт</b>\n\n"
                "Ваш акаунт керується адміністратором.\n\n"
                "<b>Для:</b>\n\n"
                "• переприв'язки Telegram;\n"
                "• відновлення доступу;\n"
                "• зміни персональних даних;\n\n"
                "зверніться до адміністратора."
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="courier_profile_back",
                )
            ]])
            
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
            await callback.answer()
        else:
            await callback.answer("❌ Невідома категорія", show_alert=True)

    finally:
        db.close()


@router.callback_query(F.data == "courier_profile_back", CourierFilter())
async def courier_profile_back(callback: CallbackQuery):
    """Return to courier profile main page."""
    db = SessionLocal()
    try:
        courier = ActivationService.get_courier(db, callback.from_user.id)
        
        text = _build_courier_profile_message(courier)
        keyboard = _build_courier_profile_keyboard()
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await callback.answer()

    finally:
        db.close()


@router.callback_query(F.data == "courier_back_to_menu", CourierFilter())
async def courier_back_to_menu(callback: CallbackQuery):
    """Return to courier main menu."""
    db = SessionLocal()
    try:
        courier = ActivationService.get_courier(db, callback.from_user.id)
        
        await callback.message.answer(
            "📋 Головне меню",
            reply_markup=courier_main_menu(courier),
        )
        await callback.answer()

    finally:
        db.close()
