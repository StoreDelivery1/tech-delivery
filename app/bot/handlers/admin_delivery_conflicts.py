"""Admin handlers for delivery conflict management."""

import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.bot import bot
from app.bot.filters.roles import AdminFilter
from app.database.session import SessionLocal
from app.models.order import Order, OrderStatus
from app.services.activation_service import ActivationService
from app.services.notification_service import NotificationService
from app.services.order_status_service import OrderStatusService

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


def _build_conflict_management_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Build keyboard for admin to resolve delivery conflicts."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Переоткрити для підтвердження",
                    callback_data=f"admin_reopen_confirmation:{order_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✅ Примусово завершити",
                    callback_data=f"admin_force_complete:{order_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Скасувати замовлення",
                    callback_data=f"admin_cancel_order:{order_id}",
                ),
            ],
        ]
    )


@router.callback_query(lambda callback: callback.data and callback.data.startswith("admin_reopen_confirmation:"), AdminFilter())
async def admin_reopen_confirmation_callback(callback: CallbackQuery):
    """Admin reopens order for manager to confirm again."""
    db = SessionLocal()

    try:
        order_id = int(callback.data.split(":", 1)[1])

        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            await callback.answer("❌ Замовлення не знайдено", show_alert=True)
            return

        if order.status != OrderStatus.DELIVERY_PROBLEM:
            await callback.answer("❌ Це замовлення не мало проблеми", show_alert=True)
            return

        # Reopen for confirmation
        order = OrderStatusService.resolve_problem(db, order)

        logger.info(
            "Admin reopened delivery conflict | order_id=%s order_number=%s",
            order.id,
            order.number,
        )

        # Send notification to destination managers
        await NotificationService.notify_delivery_confirmation_request(db, bot, order)

        db.add(order)
        db.commit()

        keyboard = _build_conflict_management_keyboard(order.id)
        await callback.message.edit_text(
            f"🔄 Замовлення #{order.number} переоткрито для підтвердження.\n\n"
            f"Менеджерам магазину буде надіслано повідомлення.",
            reply_markup=keyboard
        )
        await callback.answer("✅ Замовлення переоткрито.")

    except ValueError as e:
        await callback.answer(f"❌ {str(e)}", show_alert=True)
    finally:
        db.close()


@router.callback_query(lambda callback: callback.data and callback.data.startswith("admin_force_complete:"), AdminFilter())
async def admin_force_complete_callback(callback: CallbackQuery):
    """Admin force completes an order."""
    db = SessionLocal()

    try:
        order_id = int(callback.data.split(":", 1)[1])

        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            await callback.answer("❌ Замовлення не знайдено", show_alert=True)
            return

        if order.status not in [OrderStatus.DELIVERY_PROBLEM, OrderStatus.AWAITING_CONFIRMATION]:
            await callback.answer("❌ Це замовлення не можна примусово завершити", show_alert=True)
            return

        # Force complete
        order = OrderStatusService.force_complete(db, order)

        logger.info(
            "Admin force completed order | order_id=%s order_number=%s",
            order.id,
            order.number,
        )

        # Send notifications
        await NotificationService.notify_delivery_confirmed(bot, order)
        await NotificationService.notify_delivery_confirmed_to_creator(bot, order)

        db.add(order)
        db.commit()

        keyboard = _build_conflict_management_keyboard(order.id)
        await callback.message.edit_text(
            f"✅ Замовлення #{order.number} примусово завершено.",
            reply_markup=keyboard
        )
        await callback.answer("✅ Замовлення завершено.")

    except ValueError as e:
        await callback.answer(f"❌ {str(e)}", show_alert=True)
    finally:
        db.close()


@router.callback_query(lambda callback: callback.data and callback.data.startswith("admin_cancel_order:"), AdminFilter())
async def admin_cancel_order_callback(callback: CallbackQuery):
    """Admin cancels an order."""
    db = SessionLocal()

    try:
        order_id = int(callback.data.split(":", 1)[1])

        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            await callback.answer("❌ Замовлення не знайдено", show_alert=True)
            return

        if order.status == OrderStatus.CANCELED:
            await callback.answer("❌ Це замовлення уже скасовано", show_alert=True)
            return

        # Cancel order
        order = OrderStatusService.cancel(db, order)

        logger.info(
            "Admin cancelled order | order_id=%s order_number=%s",
            order.id,
            order.number,
        )

        db.add(order)
        db.commit()

        keyboard = _build_conflict_management_keyboard(order.id)
        await callback.message.edit_text(
            f"❌ Замовлення #{order.number} скасовано.",
            reply_markup=keyboard
        )
        await callback.answer("✅ Замовлення скасовано.")

    except ValueError as e:
        await callback.answer(f"❌ {str(e)}", show_alert=True)
    finally:
        db.close()
