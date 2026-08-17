from app.models.order import OrderStatus


class OrderState:

    VALID_TRANSITIONS = {
        OrderStatus.WAITING_FOR_COURIER: {
            OrderStatus.ACCEPTED,
            OrderStatus.CANCELED,
        },
        OrderStatus.ACCEPTED: {
            OrderStatus.PICKED_UP,
            OrderStatus.CANCELED,
        },
        OrderStatus.PICKED_UP: {
            OrderStatus.DELIVERING,
        },
        OrderStatus.DELIVERING: {
            OrderStatus.DELIVERED,
        },
        OrderStatus.DELIVERED: set(),
        OrderStatus.CANCELED: set(),
    }

    @classmethod
    def can_change(
        cls,
        current: OrderStatus,
        new: OrderStatus,
    ) -> bool:
        return new in cls.VALID_TRANSITIONS[current]