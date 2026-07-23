from pydantic import BaseModel


class AdminDashboardResponse(BaseModel):
    stores: int
    managers: int
    couriers: int
    online_couriers: int
    active_orders: int
    delivered_today: int