from datetime import datetime

from pydantic import BaseModel

from app.models.user import UserRole, UserStatus


class UserBase(BaseModel):
    username: str | None = None
    full_name: str
    role: UserRole
    store_id: int | None = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    username: str | None = None
    full_name: str | None = None
    role: UserRole | None = None
    status: UserStatus | None = None
    store_id: int | None = None


class UserResponse(BaseModel):
    id: int
    telegram_id: int | None
    activation_code: str | None
    activation_code_expires_at: datetime | None
    activated_at: datetime | None
    last_login_at: datetime | None
    username: str | None
    full_name: str
    role: UserRole
    status: UserStatus
    store_id: int | None

    model_config = {
        "from_attributes": True,
    }