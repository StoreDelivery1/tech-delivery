from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole
from app.schemas.order import ManagerOrderCreate


class ManagerService:

    @staticmethod
    def get_profile(
        db: Session,
        user_id: int,
    ) -> User:

        manager = db.get(User, user_id)

        if manager is None:
            raise ValueError("Manager not found")

        if manager.role != UserRole.MANAGER:
            raise ValueError("User is not a manager")

        return manager

    @staticmethod
    def create_order(
        db: Session,
        user_id: int,
        data: ManagerOrderCreate,
    ) -> Order:

        manager = ManagerService.get_profile(
            db,
            user_id,
        )

        order = Order(
            store_id=manager.store_id,
            created_by=manager.id,
            customer_name=data.customer_name,
            customer_phone=data.customer_phone,
            delivery_address=data.delivery_address,
            status=OrderStatus.CREATED,
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        return order

    @staticmethod
    def get_orders(
        db: Session,
        user_id: int,
    ) -> list[Order]:

        manager = ManagerService.get_profile(
            db,
            user_id,
        )

        return (
            db.query(Order)
            .filter(Order.store_id == manager.store_id)
            .order_by(Order.id.desc())
            .all()
        )

    @staticmethod
    def get_statistics(
        db: Session,
        user_id: int,
    ) -> dict:

        manager = ManagerService.get_profile(
            db,
            user_id,
        )

        total_orders = (
            db.query(Order)
            .filter(Order.store_id == manager.store_id)
            .count()
        )

        active_orders = (
            db.query(Order)
            .filter(
                Order.store_id == manager.store_id,
                Order.status != OrderStatus.DELIVERED,
            )
            .count()
        )

        delivered_orders = (
            db.query(Order)
            .filter(
                Order.store_id == manager.store_id,
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
    def get_couriers(
        db: Session,
        user_id: int,
    ) -> list[User]:

        manager = ManagerService.get_profile(
            db,
            user_id,
        )

        return (
            db.query(User)
            .filter(
                User.store_id == manager.store_id,
                User.role == UserRole.COURIER,
            )
            .order_by(User.full_name)
            .all()
        )