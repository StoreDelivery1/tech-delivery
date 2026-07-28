from app.database.session import SessionLocal
from app.models.user import User, UserRole
from app.services.activation_service import ActivationService

db = SessionLocal()

print("=" * 80)
print("VERIFICATION: ActivationService.get_courier() with actual courier")
print("=" * 80)

# Get active courier
courier = db.query(User).filter(
    User.role == UserRole.COURIER,
    User.telegram_id.isnot(None),
    User.activated_at.isnot(None),
).first()

if courier:
    print(f"\nTesting courier: {courier.full_name}")
    print(f"Telegram ID: {courier.telegram_id}")
    print(f"Role: {courier.role}")
    print(f"Activated: {courier.activated_at}")
    
    print("\n" + "-" * 80)
    print("Calling: ActivationService.get_courier(db, {})".format(courier.telegram_id))
    print("-" * 80)
    
    result = ActivationService.get_courier(db, courier.telegram_id)
    
    print(f"\nResult: {result}")
    
    if result:
        print(f"✓ SUCCESS - Returned courier object")
        print(f"  ID: {result.id}")
        print(f"  Name: {result.full_name}")
        print(f"  Role: {result.role}")
        print(f"  Match: {result.id == courier.id}")
    else:
        print(f"✗ FAILED - Returned None")
        print(f"\nDEBUGGING:")
        
        # Check each condition
        print(f"  telegram_id exists: {courier.telegram_id is not None}")
        print(f"  role is COURIER: {courier.role == UserRole.COURIER}")
        
        # Direct query test
        direct_result = db.query(User).filter(
            User.telegram_id == courier.telegram_id,
            User.role == UserRole.COURIER,
        ).first()
        print(f"  Direct query result: {direct_result}")

db.close()
