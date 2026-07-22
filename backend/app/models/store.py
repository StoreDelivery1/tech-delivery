from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


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

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    managers: Mapped[list["User"]] = relationship(
        back_populates="store",
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="store",
    )