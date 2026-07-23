from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


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
    def update(
        db: Session,
        user: User,
        data: UserUpdate,
    ) -> User:

        for key, value in data.model_dump(
            exclude_unset=True,
        ).items():
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