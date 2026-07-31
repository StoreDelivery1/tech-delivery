from app.database.session import SessionLocal
from app.models.user import User, UserRole, UserStatus
from app.services.activation_service import ActivationService

db = SessionLocal()

print("=" * 80)
print("INSPECTION: User with Telegram ID 8345605125")
print("=" * 80)

# Task 1: Find the user
telegram_id = 8345605125
user = db.query(User).filter(User.telegram_id == telegram_id).first()

if user:
    print("\n1. USER FOUND")
    print("-" * 80)
    print(f"id:             {user.id}")
    print(f"full_name:      {user.full_name}")
    print(f"telegram_id:    {user.telegram_id}")
    print(f"role:           {user.role}")
    print(f"status:         {user.status}")
    print(f"activated_at:   {user.activated_at}")
    
    # Task 3: Execute get_courier()
    print("\n2. EXECUTING ActivationService.get_courier(db, {})".format(telegram_id))
    print("-" * 80)
    courier = ActivationService.get_courier(db, telegram_id)
    
    # Task 4: Show returned value
    print(f"\nResult: {courier}")
    
    if courier is None:
        print("\n3. RESULT IS None - EXPLANATION")
        print("-" * 80)
        print(f"User exists in database:")
        print(f"  - telegram_id: {user.telegram_id}")
        print(f"  - role: {user.role}")
        print(f"\nget_courier() returns None because:")
        print(f"  User.role == UserRole.COURIER: {user.role == UserRole.COURIER}")
        print(f"  Actual role in database: {user.role}")
        print(f"  Expected role for courier: {UserRole.COURIER}")
        print(f"\nThe user exists but has role '{user.role}', not 'COURIER'.")
        print(f"Therefore, get_courier() correctly returns None (not a courier).")
    else:
        print("\n3. RESULT IS User Object - SUCCESS")
        print("-" * 80)
        print(f"get_courier() successfully returned:")
        print(f"  User ID: {courier.id}")
        print(f"  Role: {courier.role}")
        print(f"  Telegram ID: {courier.telegram_id}")

else:
    print("\n1. USER NOT FOUND")
    print("-" * 80)
    print(f"No user with telegram_id = {telegram_id} exists in the database.")
    
    # Task 3: Execute get_courier() anyway
    print("\n2. EXECUTING ActivationService.get_courier(db, {})".format(telegram_id))
    print("-" * 80)
    courier = ActivationService.get_courier(db, telegram_id)
    
    # Task 4: Show returned value
    print(f"\nResult: {courier}")
    
    print("\n3. EXPLANATION: User Does Not Exist")
    print("-" * 80)
    print(f"The Telegram account with ID {telegram_id} is NOT registered in the database.")
    print(f"\nWhy the bot receives updates from this account but it's not in database:")
    print(f"  1. Telegram sends updates for ANY user interaction with the bot")
    print(f"  2. The bot receives message.from_user.id = {telegram_id}")
    print(f"  3. But this user hasn't completed activation/registration yet")
    print(f"  4. Database linkage only happens after successful activation")
    print(f"  5. Without database record, user queries (like get_courier) return None")
    print(f"\nThis is normal - the user is interacting with the bot but hasn't")
    print(f"gone through the activation process to link their account.")

print("\n" + "=" * 80)
db.close()
