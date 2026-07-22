import enum

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class OrderStatus(str, enum.Enum):
    CREATED = "CREATED"
    ACCEPTED = "ACCEPTED"
    PICKED_UP = "PICKED_UP"
    DELIVERING = "DELIVERING"
    DELIVERED = "DELIVERED"
    CANCELED = "CANCELED"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id"),
    )

    customer_name: Mapped[str] = mapped_column(
        String(255),
    )

    customer_phone: Mapped[str] = mapped_column(
        String(30),
    )

    delivery_address: Mapped[str] = mapped_column(
        String(255),
    )

    status: Mapped[OrderStatus] = mapped_column(
        Enum(
            OrderStatus,
            native_enum=False,
            validate_strings=True,
        ),
        default=OrderStatus.CREATED,
    )

    store: Mapped["Store"] = relationship(
        back_populates="orders",
    )