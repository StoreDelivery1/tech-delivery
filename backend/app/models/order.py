import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class OrderPriority(str, enum.Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class OrderStatus(str, enum.Enum):
    WAITING_FOR_COURIER = "WAITING_FOR_COURIER"
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

    from_store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id"),
    )

    to_store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id"),
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
    )

    courier_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
    )

    estimated_weight: Mapped[float] = mapped_column(
        Float,
    )

    priority: Mapped[OrderPriority] = mapped_column(
        Enum(
            OrderPriority,
            native_enum=False,
            validate_strings=True,
        ),
        default=OrderPriority.NORMAL,
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[OrderStatus] = mapped_column(
        Enum(
            OrderStatus,
            native_enum=False,
            validate_strings=True,
        ),
        default=OrderStatus.WAITING_FOR_COURIER,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    picked_up_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    from_store = relationship(
        "Store",
        foreign_keys=[from_store_id],
        back_populates="outgoing_orders",
    )

    to_store = relationship(
        "Store",
        foreign_keys=[to_store_id],
        back_populates="incoming_orders",
    )

    creator = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="created_orders",
    )

    courier = relationship(
        "User",
        foreign_keys=[courier_id],
        back_populates="courier_orders",
    )