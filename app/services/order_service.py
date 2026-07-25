from datetime import datetime

from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.models.user import User


class OrderService:

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
            raise ValueError("Order not found")

        return order

    @staticmethod
    def accept_order(
        db: Session,
        order: Order,
        courier: User,
    ) -> Order:

        if order.status != OrderStatus.WAITING_FOR_COURIER:
            raise ValueError(
                "Order cannot be accepted"
            )

        order.status = OrderStatus.ACCEPTED
        order.courier_id = courier.id
        order.accepted_at = datetime.utcnow()

        db.commit()
        db.refresh(order)

        return order

    @staticmethod
    def pickup_order(
        db: Session,
        order: Order,
    ) -> Order:

        if order.status != OrderStatus.ACCEPTED:
            raise ValueError(
                "Order cannot be picked up"
            )

        order.status = OrderStatus.PICKED_UP
        order.picked_up_at = datetime.utcnow()

        db.commit()
        db.refresh(order)

        return order

    @staticmethod
    def start_delivery(
        db: Session,
        order: Order,
    ) -> Order:

        if order.status != OrderStatus.PICKED_UP:
            raise ValueError(
                "Order cannot be started"
            )

        order.status = OrderStatus.DELIVERING

        db.commit()
        db.refresh(order)

        return order

    @staticmethod
    def deliver_order(
        db: Session,
        order: Order,
    ) -> Order:

        if order.status != OrderStatus.DELIVERING:
            raise ValueError(
                "Order cannot be delivered"
            )

        order.status = OrderStatus.DELIVERED
        order.delivered_at = datetime.utcnow()

        db.commit()
        db.refresh(order)

        return order

    @staticmethod
    def cancel_order(
        db: Session,
        order: Order,
    ) -> Order:

        if order.status == OrderStatus.DELIVERED:
            raise ValueError(
                "Delivered order cannot be canceled"
            )

        order.status = OrderStatus.CANCELED

        db.commit()
        db.refresh(order)

        return order

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