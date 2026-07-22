from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
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
    db: Session = Depends(get_db),
):
    return OrderService.create_order(
        db=db,
        order=order,
    )


@router.get("/", response_model=list[OrderResponse])
def get_orders(
    db: Session = Depends(get_db),
):
    return OrderService.get_orders(db=db)


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
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