from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.dependencies import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    try:
        telegram_id = int(form_data.username)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid telegram_id",
        )

    return AuthService.login(
        db=db,
        telegram_id=telegram_id,
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    return current_user