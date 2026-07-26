from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus


class OrderQueryService:

    @staticmethod
    def get_by_id(
        db: Session,
        order_id: int,
    ) -> Order | None:

        return db.get(Order, order_id)

    @staticmethod
    def get_open_orders(
        db: Session,
    ) -> list[Order]:

        return (
            db.query(Order)
            .filter(
                Order.status == OrderStatus.WAITING_FOR_COURIER,
            )
            .order_by(Order.created_at)
            .all()
        )

    @staticmethod
    def get_by_courier(
        db: Session,
        courier_id: int,
    ) -> list[Order]:

        return (
            db.query(Order)
            .filter(
                Order.courier_id == courier_id,
            )
            .order_by(Order.id.desc())
            .all()
        )

    @staticmethod
    def get_by_store(
        db: Session,
        store_id: int,
    ) -> list[Order]:

        return (
            db.query(Order)
            .filter(
                Order.from_store_id == store_id,
            )
            .order_by(Order.id.desc())
            .all()
        )

    @staticmethod
    def get_active_by_courier(
        db: Session,
        courier_id: int,
    ) -> list[Order]:

        return (
            db.query(Order)
            .filter(
                Order.courier_id == courier_id,
                Order.status != OrderStatus.DELIVERED,
                Order.status != OrderStatus.CANCELED,
            )
            .order_by(Order.id.desc())
            .all()
        )

    @staticmethod
    def get_delivered_by_courier(
        db: Session,
        courier_id: int,
    ) -> list[Order]:

        return (
            db.query(Order)
            .filter(
                Order.courier_id == courier_id,
                Order.status == OrderStatus.DELIVERED,
            )
            .order_by(Order.id.desc())
            .all()
        )