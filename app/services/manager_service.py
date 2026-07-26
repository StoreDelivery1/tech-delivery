from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole
from app.schemas.order import ManagerOrderCreate
from app.services.order_service import OrderService


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

        if manager.store_id is None:
            raise ValueError("Manager is not assigned to a store")

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

        return OrderService.create_order(
            db=db,
            order=data,
            current_user=manager,
        )

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
            .filter(
                Order.from_store_id == manager.store_id,
            )
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

        orders = (
            db.query(Order)
            .filter(
                Order.from_store_id == manager.store_id,
            )
            .all()
        )

        return {
            "total_orders": len(orders),
            "waiting_orders": sum(
                o.status == OrderStatus.WAITING_FOR_COURIER
                for o in orders
            ),
            "in_progress_orders": sum(
                o.status
                in (
                    OrderStatus.ACCEPTED,
                    OrderStatus.PICKED_UP,
                    OrderStatus.DELIVERING,
                )
                for o in orders
            ),
            "delivered_orders": sum(
                o.status == OrderStatus.DELIVERED
                for o in orders
            ),
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