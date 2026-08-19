from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import courier_required
from app.dependencies import get_db
from app.models.order import OrderStatus
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
    current_user: User = Depends(courier_required),
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
    "/orders/open",
    response_model=list[OrderResponse],
)
def get_open_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(courier_required),
):
    return CourierService.get_open_orders(db)


@router.get(
    "/me/orders",
    response_model=list[OrderResponse],
)
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(courier_required),
):
    return CourierService.get_orders(
        db=db,
        user_id=current_user.id,
    )


@router.patch(
    "/orders/{order_id}/accept",
    response_model=OrderResponse,
)
def accept_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(courier_required),
):
    try:
        return CourierService.accept_order(
            db=db,
            order_id=order_id,
            courier_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.patch(
    "/orders/{order_id}/pickup",
    response_model=OrderResponse,
)
def pickup_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(courier_required),
):
    try:
        return CourierService.change_status(
            db=db,
            order_id=order_id,
            courier_id=current_user.id,
            new_status=OrderStatus.PICKED_UP,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.patch(
    "/orders/{order_id}/delivering",
    response_model=OrderResponse,
)
def delivering_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(courier_required),
):
    try:
        return CourierService.change_status(
            db=db,
            order_id=order_id,
            courier_id=current_user.id,
            new_status=OrderStatus.DELIVERING,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.patch(
    "/orders/{order_id}/deliver",
    response_model=OrderResponse,
)
def deliver_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(courier_required),
):
    try:
        return CourierService.change_status(
            db=db,
            order_id=order_id,
            courier_id=current_user.id,
            new_status=OrderStatus.DELIVERED,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get(
    "/me/statistics",
    response_model=CourierStatistics,
)
def get_my_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(courier_required),
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
    current_user: User = Depends(courier_required),
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