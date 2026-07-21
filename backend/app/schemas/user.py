from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    telegram_id: int
    username: str | None = None
    full_name: str


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    full_name: str

    model_config = ConfigDict(from_attributes=True)