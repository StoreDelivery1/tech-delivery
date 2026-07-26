from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.models.user import User


class OrderStatusService:

    @staticmethod
    def accept(
        db: Session,
        order: Order,
        courier: User,
    ) -> Order:

        if order.status != OrderStatus.WAITING_FOR_COURIER:
            raise ValueError(
                "Order cannot be accepted."
            )

        order.status = OrderStatus.ACCEPTED
        order.courier_id = courier.id
        order.accepted_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(order)

        return order

    @staticmethod
    def pickup(
        db: Session,
        order: Order,
    ) -> Order:

        if order.status != OrderStatus.ACCEPTED:
            raise ValueError(
                "Order cannot be picked up."
            )

        order.status = OrderStatus.PICKED_UP
        order.picked_up_at = datetime.now(timezone.utc)

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
                "Order cannot start delivery."
            )

        order.status = OrderStatus.DELIVERING

        db.commit()
        db.refresh(order)

        return order

    @staticmethod
    def deliver(
        db: Session,
        order: Order,
    ) -> Order:

        if order.status != OrderStatus.DELIVERING:
            raise ValueError(
                "Order cannot be delivered."
            )

        order.status = OrderStatus.DELIVERED
        order.delivered_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(order)

        return order

    @staticmethod
    def cancel(
        db: Session,
        order: Order,
    ) -> Order:

        if order.status == OrderStatus.DELIVERED:
            raise ValueError(
                "Delivered order cannot be canceled."
            )

        order.status = OrderStatus.CANCELED

        db.commit()
        db.refresh(order)

        return order