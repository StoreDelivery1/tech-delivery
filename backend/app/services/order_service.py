from sqlalchemy.orm import Session

from app.models.order import Order, OrderPriority, OrderSize, OrderStatus
from app.models.user import User
from app.schemas.order import OrderCreate
from app.services.order_number_service import OrderNumberService
from app.services.order_status_service import OrderStatusService


class OrderService:

    @staticmethod
    def create_order_with_stores(
        db: Session,
        current_user: User,
        from_store_id: int,
        to_store_id: int,
        description: str,
        size: OrderSize | None = None,
        priority: OrderPriority = OrderPriority.NORMAL,
    ) -> Order:
        """Create a regular delivery with an explicit route for product orders."""
        if current_user.store_id is None:
            raise ValueError("Manager has no assigned store.")

        if to_store_id != current_user.store_id:
            raise ValueError("Destination store must be the manager's assigned store.")

        if from_store_id == to_store_id:
            raise ValueError("Source and destination stores must be different.")

        new_order = Order(
            number=OrderNumberService.generate(db),
            from_store_id=from_store_id,
            to_store_id=to_store_id,
            created_by=current_user.id,
            description=description,
            size=size,
            priority=priority,
            status=OrderStatus.WAITING_FOR_COURIER,
        )

        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        return new_order

    @staticmethod
    def create_order(
        db: Session,
        order: OrderCreate,
        current_user: User,
    ) -> Order:

        if current_user.store_id is None:
            raise ValueError(
                "Manager has no assigned store."
            )

        new_order = Order(
            number=OrderNumberService.generate(db),
            from_store_id=current_user.store_id,
            to_store_id=order.to_store_id,
            created_by=current_user.id,
            description=order.description,
            size=order.size,
            priority=order.priority,
            manager_comment=order.manager_comment,
            status=OrderStatus.WAITING_FOR_COURIER,
        )

        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        return new_order

    @staticmethod
    def get_orders(
        db: Session,
    ) -> list[Order]:

        return (
            db.query(Order)
            .order_by(Order.id.desc())
            .all()
        )

    @staticmethod
    def get_order(
        db: Session,
        order_id: int,
    ) -> Order:

        order = db.get(Order, order_id)

        if order is None:
            raise ValueError(
                "Order not found."
            )

        return order

    @staticmethod
    def assign_courier(
        db: Session,
        order_id: int,
        courier_id: int,
    ) -> Order:

        order = OrderService.get_order(
            db,
            order_id,
        )

        courier = db.get(
            User,
            courier_id,
        )

        if courier is None:
            raise ValueError(
                "Courier not found."
            )

        return OrderStatusService.accept(
            db=db,
            order=order,
            courier=courier,
        )

    @staticmethod
    def update_status(
        db: Session,
        order_id: int,
        new_status: OrderStatus,
    ) -> Order:

        order = OrderService.get_order(
            db,
            order_id,
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

        if new_status == OrderStatus.CANCELED:
            return OrderStatusService.cancel(
                db,
                order,
            )

        raise ValueError(
            "Invalid status."
        )

    @staticmethod
    def delete_order(
        db: Session,
        order_id: int,
    ) -> None:

        order = OrderService.get_order(
            db,
            order_id,
        )

        db.delete(order)
        db.commit()