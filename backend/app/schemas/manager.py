from pydantic import BaseModel


class ManagerStatistics(BaseModel):
    total_orders: int
    waiting_orders: int
    in_progress_orders: int
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