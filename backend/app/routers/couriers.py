from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.dependencies import get_db
from app.models.user import User
from app.schemas.courier import (
    CourierResponse,
    CourierStatistics,
    CourierStatusUpdate,
)
from app.schemas.order import OrderResponse
from app.services.courier_service import CourierService

router = APIRouter(
    prefix="/couriers",
    tags=["Couriers"],
)


@router.get(
    "/me",
    response_model=CourierResponse,
)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return CourierService.get_profile(
            db=db,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )


@router.get(
    "/me/orders",
    response_model=list[OrderResponse],
)
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CourierService.get_orders(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/me/statistics",
    response_model=CourierStatistics,
)
def get_my_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CourierService.get_statistics(
        db=db,
        user_id=current_user.id,
    )


@router.patch(
    "/me/status",
    response_model=CourierResponse,
)
def update_my_status(
    data: CourierStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return CourierService.update_online_status(
            db=db,
            user_id=current_user.id,
            is_online=data.is_online,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )