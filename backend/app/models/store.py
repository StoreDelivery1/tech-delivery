import enum

from sqlalchemy import Boolean, Enum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class StoreNetwork(str, enum.Enum):
    APPLE_ROOM = "APPLE_ROOM"
    JABKO = "JABKO"


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
    )

    address: Mapped[str] = mapped_column(
        String(255),
    )

    city: Mapped[str] = mapped_column(
        String(100),
    )

    latitude: Mapped[float] = mapped_column(
        Float,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
    )

    network: Mapped[StoreNetwork] = mapped_column(
        Enum(
            StoreNetwork,
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
        default=StoreNetwork.APPLE_ROOM,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    managers: Mapped[list["User"]] = relationship(
        back_populates="store",
    )

    outgoing_orders: Mapped[list["Order"]] = relationship(
        foreign_keys="Order.from_store_id",
        back_populates="from_store",
    )

    incoming_orders: Mapped[list["Order"]] = relationship(
        foreign_keys="Order.to_store_id",
        back_populates="to_store",
    )