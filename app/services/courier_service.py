from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole
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
            .filter(Order.courier_id == user_id)
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

        return OrderStatusService.accept(
            db=db,
            order=order,
            courier=courier,
        )

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

        if new_status == OrderStatus.DELIVERED:
            return OrderStatusService.deliver(
                db,
                order,
            )

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
        user.last_seen = datetime.now(timezone.utc)

        db.commit()
        db.refresh(user)

        return user