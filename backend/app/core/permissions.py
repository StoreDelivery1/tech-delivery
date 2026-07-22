from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User, UserRole


def require_role(
    role: UserRole,
):
    def dependency(
        current_user: Annotated[
            User,
            Depends(get_current_user),
        ],
    ) -> User:

        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )

        return current_user

    return dependency