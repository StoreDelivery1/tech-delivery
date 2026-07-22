from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.models.user import User


class CourierService:

    @staticmethod
    def get_profile(
        db: Session,
        user_id: int,
    ) -> User:

        user = db.get(User, user_id)

        if user is None:
            raise ValueError("Courier not found")

        return user

    @staticmethod
    def get_orders(
        db: Session,
        user_id: int,
    ) -> list[Order]:

        return (
            db.query(Order)
            .filter(Order.courier_id == user_id)
            .order_by(Order.id.desc())
            .all()
        )

    @staticmethod
    def get_statistics(
        db: Session,
        user_id: int,
    ) -> dict:

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

        user = db.get(User, user_id)

        if user is None:
            raise ValueError("Courier not found")

        user.is_online = is_online
        user.last_seen = datetime.now(timezone.utc)

        db.commit()
        db.refresh(user)

        return user