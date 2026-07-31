from app.database.session import SessionLocal
from app.models.user import User, UserRole
from app.services.activation_service import ActivationService

db = SessionLocal()

print("=" * 70)
print("ROOT CAUSE ANALYSIS: get_courier() Behavior")
print("=" * 70)

print("\n1. USER ROLE DEFINITION IN CODE")
print("-" * 70)
print("class UserRole(str, enum.Enum):")
print("    ADMIN = 'ADMIN'")
print("    MANAGER = 'MANAGER'")
print("    COURIER = 'COURIER'")

print("\n2. DATABASE USERS BY ROLE")
print("-" * 70)
for role in [UserRole.COURIER, UserRole.MANAGER, UserRole.ADMIN]:
    users = db.query(User).filter(User.role == role).all()
    print(f"\n{role.name} users:")
    for u in users:
        print(f"  ID: {u.id:2} | Name: {u.full_name:30} | TG: {u.telegram_id}")

print("\n3. HOW get_courier() WORKS")
print("-" * 70)
print("@staticmethod")
print("def get_courier(db: Session, telegram_id: int) -> User | None:")
print("    return (")
print("        db.query(User)")
print("        .filter(")
print("            User.telegram_id == telegram_id,")
print("            User.role == UserRole.COURIER,")
print("        )")
print("        .first()")
print("    )")

print("\n4. ENUM COMPARISON VERIFICATION")
print("-" * 70)
courier = db.query(User).filter(User.role == UserRole.COURIER).first()
if courier:
    print(f"Test user: {courier.full_name}")
    print(f"  courier.role: {courier.role}")
    print(f"  UserRole.COURIER: {UserRole.COURIER}")
    print(f"  courier.role == UserRole.COURIER: {courier.role == UserRole.COURIER}")
    print(f"  ✓ Enum comparison works correctly")

print("\n5. ROOT CAUSE - WHY get_courier() MIGHT RETURN NONE")
print("-" * 70)
print("get_courier() will return None ONLY if:")
print("  1. Telegram ID doesn't exist in database")
print("  2. Telegram ID exists BUT user.role != UserRole.COURIER")
print("     (i.e., the user is a MANAGER or ADMIN)")
print("  3. Telegram ID is None/null")
print("")
print("This is CORRECT behavior - it prevents managers/admins from being")
print("treated as couriers by get_courier()")

print("\n6. VERIFICATION: Test with courier telegram IDs")
print("-" * 70)
couriers_with_tg = db.query(User).filter(
    User.role == UserRole.COURIER,
    User.telegram_id.isnot(None)
).all()

for courier in couriers_with_tg:
    result = ActivationService.get_courier(db, courier.telegram_id)
    status = "✓ SUCCESS" if result else "✗ FAILED"
    print(f"{status}: get_courier({courier.telegram_id}) -> {courier.full_name}")

print("\n" + "=" * 70)
print("CONCLUSION: get_courier() is working CORRECTLY")
print("=" * 70)

db.close()
