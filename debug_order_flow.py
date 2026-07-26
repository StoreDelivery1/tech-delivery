from app.database.session import SessionLocal
from app.schemas.order import ManagerOrderCreate
from app.models.order import OrderPriority
from app.models.user import User, UserRole
from app.services.manager_service import ManagerService
from app.services.courier_service import CourierService


db = SessionLocal()
try:
    manager = db.query(User).filter(User.role == UserRole.MANAGER).first()
    print("manager-user", manager.id if manager else None)

    if manager is None:
        raise SystemExit("No manager user found")

    order = ManagerService.create_order(
        db,
        manager.id,
        ManagerOrderCreate(
            to_store_id=1,
            description="debug order",
            estimated_weight=2.5,
            priority=OrderPriority.NORMAL,
        ),
    )

    print("created-order-id", order.id)
    print("created-order-number", order.number)
    print("created-order-status", order.status)
    print("created-order-from", order.from_store_id)
    print("created-order-to", order.to_store_id)

    open_orders = CourierService.get_open_orders(db)
    print("open-orders-count", len(open_orders))
    for o in open_orders:
        print("open-order", o.id, o.status, o.to_store_id)
finally:
    db.close()
