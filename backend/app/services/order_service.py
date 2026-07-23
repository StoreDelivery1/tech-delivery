from sqlalchemy.orm import Session

from app.models.order import Order


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