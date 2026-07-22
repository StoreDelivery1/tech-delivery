from pydantic import BaseModel

from app.models.order import OrderStatus


class OrderCreate(BaseModel):
    store_id: int
    customer_name: str
    customer_phone: str
    delivery_address: str


class OrderResponse(BaseModel):
    id: int
    store_id: int
    customer_name: str
    customer_phone: str
    delivery_address: str
    status: OrderStatus

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: OrderStatus