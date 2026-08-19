import secrets
import string
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.user import User, UserRole, UserStatus


class ActivationService:

    CODE_PREFIX = "TD-"
    CODE_SUFFIX_LENGTH = 7
    CODE_EXPIRE_MINUTES = 60

    @staticmethod
    def generate_code(
        db: Session,
    ) -> str:

        if ActivationService.CODE_SUFFIX_LENGTH <= 0:
            raise ValueError("Invalid activation code configuration")

        while True:
            suffix = "".join(
                secrets.choice(
                    string.ascii_uppercase + string.digits,
                )
                for _ in range(ActivationService.CODE_SUFFIX_LENGTH)
            )

            code = f"{ActivationService.CODE_PREFIX}{suffix}"

            exists = (
                db.query(User)
                .filter(User.activation_code == code)
                .first()
            )

            if exists is None:
                return code

    @staticmethod
    def assign_activation_code(
        db: Session,
        user: User,
    ) -> User:

        user.activation_code = ActivationService.generate_code(db)

        user.activation_code_expires_at = (
            datetime.now()
            + timedelta(minutes=ActivationService.CODE_EXPIRE_MINUTES)
        )

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def get_by_code(
        db: Session,
        code: str,
    ) -> User | None:

        return (
            db.query(User)
            .filter(User.activation_code == code)
            .first()
        )

    @staticmethod
    def get_by_telegram(
        db: Session,
        telegram_id: int,
    ) -> User | None:

        return (
            db.query(User)
            .filter(User.telegram_id == telegram_id)
            .first()
        )

    @staticmethod
    def get_admin(
        db: Session,
        telegram_id: int,
    ) -> User | None:
        """Get admin user by telegram_id with role verification."""
        return (
            db.query(User)
            .filter(
                User.telegram_id == telegram_id,
                User.role == UserRole.ADMIN,
                User.status == UserStatus.ACTIVE,
            )
            .first()
        )

    @staticmethod
    def get_manager(
        db: Session,
        telegram_id: int,
    ) -> User | None:
        """Get manager user by telegram_id with role verification."""
        return (
            db.query(User)
            .filter(
                User.telegram_id == telegram_id,
                User.role == UserRole.MANAGER,
                User.status == UserStatus.ACTIVE,
            )
            .first()
        )

    @staticmethod
    def get_courier(
        db: Session,
        telegram_id: int,
    ) -> User | None:
        """Get courier user by telegram_id with role verification."""
        return (
            db.query(User)
            .filter(
                User.telegram_id == telegram_id,
                User.role == UserRole.COURIER,
                User.status == UserStatus.ACTIVE,
            )
            .first()
        )

    @staticmethod
    def activate(
        db: Session,
        user: User,
        telegram_id: int,
        username: str | None,
    ) -> User:

        if (
            user.activation_code_expires_at
            and user.activation_code_expires_at
            < datetime.now()
        ):
            raise ValueError("Activation code expired")

        existing = ActivationService.get_by_telegram(
            db,
            telegram_id,
        )

        if existing and existing.id != user.id:
            raise ValueError(
                "Telegram account already linked"
            )

        user.telegram_id = telegram_id
        user.username = username

        user.activated_at = datetime.now()
        user.last_login_at = datetime.now()

        user.activation_code = None
        user.activation_code_expires_at = None

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def update_last_login(
        db: Session,
        user: User,
    ) -> None:

        user.last_login_at = datetime.now()

        db.commit()

    @staticmethod
    def reset_telegram(
        db: Session,
        user: User,
    ) -> User:

        user.telegram_id = None
        user.username = None
        user.activated_at = None

        user.activation_code = (
            ActivationService.generate_code(db)
        )

        user.activation_code_expires_at = (
            datetime.now()
            + timedelta(minutes=ActivationService.CODE_EXPIRE_MINUTES)
        )

        db.commit()
        db.refresh(user)

        return user