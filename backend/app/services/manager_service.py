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

        order = Order(
            number="",
            from_store_id=manager.store_id,
            to_store_id=data.to_store_id,
            created_by=manager.id,
            description=data.description,
            estimated_weight=data.estimated_weight,
            priority=data.priority,
            manager_comment=data.manager_comment,
            status=OrderStatus.WAITING_FOR_COURIER,
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        order.number = f"TD-{order.id:06d}"

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
            .filter(Order.from_store_id == manager.store_id)
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
            .filter(Order.from_store_id == manager.store_id)
            .all()
        )

        return {
            "total_orders": len(orders),
            "waiting_orders": len(
                [
                    o
                    for o in orders
                    if o.status == OrderStatus.WAITING_FOR_COURIER
                ]
            ),
            "in_progress_orders": len(
                [
                    o
                    for o in orders
                    if o.status
                    in (
                        OrderStatus.ACCEPTED,
                        OrderStatus.PICKED_UP,
                        OrderStatus.DELIVERING,
                    )
                ]
            ),
            "delivered_orders": len(
                [
                    o
                    for o in orders
                    if o.status == OrderStatus.DELIVERED
                ]
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