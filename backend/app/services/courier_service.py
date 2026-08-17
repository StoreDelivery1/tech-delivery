from datetime import datetime

from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole, CourierAvailability
from app.services.order_service import OrderService
from app.services.order_status_service import OrderStatusService


class CourierService:

    @staticmethod
    def get_profile(
        db: Session,
        user_id: int,
    ) -> User:

        user = db.get(User, user_id)

        if user is None:
            raise ValueError("Courier not found")

        if user.role != UserRole.COURIER:
            raise ValueError("User is not a courier")

        return user

    @staticmethod
    def get_open_orders(
        db: Session,
    ) -> list[Order]:

        return (
            db.query(Order)
            .filter(
                Order.status == OrderStatus.WAITING_FOR_COURIER,
            )
            .order_by(Order.created_at)
            .all()
        )

    @staticmethod
    def get_orders(
        db: Session,
        user_id: int,
    ) -> list[Order]:

        CourierService.get_profile(
            db,
            user_id,
        )

        return (
            db.query(Order)
            .filter(
                Order.courier_id == user_id,
                Order.status.in_(
                    [
                        OrderStatus.ACCEPTED,
                        OrderStatus.PICKED_UP,
                        OrderStatus.DELIVERING,
                    ]
                ),
            )
            .order_by(Order.id.desc())
            .all()
        )

    @staticmethod
    def accept_order(
        db: Session,
        order_id: int,
        courier_id: int,
    ) -> Order:

        courier = CourierService.get_profile(
            db,
            courier_id,
        )

        order = OrderService.get_order(
            db,
            order_id,
        )

        order = OrderStatusService.accept(
            db=db,
            order=order,
            courier=courier,
        )

        # Auto-transition: AVAILABLE → BUSY
        if courier.availability == CourierAvailability.AVAILABLE:
            CourierService.set_busy(db, courier_id)

        return order

    @staticmethod
    def start_shift(db: Session, courier_id: int) -> User:
        """Start shift: OFFLINE → AVAILABLE."""
        courier = CourierService.get_profile(db, courier_id)

        if courier.availability == CourierAvailability.AVAILABLE:
            raise ValueError("Зміна вже розпочата")

        courier.availability = CourierAvailability.AVAILABLE
        db.commit()
        db.refresh(courier)
        return courier

    @staticmethod
    def end_shift(db: Session, courier_id: int) -> User:
        """End shift: AVAILABLE → OFFLINE. Fails if courier has active orders."""
        courier = CourierService.get_profile(db, courier_id)

        if courier.availability == CourierAvailability.OFFLINE:
            raise ValueError("Зміна вже завершена")

        # Check for active orders
        active_orders = (
            db.query(Order)
            .filter(
                Order.courier_id == courier_id,
                Order.status.in_([
                    OrderStatus.ACCEPTED,
                    OrderStatus.PICKED_UP,
                    OrderStatus.DELIVERING,
                ]),
            )
            .count()
        )

        if active_orders > 0:
            raise ValueError(
                "Неможливо завершити зміну. Спочатку завершіть активну доставку."
            )

        courier.availability = CourierAvailability.OFFLINE
        db.commit()
        db.refresh(courier)
        return courier

    @staticmethod
    def set_busy(db: Session, courier_id: int) -> User:
        """Set courier to BUSY (internal use only)."""
        courier = db.get(User, courier_id)
        if courier is None:
            raise ValueError("Courier not found")
        courier.availability = CourierAvailability.BUSY
        db.commit()
        db.refresh(courier)
        return courier

    @staticmethod
    def set_available(db: Session, courier_id: int) -> User:
        """Set courier to AVAILABLE. Called after order delivery if shift is ongoing."""
        courier = db.get(User, courier_id)
        if courier is None:
            raise ValueError("Courier not found")

        # Only set AVAILABLE if courier is currently BUSY and has no other active orders
        if courier.availability == CourierAvailability.BUSY:
            active_orders = (
                db.query(Order)
                .filter(
                    Order.courier_id == courier_id,
                    Order.status.in_([
                        OrderStatus.ACCEPTED,
                        OrderStatus.PICKED_UP,
                        OrderStatus.DELIVERING,
                    ]),
                )
                .count()
            )
            if active_orders == 0:
                courier.availability = CourierAvailability.AVAILABLE
                db.commit()

        db.refresh(courier)
        return courier

    @staticmethod
    def change_status(
        db: Session,
        order_id: int,
        courier_id: int,
        new_status: OrderStatus,
    ) -> Order:

        CourierService.get_profile(
            db,
            courier_id,
        )

        order = OrderService.get_order(
            db,
            order_id,
        )

        if order.courier_id != courier_id:
            raise ValueError(
                "This order belongs to another courier."
            )

        if new_status == OrderStatus.PICKED_UP:
            return OrderStatusService.pickup(
                db,
                order,
            )

        if new_status == OrderStatus.DELIVERING:
            return OrderStatusService.start_delivery(
                db,
                order,
            )

        if new_status == OrderStatus.AWAITING_CONFIRMATION:
            order = OrderStatusService.mark_awaiting_confirmation(
                db,
                order,
            )
            # Courier is free after goods are transferred to destination store.
            CourierService.set_available(db, courier_id)
            return order

        if new_status == OrderStatus.DELIVERED:
            order = OrderStatusService.deliver(
                db,
                order,
            )
            # Auto-transition: BUSY → AVAILABLE (if no other active orders)
            CourierService.set_available(db, courier_id)
            return order

        raise ValueError("Invalid status.")

    @staticmethod
    def get_statistics(
        db: Session,
        user_id: int,
    ) -> dict:

        CourierService.get_profile(
            db,
            user_id,
        )

        total_orders = (
            db.query(Order)
            .filter(Order.courier_id == user_id)
            .count()
        )

        active_orders = (
            db.query(Order)
            .filter(
                Order.courier_id == user_id,
                Order.status != OrderStatus.DELIVERED,
                Order.status != OrderStatus.CANCELED,
            )
            .count()
        )

        delivered_orders = (
            db.query(Order)
            .filter(
                Order.courier_id == user_id,
                Order.status == OrderStatus.DELIVERED,
            )
            .count()
        )

        return {
            "total_orders": total_orders,
            "active_orders": active_orders,
            "delivered_orders": delivered_orders,
        }

    @staticmethod
    def update_online_status(
        db: Session,
        user_id: int,
        is_online: bool,
    ) -> User:

        user = CourierService.get_profile(
            db,
            user_id,
        )

        user.is_online = is_online
        user.last_seen = datetime.now()

        db.commit()
        db.refresh(user)

        return user