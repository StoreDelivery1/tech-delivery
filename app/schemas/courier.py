from datetime import datetime

from pydantic import BaseModel

from app.models.user import UserStatus


class CourierResponse(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    full_name: str
    status: UserStatus
    is_online: bool
    last_seen: datetime | None

    model_config = {
        "from_attributes": True,
    }


class CourierStatistics(BaseModel):
    total_orders: int
    active_orders: int
    delivered_orders: int


class CourierStatusUpdate(BaseModel):
    is_online: bool