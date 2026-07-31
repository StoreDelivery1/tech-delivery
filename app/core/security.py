from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.dependencies import get_db
from app.models.user import User, UserStatus

_ALLOWED_JWT_ALGORITHMS = {"HS256"}


def _validate_jwt_settings() -> None:
    if (
        not settings.SECRET_KEY
        or settings.SECRET_KEY in {"change_me_in_env", "<strong_random_secret>"}
        or len(settings.SECRET_KEY) < 32
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server authentication is not configured",
        )

    if settings.ALGORITHM not in _ALLOWED_JWT_ALGORITHMS:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unsupported token algorithm configuration",
        )

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
)


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    _validate_jwt_settings()

    payload = data.copy()

    now = datetime.now(timezone.utc)
    expires_in = expires_delta or timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    if expires_in.total_seconds() <= 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid token expiration configuration",
        )

    payload.update(
        {
            "iat": now,
            "exp": now + expires_in,
            "type": "access",
        }
    )

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    _validate_jwt_settings()

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(token)

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = db.get(User, int(user_id))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return user