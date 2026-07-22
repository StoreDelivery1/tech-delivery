from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post("/", response_model=UserResponse)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    new_user = User(**user.model_dump())

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/", response_model=list[UserResponse])
def get_users(
    db: Session = Depends(get_db),
):
    return db.query(User).all()