from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole


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

        order = db.get(Order, order_id)

        if order is None:
            raise ValueError("Order not found")

        if order.status != OrderStatus.WAITING_FOR_COURIER:
            raise ValueError("Order is not available")

        if order.courier_id is not None:
            raise ValueError("Order already accepted")

        order.courier_id = courier.id
        order.status = OrderStatus.ACCEPTED
        order.accepted_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(order)

        return order

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

        order = db.get(Order, order_id)

        if order is None:
            raise ValueError("Order not found")

        if order.courier_id != courier_id:
            raise ValueError("This order is assigned to another courier")

        allowed = {
            OrderStatus.ACCEPTED: OrderStatus.PICKED_UP,
            OrderStatus.PICKED_UP: OrderStatus.DELIVERING,
            OrderStatus.DELIVERING: OrderStatus.DELIVERED,
        }

        expected = allowed.get(order.status)

        if expected != new_status:
            raise ValueError(
                f"Cannot change status from {order.status} to {new_status}"
            )

        order.status = new_status

        now = datetime.now(timezone.utc)

        if new_status == OrderStatus.PICKED_UP:
            order.picked_up_at = now

        if new_status == OrderStatus.DELIVERED:
            order.delivered_at = now

        db.commit()
        db.refresh(order)

        return order

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