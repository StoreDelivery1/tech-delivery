"""Delivery confirmation workflow handlers for managers."""

import logging

from aiogram import Router
from aiogram.types import CallbackQuery

from app.bot.bot import bot
from app.bot.filters.roles import ManagerFilter
from app.database.session import SessionLocal
from app.models.order import Order, OrderStatus
from app.services.activation_service import ActivationService
from app.services.notification_service import NotificationService
from app.services.order_status_service import OrderStatusService

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(ManagerFilter())
router.callback_query.filter(ManagerFilter())


@router.callback_query(lambda callback: callback.data and callback.data.startswith("confirm_delivery:"), ManagerFilter())
async def confirm_delivery_callback(callback: CallbackQuery):
    """Manager confirms that goods were received from courier."""
    db = SessionLocal()

    try:
        order_id = int(callback.data.split(":", 1)[1])

        manager = ActivationService.get_manager(
            db,
            callback.from_user.id,
        )

        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            await callback.answer("❌ Замовлення не знайдено", show_alert=True)
            return

        # Verify manager is from destination store
        if order.to_store_id != manager.store_id:
            await callback.answer("❌ Ви не маєте доступу до цієї доставки", show_alert=True)
            return

        if order.status != OrderStatus.AWAITING_CONFIRMATION:
            await callback.answer("❌ Доставка не потребує підтвердження", show_alert=True)
            return

        # Confirm delivery
        order = OrderStatusService.confirm_delivery(db, order)

        logger.info(
            "Delivery confirmed | order_id=%s order_number=%s manager_id=%s",
            order.id,
            order.number,
            manager.id,
        )

        # Send notifications
        await NotificationService.notify_delivery_confirmed(bot, order)
        await NotificationService.notify_delivery_confirmed_to_creator(bot, order)

        db.add(order)
        db.commit()

        await callback.message.edit_text(
            f"✅ Доставка підтверджена\n\n📦 {order.number}",
            reply_markup=None
        )
        await callback.answer("✅ Спасибо! Доставка підтверджена.")

    except ValueError as e:
        await callback.answer(f"❌ {str(e)}", show_alert=True)
    finally:
        db.close()


@router.callback_query(lambda callback: callback.data and callback.data.startswith("report_delivery_problem:"), ManagerFilter())
async def report_delivery_problem_callback(callback: CallbackQuery):
    """Manager reports a problem with the delivery."""
    db = SessionLocal()

    try:
        order_id = int(callback.data.split(":", 1)[1])

        manager = ActivationService.get_manager(
            db,
            callback.from_user.id,
        )

        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            await callback.answer("❌ Замовлення не знайдено", show_alert=True)
            return

        # Verify manager is from destination store
        if order.to_store_id != manager.store_id:
            await callback.answer("❌ Ви не маєте доступу до цієї доставки", show_alert=True)
            return

        if order.status != OrderStatus.AWAITING_CONFIRMATION:
            await callback.answer("❌ Доставка не потребує підтвердження", show_alert=True)
            return

        # Report problem
        order = OrderStatusService.report_problem(db, order)

        logger.info(
            "Delivery problem reported | order_id=%s order_number=%s manager_id=%s",
            order.id,
            order.number,
            manager.id,
        )

        # Send notifications
        await NotificationService.notify_delivery_problem_reported(db, bot, order)

        db.add(order)
        db.commit()

        await callback.message.edit_text(
            f"⚠️ Проблема повідомлена адміністратору\n\n📦 {order.number}",
            reply_markup=None
        )
        await callback.answer("✅ Проблема повідомлена. Адміністратор буде в курсі.")

    except ValueError as e:
        await callback.answer(f"❌ {str(e)}", show_alert=True)
    finally:
        db.close()
