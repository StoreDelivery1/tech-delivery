from pydantic import BaseModel


class StoreCreate(BaseModel):
    name: str
    address: str
    city: str
    latitude: float
    longitude: float


class StoreResponse(BaseModel):
    id: int
    name: str
    address: str
    city: str
    latitude: float
    longitude: float
    is_active: bool

    class Config:
        from_attributes = True