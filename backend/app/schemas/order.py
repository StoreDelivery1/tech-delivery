from pydantic import BaseModel, ConfigDict

from app.models.order import OrderPriority, OrderStatus


class OrderCreate(BaseModel):
    to_store_id: int
    description: str
    estimated_weight: float | None = None
    priority: OrderPriority = OrderPriority.NORMAL
    manager_comment: str | None = None


class OrderResponse(BaseModel):
    id: int
    number: str

    from_store_id: int
    to_store_id: int

    created_by: int
    courier_id: int | None

    description: str
    estimated_weight: float | None

    priority: OrderPriority
    manager_comment: str | None

    status: OrderStatus

    model_config = ConfigDict(
        from_attributes=True,
    )


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class AssignCourierRequest(BaseModel):
    courier_id: int