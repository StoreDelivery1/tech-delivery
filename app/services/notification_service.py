import logging
from datetime import datetime

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.bot import bot as _global_bot

logger = logging.getLogger(__name__)


class NotificationService:

    # ── Low-level primitives (global bot singleton) ───────────────────────

    @staticmethod
    async def send_message(
        telegram_id: int,
        text: str,
        **kwargs,
    ) -> bool:
        try:
            await _global_bot.send_message(
                chat_id=telegram_id,
                text=text,
                **kwargs,
            )
            return True

        except TelegramBadRequest:
            return False

        except Exception as exc:
            logger.error("send_message error for %s: %s", telegram_id, exc)
            return False

    @staticmethod
    async def edit_message(
        chat_id: int,
        message_id: int,
        text: str,
        **kwargs,
    ) -> bool:
        try:
            await _global_bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                **kwargs,
            )
            return True

        except TelegramBadRequest:
            return False

        except Exception as exc:
            logger.error("edit_message error for %s/%s: %s", chat_id, message_id, exc)
            return False

    @staticmethod
    async def delete_message(
        chat_id: int,
        message_id: int,
    ) -> bool:
        try:
            await _global_bot.delete_message(
                chat_id=chat_id,
                message_id=message_id,
            )
            return True

        except TelegramBadRequest:
            return False

        except Exception as exc:
            logger.error("delete_message error for %s/%s: %s", chat_id, message_id, exc)
            return False

    # ── Order-status notifications ────────────────────────────────────────

    @staticmethod
    def _build_details_keyboard(order) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📋 Відкрити заявку",
                        callback_data=f"order_details:{order.id}",
                    )
                ]
            ]
        )

    @staticmethod
    def _format_order_message(order, status_label: str, time_str: str) -> str:
        courier_name = order.courier.full_name if order.courier else "—"
        from_store = order.from_store.name if order.from_store else "—"
        to_store = order.to_store.name if order.to_store else "—"
        return (
            f"📦 Заявка №<b>{order.number}</b>\n\n"
            f"📍 Звідки:\n{from_store}\n\n"
            f"📍 Куди:\n{to_store}\n\n"
            f"👤 Кур'єр:\n{courier_name}\n\n"
            f"🟢 Статус:\n{status_label}\n\n"
            f"🕒 {time_str}"
        )

    @staticmethod
    async def _send_message_to_manager(
        bot: Bot,
        order,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> int | None:
        """Send message to manager and return message_id, or None on failure."""
        try:
            manager = order.creator
            if manager is None:
                logger.warning(
                    "Cannot notify manager: order.creator is None | order_id=%s order_number=%s",
                    order.id,
                    order.number,
                )
                return None

            if not manager.telegram_id:
                logger.warning(
                    "Cannot notify manager: telegram_id is None | order_id=%s order_number=%s manager_id=%s",
                    order.id,
                    order.number,
                    manager.id,
                )
                return None

            logger.info(
                "Sending message to manager | order_id=%s order_number=%s manager_id=%s manager_telegram_id=%s",
                order.id,
                order.number,
                manager.id,
                manager.telegram_id,
            )

            message = await bot.send_message(
                chat_id=manager.telegram_id,
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
            )
            logger.info(
                "Message sent to manager | order_id=%s order_number=%s message_id=%s",
                order.id,
                order.number,
                message.message_id,
            )
            return message.message_id

        except TelegramForbiddenError as exc:
            logger.error(
                "Manager blocked the bot | order_id=%s order_number=%s manager_id=%s | %s",
                order.id,
                order.number,
                order.creator.id if order.creator else "unknown",
                exc,
            )
        except TelegramAPIError as exc:
            logger.error(
                "Telegram API error sending message | order_id=%s order_number=%s manager_id=%s | %s",
                order.id,
                order.number,
                order.creator.id if order.creator else "unknown",
                exc,
            )
        except Exception as exc:
            logger.error(
                "Unexpected error sending message | order_id=%s order_number=%s | %s: %s",
                order.id,
                order.number,
                type(exc).__name__,
                exc,
            )
        return None

    @staticmethod
    async def _edit_or_resend_manager_message(
        bot: Bot,
        order,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> None:
        """Edit existing message to manager, or send new one if edit fails."""
        try:
            manager = order.creator
            if manager is None:
                logger.warning(
                    "Cannot update manager notification: order.creator is None | order_id=%s",
                    order.id,
                )
                return

            if not manager.telegram_id:
                logger.warning(
                    "Cannot update manager notification: telegram_id is None | order_id=%s manager_id=%s",
                    order.id,
                    manager.id,
                )
                return

            # Try to edit existing message
            if order.manager_chat_id and order.manager_message_id:
                logger.info(
                    "Attempting to edit manager message | order_id=%s chat_id=%s message_id=%s order_status=%s",
                    order.id,
                    order.manager_chat_id,
                    order.manager_message_id,
                    order.status,
                )
                try:
                    await bot.edit_message_text(
                        chat_id=order.manager_chat_id,
                        message_id=order.manager_message_id,
                        text=text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup,
                    )
                    logger.info(
                        "Manager message edited successfully | order_id=%s message_id=%s",
                        order.id,
                        order.manager_message_id,
                    )
                    return
                except TelegramBadRequest as exc:
                    logger.warning(
                        "Cannot edit manager message (message deleted/not found) | order_id=%s message_id=%s | %s",
                        order.id,
                        order.manager_message_id,
                        exc,
                    )
                    # Fall through to resend

            # Send new message if no existing message or edit failed
            logger.info(
                "Sending new message to manager | order_id=%s manager_id=%s order_status=%s",
                order.id,
                manager.id,
                order.status,
            )
            message = await bot.send_message(
                chat_id=manager.telegram_id,
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
            )
            logger.info(
                "New message sent to manager | order_id=%s new_message_id=%s",
                order.id,
                message.message_id,
            )
            # Update order with new message_id (caller should persist)
            order.manager_chat_id = manager.telegram_id
            order.manager_message_id = message.message_id

        except TelegramForbiddenError as exc:
            logger.error(
                "Manager blocked the bot | order_id=%s manager_id=%s | %s",
                order.id,
                order.creator.id if order.creator else "unknown",
                exc,
            )
        except TelegramAPIError as exc:
            logger.error(
                "Telegram API error updating manager notification | order_id=%s | %s",
                order.id,
                exc,
            )
        except Exception as exc:
            logger.error(
                "Unexpected error updating manager notification | order_id=%s | %s: %s",
                order.id,
                type(exc).__name__,
                exc,
            )

    @staticmethod
    async def notify_order_created(bot: Bot, order) -> int | None:
        """Send initial order notification to manager and return message_id."""
        time_str = order.created_at.strftime("%H:%M")
        text = NotificationService._format_order_message(order, "Нова заявка", time_str)
        keyboard = NotificationService._build_details_keyboard(order)
        return await NotificationService._send_message_to_manager(bot, order, text, keyboard)

    @staticmethod
    async def notify_order_accepted(bot: Bot, order) -> None:
        time_str = (order.accepted_at or datetime.now()).strftime("%H:%M")
        text = NotificationService._format_order_message(order, "Прийнято", time_str)
        keyboard = NotificationService._build_details_keyboard(order)
        await NotificationService._edit_or_resend_manager_message(bot, order, text, keyboard)

    @staticmethod
    async def notify_order_picked_up(bot: Bot, order) -> None:
        time_str = (order.picked_up_at or datetime.now()).strftime("%H:%M")
        text = NotificationService._format_order_message(order, "Кур'єр забрав товар", time_str)
        keyboard = NotificationService._build_details_keyboard(order)
        await NotificationService._edit_or_resend_manager_message(bot, order, text, keyboard)

    @staticmethod
    async def notify_order_delivering(bot: Bot, order) -> None:
        time_str = datetime.now().strftime("%H:%M")
        text = NotificationService._format_order_message(order, "В дорозі", time_str)
        keyboard = NotificationService._build_details_keyboard(order)
        await NotificationService._edit_or_resend_manager_message(bot, order, text, keyboard)

    @staticmethod
    async def notify_order_delivered(bot: Bot, order) -> None:
        time_str = (order.delivered_at or datetime.now()).strftime("%H:%M")
        text = NotificationService._format_order_message(order, "Доставлено", time_str)
        keyboard = NotificationService._build_details_keyboard(order)
        await NotificationService._edit_or_resend_manager_message(bot, order, text, keyboard)

    # ── Incoming Deliveries Notifications ────────────────────────────────────

    @staticmethod
    async def notify_incoming_delivery_status_change(
        db,
        bot: Bot,
        order,
        status_label: str,
    ) -> None:
        """Notify all managers at destination store about delivery status change.
        
        This is for incoming deliveries - notifies all managers at the destination store,
        not just the creator of the order.
        """
        if order.to_store is None:
            return

        from app.models.user import User, UserRole

        # Get all managers assigned to destination store
        managers = (
            db.query(User)
            .filter(
                User.store_id == order.to_store_id,
                User.role == UserRole.MANAGER,
            )
            .all()
        )

        if not managers:
            return

        courier_name = order.courier.full_name if order.courier else "—"
        to_store = order.to_store.name if order.to_store else "—"

        text = (
            f"🔔 <b>Оновлення доставки</b>\n\n"
            f"📦 Номер: <b>{order.number}</b>\n"
            f"👤 Курьєр: <b>{courier_name}</b>\n"
            f"🏪 Магазин: <b>{to_store}</b>\n"
            f"📍 Статус: <b>{status_label}</b>"
        )

        keyboard = NotificationService._build_details_keyboard(order)

        # Send to all managers
        for manager in managers:
            try:
                await bot.send_message(
                    chat_id=manager.telegram_id,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
            except Exception as exc:
                logger.error(
                    "Failed to notify manager about incoming delivery | manager_id=%s order_id=%s | %s",
                    manager.id,
                    order.id,
                    exc,
                )

    @staticmethod
    async def notify_incoming_delivery_accepted(db, bot: Bot, order) -> None:
        """Notify managers at destination store - delivery accepted."""
        await NotificationService.notify_incoming_delivery_status_change(
            db, bot, order, "✅ Прийнято"
        )

    @staticmethod
    async def notify_incoming_delivery_picked_up(db, bot: Bot, order) -> None:
        """Notify managers at destination store - delivery picked up."""
        await NotificationService.notify_incoming_delivery_status_change(
            db, bot, order, "📦 Забрано"
        )

    @staticmethod
    async def notify_incoming_delivery_in_transit(db, bot: Bot, order) -> None:
        """Notify managers at destination store - delivery in transit."""
        await NotificationService.notify_incoming_delivery_status_change(
            db, bot, order, "🚚 В дорозі"
        )

    @staticmethod
    async def notify_incoming_delivery_arrived(db, bot: Bot, order) -> None:
        """Notify managers at destination store - delivery arrived."""
        if order.to_store is None:
            return

        from app.models.user import User, UserRole

        managers = (
            db.query(User)
            .filter(
                User.store_id == order.to_store_id,
                User.role == UserRole.MANAGER,
            )
            .all()
        )

        if not managers:
            return

        courier_name = order.courier.full_name if order.courier else "—"
        to_store = order.to_store.name if order.to_store else "—"

        text = (
            f"✅ <b>Товар прибув</b>\n\n"
            f"📦 Номер: <b>{order.number}</b>\n"
            f"👤 Курьєр: <b>{courier_name}</b>\n"
            f"🏪 Магазин: <b>{to_store}</b>\n"
            f"📍 Статус: <b>Доставлено</b>"
        )

        keyboard = NotificationService._build_details_keyboard(order)

        # Send to all managers
        for manager in managers:
            try:
                await bot.send_message(
                    chat_id=manager.telegram_id,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
            except Exception as exc:
                logger.error(
                    "Failed to notify manager about incoming delivery arrival | manager_id=%s order_id=%s | %s",
                    manager.id,
                    order.id,
                    exc,
                )

    # ── Delivery Confirmation Workflow Notifications ──────────────────────────

    @staticmethod
    async def notify_courier_goods_transferred(bot: Bot, order) -> None:
        """Notify courier that order status changed to AWAITING_CONFIRMATION."""
        if order.courier is None or not order.courier.telegram_id:
            return

        text = (
            f"📍 <b>Статус оновлено</b>\n\n"
            f"📦 Заявка: <b>{order.number}</b>\n"
            f"🏪 Магазин призначення: <b>{order.to_store.name if order.to_store else '—'}</b>\n"
            f"✅ <b>Товар передано магазину</b>\n\n"
            f"Очікуємо підтвердження від магазину."
        )

        try:
            await bot.send_message(
                chat_id=order.courier.telegram_id,
                text=text,
                parse_mode=ParseMode.HTML,
            )
        except Exception as exc:
            logger.error(
                "Failed to notify courier about goods transfer | courier_id=%s order_id=%s | %s",
                order.courier.id,
                order.id,
                exc,
            )

    @staticmethod
    async def notify_delivery_confirmation_request(
        db,
        bot: Bot,
        order,
    ) -> None:
        """Notify all managers at destination store to confirm delivery."""
        if order.to_store is None or order.courier is None:
            return

        from app.models.user import User, UserRole, UserStatus

        managers = (
            db.query(User)
            .filter(
                User.store_id == order.to_store_id,
                User.role == UserRole.MANAGER,
                User.status == UserStatus.ACTIVE,
                User.telegram_id.isnot(None),
            )
            .all()
        )

        if not managers:
            return

        courier_name = order.courier.full_name if order.courier else "—"
        from_store = order.from_store.name if order.from_store else "—"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Підтвердити отримання",
                        callback_data=f"confirm_delivery:{order.id}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="⚠️ Повідомити про проблему",
                        callback_data=f"report_delivery_problem:{order.id}",
                    ),
                ],
            ]
        )

        text = (
            f"📦 <b>Доставка прибула</b>\n\n"
            f"📦 Номер: <b>{order.number}</b>\n"
            f"📍 Звідки: <b>{from_store}</b>\n"
            f"👤 Кур'єр: <b>{courier_name}</b>\n\n"
            f"🔔 <b>Будь ласка, підтвердіть отримання товару.</b>"
        )

        # Send to all destination managers
        for manager in managers:
            if manager.telegram_id == order.courier.telegram_id:
                logger.warning(
                    "Skipping delivery confirmation recipient with courier Telegram ID | order_id=%s manager_id=%s telegram_id=%s",
                    order.id,
                    manager.id,
                    manager.telegram_id,
                )
                continue

            try:
                await bot.send_message(
                    chat_id=manager.telegram_id,
                    text=text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard,
                )
            except Exception as exc:
                logger.error(
                    "Failed to send delivery confirmation request | manager_id=%s order_id=%s | %s",
                    manager.id,
                    order.id,
                    exc,
                )

    @staticmethod
    async def notify_delivery_confirmed(bot: Bot, order) -> None:
        """Notify courier that delivery was confirmed by destination store."""
        if order.courier is None or not order.courier.telegram_id:
            return

        text = (
            f"✅ <b>Доставка підтверджена</b>\n\n"
            f"📦 Заявка: <b>{order.number}</b>\n"
            f"🏪 Магазин призначення: <b>{order.to_store.name if order.to_store else '—'}</b>\n\n"
            f"Магазин підтвердив отримання товару."
        )

        try:
            await bot.send_message(
                chat_id=order.courier.telegram_id,
                text=text,
                parse_mode=ParseMode.HTML,
            )
        except Exception as exc:
            logger.error(
                "Failed to notify courier about delivery confirmation | courier_id=%s order_id=%s | %s",
                order.courier.id,
                order.id,
                exc,
            )

    @staticmethod
    async def notify_delivery_confirmed_to_creator(bot: Bot, order) -> None:
        """Notify order creator that destination store confirmed delivery."""
        if order.creator is None or not order.creator.telegram_id:
            return

        text = (
            f"✅ <b>Магазин підтвердив отримання</b>\n\n"
            f"📦 Заявка: <b>{order.number}</b>\n"
            f"🏪 Магазин призначення: <b>{order.to_store.name if order.to_store else '—'}</b>\n\n"
            f"Магазин підтвердив, що товар було отримано."
        )

        try:
            await bot.send_message(
                chat_id=order.creator.telegram_id,
                text=text,
                parse_mode=ParseMode.HTML,
            )
        except Exception as exc:
            logger.error(
                "Failed to notify creator about delivery confirmation | creator_id=%s order_id=%s | %s",
                order.creator.id,
                order.id,
                exc,
            )

    @staticmethod
    async def notify_delivery_problem_reported(
        db,
        bot: Bot,
        order,
    ) -> None:
        """Notify courier and admin when manager reports a delivery problem."""
        # Notify courier
        if order.courier and order.courier.telegram_id:
            text = (
                f"⚠️ <b>Проблема з доставкою</b>\n\n"
                f"📦 Заявка: <b>{order.number}</b>\n"
                f"🏪 Магазин: <b>{order.to_store.name if order.to_store else '—'}</b>\n\n"
                f"Магазин призначення повідомив про проблему з доставкою."
            )

            try:
                await bot.send_message(
                    chat_id=order.courier.telegram_id,
                    text=text,
                    parse_mode=ParseMode.HTML,
                )
            except Exception as exc:
                logger.error(
                    "Failed to notify courier about delivery problem | courier_id=%s order_id=%s | %s",
                    order.courier.id,
                    order.id,
                    exc,
                )

        # Notify order creator
        if order.creator and order.creator.telegram_id:
            text = (
                f"⚠️ <b>Доставка потребує уваги</b>\n\n"
                f"📦 Заявка: <b>{order.number}</b>\n"
                f"🏪 Магазин: <b>{order.to_store.name if order.to_store else '—'}</b>\n\n"
                f"Магазин повідомив про проблему при доставці товару."
            )

            try:
                await bot.send_message(
                    chat_id=order.creator.telegram_id,
                    text=text,
                    parse_mode=ParseMode.HTML,
                )
            except Exception as exc:
                logger.error(
                    "Failed to notify creator about delivery problem | creator_id=%s order_id=%s | %s",
                    order.creator.id,
                    order.id,
                    exc,
                )

        # Notify admins
        from app.models.user import User, UserRole

        admins = db.query(User).filter(User.role == UserRole.ADMIN).all()

        if admins:
            courier_name = order.courier.full_name if order.courier else "—"
            creator_name = order.creator.full_name if order.creator else "—"
            from_store = order.from_store.name if order.from_store else "—"
            to_store = order.to_store.name if order.to_store else "—"

            text = (
                f"🚨 <b>Конфлікт доставки</b>\n\n"
                f"📦 Номер замовлення: <b>{order.number}</b>\n"
                f"👤 Кур'єр: <b>{courier_name}</b>\n"
                f"📍 Звідки: <b>{from_store}</b>\n"
                f"📍 Куди: <b>{to_store}</b>\n"
                f"👤 Менеджер (створювач): <b>{creator_name}</b>\n\n"
                f"⚠️ <b>Магазин повідомив про проблему</b>\n\n"
                f"Статус: Очікує розгляду адміністратора"
            )

            for admin in admins:
                try:
                    await bot.send_message(
                        chat_id=admin.telegram_id,
                        text=text,
                        parse_mode=ParseMode.HTML,
                    )
                except Exception as exc:
                    logger.error(
                        "Failed to notify admin about delivery problem | admin_id=%s order_id=%s | %s",
                        admin.id,
                        order.id,
                        exc,
                    )