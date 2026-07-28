from pydantic import BaseModel

from app.models.store import StoreNetwork


class StoreCreate(BaseModel):
    name: str
    address: str
    city: str
    latitude: float
    longitude: float
    network: StoreNetwork


class StoreResponse(BaseModel):
    id: int
    name: str
    address: str
    city: str
    latitude: float
    longitude: float
    network: StoreNetwork
    is_active: bool

    class Config:
        from_attributes = True