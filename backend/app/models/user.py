import enum

from sqlalchemy import Enum, ForeignKey, Integer, String
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

    store_id: Mapped[int | None] = mapped_column(
        ForeignKey("stores.id"),
        nullable=True,
    )

    store: Mapped["Store"] = relationship(
        back_populates="managers",
    )