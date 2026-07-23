from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User, UserRole


def require_roles(
    current_user: User,
    *roles: UserRole,
) -> None:

    if current_user.role not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )


def admin_required(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:

    require_roles(
        current_user,
        UserRole.ADMIN,
    )

    return current_user


def manager_required(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:

    require_roles(
        current_user,
        UserRole.MANAGER,
    )

    return current_user


def courier_required(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:

    require_roles(
        current_user,
        UserRole.COURIER,
    )

    return current_user