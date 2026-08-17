from datetime import datetime

from sqlalchemy.orm import Session

from app.models.order import Order


class OrderNumberService:

    @staticmethod
    def generate(
        db: Session,
    ) -> str:

        year = datetime.now().year

        last_order = (
            db.query(Order)
            .order_by(Order.id.desc())
            .first()
        )

        if last_order is None:
            number = 1
        else:
            try:
                number = int(
                    last_order.number.split("-")[1]
                ) + 1
            except Exception:
                number = last_order.id + 1

        return f"{year}-{number:06d}"