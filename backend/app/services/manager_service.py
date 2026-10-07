from sqlalchemy.orm import Session, joinedload

from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole
from app.schemas.order import ManagerOrderCreate
from app.services.order_service import OrderService
from app.services.distribution_service import DistributionService

_ACTIVE_STATUSES = [
    OrderStatus.WAITING_FOR_COURIER,
    OrderStatus.ACCEPTED,
    OrderStatus.PICKED_UP,
    OrderStatus.DELIVERING,
]

_COMPLETED_STATUSES = [
    OrderStatus.DELIVERED,
    OrderStatus.CANCELED,
]

_REQUESTED_ORDER_ACTIVE_STATUSES = [
    OrderStatus.WAITING_FOR_COURIER,
    OrderStatus.ACCEPTED,
    OrderStatus.PICKED_UP,
    OrderStatus.DELIVERING,
    OrderStatus.AWAITING_CONFIRMATION,
    OrderStatus.DELIVERY_PROBLEM,
]


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
    def get_my_created_orders(
        db: Session,
        user_id: int,
    ) -> tuple[list[Order], list[Order]]:
        """Return (active_orders, completed_orders) for orders created by user_id."""
        orders = (
            db.query(Order)
            .filter(Order.created_by == user_id)
            .order_by(Order.id.desc())
            .all()
        )
        active    = [o for o in orders if o.status in _ACTIVE_STATUSES]
        completed = [o for o in orders if o.status in _COMPLETED_STATUSES]
        return active, completed

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

    @staticmethod
    def get_incoming_active_deliveries(
        db: Session,
        user_id: int,
    ) -> list[Order]:
        """Get all active incoming deliveries to manager's store.
        
        Includes statuses: ACCEPTED, PICKED_UP, DELIVERING
        """
        manager = ManagerService.get_profile(db, user_id)

        incoming_active_statuses = [
            OrderStatus.ACCEPTED,
            OrderStatus.PICKED_UP,
            OrderStatus.DELIVERING,
        ]

        return (
            db.query(Order)
            .filter(
                Order.to_store_id == manager.store_id,
                Order.status.in_(incoming_active_statuses),
            )
            .options(
                joinedload(Order.courier),
                joinedload(Order.from_store),
                joinedload(Order.to_store),
            )
            .order_by(Order.id.desc())
            .all()
        )

    @staticmethod
    def _requested_orders_query(db: Session, manager: User):
        return (
            db.query(Order)
            .join(Order.creator)
            .filter(
                Order.from_store_id == manager.store_id,
                Order.to_store_id != manager.store_id,
                User.store_id == Order.to_store_id,
                Order.status.in_(_REQUESTED_ORDER_ACTIVE_STATUSES),
            )
            .options(
                joinedload(Order.from_store),
                joinedload(Order.to_store),
                joinedload(Order.creator).joinedload(User.store),
            )
        )

    @staticmethod
    def get_active_orders_requested_from_store(
        db: Session,
        user_id: int,
    ) -> list[Order]:
        """Return active product requests that other stores placed with this manager's store."""
        manager = ManagerService.get_profile(db, user_id)
        return ManagerService._requested_orders_query(db, manager).order_by(Order.id.desc()).all()

    @staticmethod
    def get_active_order_requested_from_store(
        db: Session,
        user_id: int,
        order_id: int,
    ) -> Order | None:
        """Return one active request only if it is assigned to this manager's store as source."""
        manager = ManagerService.get_profile(db, user_id)
        return ManagerService._requested_orders_query(db, manager).filter(Order.id == order_id).one_or_none()

    @staticmethod
    def get_incoming_deliveries_by_date_range(
        db: Session,
        user_id: int,
        date_range: str,
    ) -> tuple[list[Order], list[Order]]:
        """Get incoming deliveries (active and completed) by date range.
        
        date_range: "today", "week", "month"
        Returns: (active_orders, completed_orders)
        """
        from datetime import datetime, timedelta, timezone

        manager = ManagerService.get_profile(db, user_id)

        now = datetime.now(timezone.utc)
        
        if date_range == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range == "week":
            start_date = now - timedelta(days=7)
        elif date_range == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = None

        query = db.query(Order).filter(Order.to_store_id == manager.store_id)

        if start_date:
            query = query.filter(Order.created_at >= start_date)

        orders = query.order_by(Order.id.desc()).all()

        active = [o for o in orders if o.status in _ACTIVE_STATUSES]
        completed = [o for o in orders if o.status in _COMPLETED_STATUSES]

        return active, completed

    @staticmethod
    def get_incoming_delivery_count(
        db: Session,
        user_id: int,
    ) -> int:
        """Get count of active incoming deliveries."""
        manager = ManagerService.get_profile(db, user_id)

        incoming_active_statuses = [
            OrderStatus.ACCEPTED,
            OrderStatus.PICKED_UP,
            OrderStatus.DELIVERING,
        ]

        return (
            db.query(Order)
            .filter(
                Order.to_store_id == manager.store_id,
                Order.status.in_(incoming_active_statuses),
            )
            .count()
        )