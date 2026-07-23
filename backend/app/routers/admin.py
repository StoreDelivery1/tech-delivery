from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.permissions import admin_required
from app.dependencies import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.get(
    "/users",
    response_model=list[UserResponse],
)
def get_users(
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db),
):
    return UserService.get_all(db)


@router.post(
    "/users",
    response_model=UserResponse,
)
def create_user(
    user: UserCreate,
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db),
):
    return UserService.create(
        db,
        user,
    )