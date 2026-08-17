from app.database.session import SessionLocal
from app.models.user import User, UserRole

db = SessionLocal()

# Get first user
user = db.query(User).first()

if user:
    print("=== USER DATA ===")
    print(f"id: {user.id}")
    print(f"full_name: {user.full_name}")
    print(f"telegram_id: {user.telegram_id}")
    print(f"role (Python object): {user.role}")
    print(f"role (type): {type(user.role)}")
    print(f"role (repr): {repr(user.role)}")
    
    # Raw SQL query to see what's in database
    from sqlalchemy import text
    raw_result = db.execute(text("SELECT id, full_name, telegram_id, role FROM users LIMIT 1")).fetchone()
    print(f"\n=== RAW DATABASE VALUE ===")
    print(f"role (raw from DB): {raw_result[3]}")
    print(f"role (raw type): {type(raw_result[3])}")
    
    # Check UserRole definition
    print(f"\n=== UserRole ENUM ===")
    print(f"UserRole.COURIER: {UserRole.COURIER}")
    print(f"UserRole.COURIER (type): {type(UserRole.COURIER)}")
    print(f"UserRole.COURIER (repr): {repr(UserRole.COURIER)}")
    
    # Test comparison
    print(f"\n=== COMPARISON TEST ===")
    print(f"user.role == UserRole.COURIER: {user.role == UserRole.COURIER}")
    print(f"user.role == 'COURIER': {user.role == 'COURIER'}")
    print(f"str(user.role) == 'COURIER': {str(user.role) == 'COURIER'}")
    print(f"user.role.value == 'COURIER': {user.role.value == 'COURIER'}")
    
    # Check all users and their roles
    print(f"\n=== ALL USERS ===")
    all_users = db.query(User).all()
    for u in all_users:
        print(f"ID: {u.id}, Name: {u.full_name}, TG: {u.telegram_id}, Role: {u.role} ({type(u.role).__name__})")

else:
    print("No users found in database")

db.close()
