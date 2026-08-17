from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.order import Order, OrderStatus
from app.models.user import User


class OrderStatusService:

    @staticmethod
    def _ensure_order_loaded(db: Session, order: Order) -> Order:
        """Ensure all relationships are eagerly loaded before detaching from session."""
        # Access relationships to trigger load while session is active
        _ = order.creator
        _ = order.courier
        _ = order.from_store
        _ = order.to_store
        return order

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
        order.accepted_at = datetime.now()

        db.commit()
        db.refresh(order)
        return OrderStatusService._ensure_order_loaded(db, order)

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
        order.picked_up_at = datetime.now()

        db.commit()
        db.refresh(order)
        return OrderStatusService._ensure_order_loaded(db, order)

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
        return OrderStatusService._ensure_order_loaded(db, order)

    @staticmethod
    def deliver(
        db: Session,
        order: Order,
    ) -> Order:
        """Deprecated: Use mark_awaiting_confirmation instead."""
        if order.status != OrderStatus.DELIVERING:
            raise ValueError(
                "Order cannot be delivered."
            )

        order.status = OrderStatus.DELIVERED
        order.delivered_at = datetime.now()

        db.commit()
        db.refresh(order)
        return OrderStatusService._ensure_order_loaded(db, order)

    @staticmethod
    def mark_awaiting_confirmation(
        db: Session,
        order: Order,
    ) -> Order:
        """Courier marks order as transferred to destination store."""
        if order.status != OrderStatus.DELIVERING:
            raise ValueError(
                "Order cannot be marked as awaiting confirmation."
            )

        order.status = OrderStatus.AWAITING_CONFIRMATION
        order.delivered_at = datetime.now()

        db.commit()
        db.refresh(order)
        return OrderStatusService._ensure_order_loaded(db, order)

    @staticmethod
    def confirm_delivery(
        db: Session,
        order: Order,
    ) -> Order:
        """Manager confirms goods received from courier."""
        if order.status != OrderStatus.AWAITING_CONFIRMATION:
            raise ValueError(
                "Order cannot be confirmed."
            )

        order.status = OrderStatus.COMPLETED
        order.confirmed_at = datetime.now()

        db.commit()
        db.refresh(order)
        return OrderStatusService._ensure_order_loaded(db, order)

    @staticmethod
    def report_problem(
        db: Session,
        order: Order,
    ) -> Order:
        """Manager reports a problem with the delivery."""
        if order.status != OrderStatus.AWAITING_CONFIRMATION:
            raise ValueError(
                "Problem can only be reported for orders awaiting confirmation."
            )

        order.status = OrderStatus.DELIVERY_PROBLEM
        order.problem_reported_at = datetime.now()

        db.commit()
        db.refresh(order)
        return OrderStatusService._ensure_order_loaded(db, order)

    @staticmethod
    def resolve_problem(
        db: Session,
        order: Order,
    ) -> Order:
        """Admin resolves a delivery problem."""
        if order.status != OrderStatus.DELIVERY_PROBLEM:
            raise ValueError(
                "Order is not in problem state."
            )

        order.status = OrderStatus.AWAITING_CONFIRMATION

        db.commit()
        db.refresh(order)
        return OrderStatusService._ensure_order_loaded(db, order)

    @staticmethod
    def force_complete(
        db: Session,
        order: Order,
    ) -> Order:
        """Admin force completes an order (after resolving problem or override)."""
        order.status = OrderStatus.COMPLETED
        order.confirmed_at = datetime.now()

        db.commit()
        db.refresh(order)
        return OrderStatusService._ensure_order_loaded(db, order)

    @staticmethod
    def cancel(
        db: Session,
        order: Order,
    ) -> Order:

        if order.status in [OrderStatus.DELIVERED, OrderStatus.COMPLETED]:
            raise ValueError(
                "Completed order cannot be canceled."
            )

        order.status = OrderStatus.CANCELED

        db.commit()
        db.refresh(order)

        return order