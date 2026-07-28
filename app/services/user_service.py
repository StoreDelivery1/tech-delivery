from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.services.activation_service import ActivationService


class UserService:

    @staticmethod
    def _normalize_user_data(user_data: UserCreate | UserUpdate) -> dict:
        data = user_data.model_dump(exclude_unset=True)
        role = data.get("role")

        if role in {UserRole.ADMIN, UserRole.COURIER}:
            data["store_id"] = None
        elif role == UserRole.MANAGER and data.get("store_id") is None:
            raise ValueError("Manager must have a store_id")

        return data

    @staticmethod
    def _normalize_user_instance(user: User, data: dict) -> None:
        role = data.get("role", user.role)

        if role in {UserRole.ADMIN, UserRole.COURIER}:
            data["store_id"] = None
        elif role == UserRole.MANAGER and data.get("store_id") is None and user.store_id is None:
            raise ValueError("Manager must have a store_id")

        for key, value in data.items():
            setattr(user, key, value)

    @staticmethod
    def create(
        db: Session,
        user: UserCreate,
    ) -> User:

        normalized_data = UserService._normalize_user_data(user)
        new_user = User(**normalized_data)

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        ActivationService.assign_activation_code(
            db=db,
            user=new_user,
        )

        return new_user

    @staticmethod
    def get_all(
        db: Session,
    ) -> list[User]:

        return (
            db.query(User)
            .order_by(User.id)
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        user_id: int,
    ) -> User | None:

        return db.get(User, user_id)

    @staticmethod
    def get_by_telegram_id(
        db: Session,
        telegram_id: int,
    ) -> User | None:

        return (
            db.query(User)
            .filter(User.telegram_id == telegram_id)
            .first()
        )

    @staticmethod
    def update(
        db: Session,
        user: User,
        data: UserUpdate,
    ) -> User:

        update_data = UserService._normalize_user_data(data)
        UserService._normalize_user_instance(user, update_data)

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def delete(
        db: Session,
        user: User,
    ) -> None:

        db.delete(user)
        db.commit()