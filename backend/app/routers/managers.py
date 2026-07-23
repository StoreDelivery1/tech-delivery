from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.permissions import manager_required
from app.dependencies import get_db
from app.models.user import User
from app.schemas.manager import (
    ManagerCourierResponse,
    ManagerStatistics,
)
from app.schemas.order import (
    ManagerOrderCreate,
    OrderResponse,
)
from app.schemas.user import UserResponse
from app.services.manager_service import ManagerService

router = APIRouter(
    prefix="/managers",
    tags=["Managers"],
)


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_my_profile(
    current_user: User = Depends(manager_required),
    db: Session = Depends(get_db),
):
    return ManagerService.get_profile(
        db,
        current_user.id,
    )


@router.post(
    "/me/orders",
    response_model=OrderResponse,
)
def create_order(
    order: ManagerOrderCreate,
    current_user: User = Depends(manager_required),
    db: Session = Depends(get_db),
):
    return ManagerService.create_order(
        db,
        current_user.id,
        order,
    )


@router.get(
    "/me/orders",
    response_model=list[OrderResponse],
)
def get_my_orders(
    current_user: User = Depends(manager_required),
    db: Session = Depends(get_db),
):
    return ManagerService.get_orders(
        db,
        current_user.id,
    )


@router.get(
    "/me/couriers",
    response_model=list[ManagerCourierResponse],
)
def get_my_couriers(
    current_user: User = Depends(manager_required),
    db: Session = Depends(get_db),
):
    return ManagerService.get_couriers(
        db,
        current_user.id,
    )


@router.get(
    "/me/statistics",
    response_model=ManagerStatistics,
)
def get_my_statistics(
    current_user: User = Depends(manager_required),
    db: Session = Depends(get_db),
):
    return ManagerService.get_statistics(
        db,
        current_user.id,
    )