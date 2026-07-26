from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.activation_service import ActivationService


class UserService:

    @staticmethod
    def create(
        db: Session,
        user: UserCreate,
    ) -> User:

        new_user = User(**user.model_dump())

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

        update_data = data.model_dump(
            exclude_unset=True,
        )

        for key, value in update_data.items():
            setattr(user, key, value)

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