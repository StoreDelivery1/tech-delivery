from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.models.store import Store
from app.models.user import User, UserRole


class AdminService:

    @staticmethod
    def get_dashboard(
        db: Session,
    ) -> dict:

        stores = db.query(Store).count()

        managers = (
            db.query(User)
            .filter(User.role == UserRole.MANAGER)
            .count()
        )

        couriers = (
            db.query(User)
            .filter(User.role == UserRole.COURIER)
            .count()
        )

        online_couriers = (
            db.query(User)
            .filter(
                User.role == UserRole.COURIER,
                User.is_online.is_(True),
            )
            .count()
        )

        active_orders = (
            db.query(Order)
            .filter(
                Order.status != OrderStatus.DELIVERED,
                Order.status != OrderStatus.CANCELED,
            )
            .count()
        )

        delivered_today = (
            db.query(Order)
            .filter(
                Order.status == OrderStatus.DELIVERED,
                func.date(Order.delivered_at) == date.today(),
            )
            .count()
        )

        return {
            "stores": stores,
            "managers": managers,
            "couriers": couriers,
            "online_couriers": online_couriers,
            "active_orders": active_orders,
            "delivered_today": delivered_today,
        }