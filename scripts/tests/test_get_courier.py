from app.database.session import SessionLocal
from app.models.user import User, UserRole
from app.services.activation_service import ActivationService

db = SessionLocal()

print("=== TESTING get_courier() ===\n")

# Get all couriers
couriers = db.query(User).filter(User.role == UserRole.COURIER).all()
print(f"Total couriers in DB: {len(couriers)}\n")

for courier in couriers:
    print(f"Courier ID {courier.id}: {courier.full_name}")
    print(f"  - Telegram ID: {courier.telegram_id}")
    print(f"  - Role: {courier.role}")
    
    if courier.telegram_id:
        result = ActivationService.get_courier(db, courier.telegram_id)
        print(f"  - get_courier({courier.telegram_id}): {result}")
        if result:
            print(f"    ✓ Found: {result.full_name} (Role: {result.role})")
        else:
            print(f"    ✗ RETURNED NONE!")
    else:
        print(f"  - No telegram_id (cannot test)")
    print()

# Test with manager telegram
print("=== TESTING get_courier() WITH MANAGER ===\n")
manager = db.query(User).filter(User.role == UserRole.MANAGER, User.telegram_id.isnot(None)).first()
if manager:
    print(f"Manager ID {manager.id}: {manager.full_name}")
    print(f"  - Telegram ID: {manager.telegram_id}")
    print(f"  - Role: {manager.role}")
    result = ActivationService.get_courier(db, manager.telegram_id)
    print(f"  - get_courier({manager.telegram_id}): {result}")
    if result:
        print(f"    ✗ ERROR: Should return None but got {result.full_name}")
    else:
        print(f"    ✓ Correctly returned None")

db.close()
