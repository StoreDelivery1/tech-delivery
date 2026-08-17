import logging

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.models.user import User, CourierAvailability

logger = logging.getLogger(__name__)


class DistributionService:
    """Smart distribution of orders to available couriers.
    
    Handles:
    - Distributing new orders to all AVAILABLE couriers
    - Distributing next waiting order to newly available courier
    - Multiple courier acceptance (first wins, others get rejection)
    """

    @staticmethod
    def _format_order_offer(order) -> str:
        """Format order for telegram inline offer."""
        from_store = order.from_store.name if order.from_store else "—"
        to_store = order.to_store.name if order.to_store else "—"
        return (
            f"📦 Нова заявка №<b>{order.number}</b>\n\n"
            f"📍 {from_store} → {to_store}\n"
            f"📝 {order.description}"
        )

    @staticmethod
    def _build_accept_keyboard(order_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text="✅ Прийняти",
                    callback_data=f"accept:{order_id}",
                )
            ]]
        )

    @staticmethod
    def get_available_couriers(db: Session) -> list[User]:
        """Get all couriers currently AVAILABLE (not OFFLINE or BUSY)."""
        return (
            db.query(User)
            .filter(
                User.role.in_(['COURIER']),
                User.availability == CourierAvailability.AVAILABLE,
                User.telegram_id.isnot(None),
            )
            .all()
        )

    @staticmethod
    def get_next_waiting_order(db: Session) -> Order | None:
        """Get oldest waiting order (status=WAITING_FOR_COURIER, no courier assigned)."""
        return (
            db.query(Order)
            .filter(
                Order.status == OrderStatus.WAITING_FOR_COURIER,
                Order.courier_id.is_(None),
            )
            .order_by(Order.created_at)
            .first()
        )

    @staticmethod
    async def distribute_order(
        bot: Bot,
        db: Session,
        order: Order,
        manager_telegram_id: int,
    ) -> bool:
        """
        Distribute order to all AVAILABLE couriers.
        
        Returns True if distributed to at least one courier, False if no couriers available.
        """
        couriers = DistributionService.get_available_couriers(db)

        if not couriers:
            logger.info("No AVAILABLE couriers for order %s", order.number)
            return False

        text = DistributionService._format_order_offer(order)
        keyboard = DistributionService._build_accept_keyboard(order.id)

        # Send to each courier
        for courier in couriers:
            try:
                await bot.send_message(
                    chat_id=courier.telegram_id,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
                logger.info("Sent order %s to courier %s", order.number, courier.id)
            except Exception as exc:
                logger.error(
                    "Failed to send order %s to courier %s: %s",
                    order.number,
                    courier.id,
                    exc,
                )

        return True

    @staticmethod
    async def distribute_next_waiting_order(
        bot: Bot,
        db: Session,
        courier: User,
    ) -> bool:
        """
        Find the oldest waiting order and send it to the courier.
        
        Called when:
        - Courier starts shift (OFFLINE → AVAILABLE)
        - Courier becomes available after delivery (BUSY → AVAILABLE)
        
        Returns True if an order was found and sent, False otherwise.
        """
        order = DistributionService.get_next_waiting_order(db)

        if not order:
            logger.info("No waiting orders for courier %s", courier.id)
            return False

        if not courier.telegram_id:
            logger.warning("Courier %s has no telegram_id", courier.id)
            return False

        text = DistributionService._format_order_offer(order)
        keyboard = DistributionService._build_accept_keyboard(order.id)

        try:
            await bot.send_message(
                chat_id=courier.telegram_id,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            logger.info(
                "Sent waiting order %s to newly available courier %s",
                order.number,
                courier.id,
            )
            return True
        except Exception as exc:
            logger.error(
                "Failed to send waiting order %s to courier %s: %s",
                order.number,
                courier.id,
                exc,
            )
            return False
