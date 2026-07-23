from pydantic import BaseModel

from app.models.order import OrderStatus


class OrderCreate(BaseModel):
    store_id: int
    customer_name: str
    customer_phone: str
    delivery_address: str


class ManagerOrderCreate(BaseModel):
    customer_name: str
    customer_phone: str
    delivery_address: str


class OrderResponse(BaseModel):
    id: int
    store_id: int
    courier_id: int | None
    customer_name: str
    customer_phone: str
    delivery_address: str
    status: OrderStatus

    model_config = {
        "from_attributes": True,
    }


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class AssignCourierRequest(BaseModel):
    courier_id: int