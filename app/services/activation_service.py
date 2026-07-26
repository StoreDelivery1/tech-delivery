import random
import string
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.user import User


class ActivationService:

    CODE_PREFIX = "TD"
    CODE_LENGTH = 4
    CODE_EXPIRE_HOURS = 24

    @staticmethod
    def generate_code(
        db: Session,
    ) -> str:

        while True:
            suffix = "".join(
                random.choices(
                    string.ascii_uppercase + string.digits,
                    k=ActivationService.CODE_LENGTH,
                )
            )

            code = f"{ActivationService.CODE_PREFIX}-{suffix}"

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
            datetime.now(timezone.utc)
            + timedelta(hours=ActivationService.CODE_EXPIRE_HOURS)
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
    def activate(
        db: Session,
        user: User,
        telegram_id: int,
        username: str | None,
    ) -> User:

        if (
            user.activation_code_expires_at
            and user.activation_code_expires_at
            < datetime.now(timezone.utc)
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

        user.activated_at = datetime.now(timezone.utc)
        user.last_login_at = datetime.now(timezone.utc)

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

        user.last_login_at = datetime.now(timezone.utc)

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
            datetime.now(timezone.utc)
            + timedelta(hours=ActivationService.CODE_EXPIRE_HOURS)
        )

        db.commit()
        db.refresh(user)

        return user