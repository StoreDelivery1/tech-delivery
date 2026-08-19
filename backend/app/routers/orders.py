from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import admin_required, courier_required, manager_required
from app.dependencies import get_db
from app.models.user import User
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
)
from app.services.order_service import OrderService

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


@router.post("/", response_model=OrderResponse)
def create_order(
    order: OrderCreate,
    current_user: Annotated[User, Depends(manager_required)],
    db: Session = Depends(get_db),
):
    try:
        return OrderService.create_order(
            db=db,
            order=order,
            current_user=current_user,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/", response_model=list[OrderResponse])
def get_orders(
    current_user: Annotated[User, Depends(admin_required)],
    db: Session = Depends(get_db),
):
    return OrderService.get_orders(db=db)


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    current_user: Annotated[User, Depends(admin_required)],
    db: Session = Depends(get_db),
):
    try:
        return OrderService.update_status(
            db=db,
            order_id=order_id,
            new_status=data.status,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.patch("/{order_id}/assign", response_model=OrderResponse)
def assign_courier(
    order_id: int,
    current_user: Annotated[User, Depends(courier_required)],
    db: Session = Depends(get_db),
):
    try:
        return OrderService.assign_courier(
            db=db,
            order_id=order_id,
            courier_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )