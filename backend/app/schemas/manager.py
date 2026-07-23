from pydantic import BaseModel

from app.schemas.order import OrderResponse


class ManagerStatistics(BaseModel):
    total_orders: int
    active_orders: int
    delivered_orders: int


class ManagerCourierResponse(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    full_name: str
    is_online: bool

    model_config = {
        "from_attributes": True,
    }


class ManagerOrderResponse(OrderResponse):
    created_by: int | None