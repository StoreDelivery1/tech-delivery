from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import UserStatus
from app.schemas.auth import TokenResponse
from app.services.user_service import UserService


class AuthService:

    @staticmethod
    def login(
        db: Session,
        telegram_id: int,
    ) -> TokenResponse:

        user = UserService.get_by_telegram_id(
            db,
            telegram_id,
        )

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid telegram_id",
            )

        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials",
            )

        user.last_login_at = datetime.now()

        db.commit()
        db.refresh(user)

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