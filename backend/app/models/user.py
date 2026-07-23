import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    COURIER = "COURIER"


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        unique=True,
        index=True,
    )

    username: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            native_enum=False,
            validate_strings=True,
        ),
        default=UserRole.COURIER,
    )

    status: Mapped[UserStatus] = mapped_column(
        Enum(
            UserStatus,
            native_enum=False,
            validate_strings=True,
        ),
        default=UserStatus.ACTIVE,
    )

    is_online: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Для менеджерів — магазин, у якому вони зараз працюють.
    # Для кур'єрів та адміністратора може бути NULL.
    store_id: Mapped[int | None] = mapped_column(
        ForeignKey("stores.id"),
        nullable=True,
    )

    store = relationship(
        "Store",
        back_populates="managers",
    )

    created_orders = relationship(
        "Order",
        foreign_keys="Order.created_by",
        back_populates="creator",
    )

    courier_orders = relationship(
        "Order",
        foreign_keys="Order.courier_id",
        back_populates="courier",
    )