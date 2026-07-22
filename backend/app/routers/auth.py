from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.dependencies import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/login", response_model=TokenResponse)
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

    user = (
        db.query(User)
        .filter(User.telegram_id == telegram_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid telegram_id",
        )

    token = create_access_token(
        {
            "sub": str(user.id),
            "role": user.role.value,
        }
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )