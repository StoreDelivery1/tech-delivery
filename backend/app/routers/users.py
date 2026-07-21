from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    existing_user = db.scalar(
        select(User).where(User.telegram_id == user_data.telegram_id)
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="User with this Telegram ID already exists",
        )

    user = User(
        telegram_id=user_data.telegram_id,
        username=user_data.username,
        full_name=user_data.full_name,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.id)).all()

    return users