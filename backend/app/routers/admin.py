from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import admin_required
from app.dependencies import get_db
from app.models.user import User
from app.schemas.admin import AdminDashboardResponse
from app.schemas.order import OrderResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.admin_service import AdminService
from app.services.order_service import OrderService
from app.services.user_service import UserService

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.get(
    "/dashboard",
    response_model=AdminDashboardResponse,
)
def get_dashboard(
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db),
):
    return AdminService.get_dashboard(db)


@router.get(
    "/users",
    response_model=list[UserResponse],
)
def get_users(
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db),
):
    return UserService.get_all(db)


@router.post(
    "/users",
    response_model=UserResponse,
)
def create_user(
    user: UserCreate,
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db),
):
    return UserService.create(
        db,
        user,
    )


@router.get(
    "/orders",
    response_model=list[OrderResponse],
)
def get_orders(
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db),
):
    return OrderService.get_orders(db)


@router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
)
def get_order(
    order_id: int,
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db),
):
    try:
        return OrderService.get_order(
            db,
            order_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )


@router.delete(
    "/orders/{order_id}",
)
def delete_order(
    order_id: int,
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db),
):
    try:
        OrderService.delete_order(
            db,
            order_id,
        )

        return {
            "message": "Order deleted successfully",
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )