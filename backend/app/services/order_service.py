from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.schemas.order import OrderCreate


class OrderService:

    @staticmethod
    def create_order(
        db: Session,
        order: OrderCreate,
    ) -> Order:
        new_order = Order(
            **order.model_dump(),
            status=OrderStatus.CREATED,
        )

        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        return new_order

    @staticmethod
    def get_orders(
        db: Session,
    ) -> list[Order]:
        return db.query(Order).all()

    @staticmethod
    def update_status(
        db: Session,
        order_id: int,
        new_status: OrderStatus,
    ) -> Order:

        order = db.get(Order, order_id)

        if order is None:
            raise ValueError("Order not found")

        allowed_transitions = {
            OrderStatus.CREATED: [OrderStatus.ACCEPTED],
            OrderStatus.ACCEPTED: [OrderStatus.PICKED_UP],
            OrderStatus.PICKED_UP: [OrderStatus.DELIVERING],
            OrderStatus.DELIVERING: [OrderStatus.DELIVERED],
            OrderStatus.DELIVERED: [],
            OrderStatus.CANCELED: [],
        }

        if new_status not in allowed_transitions[order.status]:
            raise ValueError(
                f"Cannot change status from {order.status} to {new_status}"
            )

        order.status = new_status

        db.commit()
        db.refresh(order)

        return order