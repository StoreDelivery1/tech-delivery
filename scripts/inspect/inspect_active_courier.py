from app.database.session import SessionLocal
from app.models.user import User, UserRole
from sqlalchemy import text

db = SessionLocal()

print("=" * 80)
print("DATABASE INSPECTION: Current Logged-In Courier")
print("=" * 80)

print("\n1. FINDING COURIER WITH ACTIVE TELEGRAM_ID")
print("-" * 80)

# Get a courier with telegram_id (activated)
courier = db.query(User).filter(
    User.role == UserRole.COURIER,
    User.telegram_id.isnot(None),
    User.activated_at.isnot(None),
).first()

if courier:
    print(f"✓ Found active courier: {courier.full_name}\n")
    
    print("2. COURIER USER DETAILS")
    print("-" * 80)
    print(f"id:                {courier.id}")
    print(f"full_name:         {courier.full_name}")
    print(f"telegram_id:       {courier.telegram_id}")
    print(f"role:              {courier.role}")
    print(f"status:            {courier.status}")
    print(f"activation_code:   {courier.activation_code}")
    print(f"activated_at:      {courier.activated_at}")
    
    print("\n3. RAW DATABASE VALUES (for role column)")
    print("-" * 80)
    raw_query = text(
        "SELECT id, full_name, telegram_id, role FROM users WHERE id = :user_id"
    )
    raw_result = db.execute(raw_query, {"user_id": courier.id}).fetchone()
    if raw_result:
        raw_id, raw_name, raw_tg, raw_role = raw_result
        print(f"id (DB):           {raw_id}")
        print(f"full_name (DB):    {raw_name}")
        print(f"telegram_id (DB):  {raw_tg}")
        print(f"role (DB):         '{raw_role}'")
        print(f"role type (DB):    {type(raw_role).__name__}")
        print(f"role repr (DB):    {repr(raw_role)}")
    
    print("\n4. EXACT QUERY FROM get_courier()")
    print("-" * 80)
    print("Query structure:")
    print("  db.query(User)")
    print("    .filter(")
    print("      User.telegram_id == telegram_id,")
    print("      User.role == UserRole.COURIER,")
    print("    )")
    print("    .first()")
    
    print(f"\nWith values:")
    print(f"  telegram_id = {courier.telegram_id}")
    print(f"  role = UserRole.COURIER = {UserRole.COURIER}")
    
    print("\n5. EXECUTING THE EXACT QUERY")
    print("-" * 80)
    
    # Method 1: Using ORM (what get_courier uses)
    orm_result = db.query(User).filter(
        User.telegram_id == courier.telegram_id,
        User.role == UserRole.COURIER,
    ).first()
    
    if orm_result:
        print(f"✓ ORM Query Result: FOUND")
        print(f"  User: {orm_result.full_name} (ID: {orm_result.id})")
        print(f"  Role: {orm_result.role}")
    else:
        print(f"✗ ORM Query Result: NONE")
    
    # Method 2: Raw SQL to verify
    print("\n  Raw SQL equivalent:")
    raw_sql = text(
        "SELECT * FROM users WHERE telegram_id = :tg_id AND role = :role_val"
    )
    raw_sql_result = db.execute(
        raw_sql,
        {"tg_id": courier.telegram_id, "role_val": "COURIER"}
    ).fetchone()
    
    if raw_sql_result:
        print(f"✓ Raw SQL Query Result: FOUND")
        print(f"  Returned row with {len(raw_sql_result)} columns")
    else:
        print(f"✗ Raw SQL Query Result: NONE")
    
    print("\n6. ROLE COLUMN ANALYSIS")
    print("-" * 80)
    print(f"Database stored value:     '{raw_role}'")
    print(f"Python Enum value:         {UserRole.COURIER}")
    print(f"Enum string representation: '{UserRole.COURIER.value}'")
    print(f"Match (==):                {courier.role == UserRole.COURIER}")
    print(f"Match (str):               {str(courier.role) == str(UserRole.COURIER)}")
    print(f"Match (.value):            {courier.role.value == 'COURIER'}")
    
    print("\n7. FILTER CONDITIONS BREAKDOWN")
    print("-" * 80)
    print(f"Condition 1: User.telegram_id == {courier.telegram_id}")
    print(f"  courier.telegram_id: {courier.telegram_id}")
    print(f"  Match: {courier.telegram_id == courier.telegram_id}")
    
    print(f"\nCondition 2: User.role == UserRole.COURIER")
    print(f"  courier.role: {courier.role}")
    print(f"  UserRole.COURIER: {UserRole.COURIER}")
    print(f"  Match: {courier.role == UserRole.COURIER}")
    
    print(f"\nBoth conditions (AND): {(courier.telegram_id == courier.telegram_id) and (courier.role == UserRole.COURIER)}")

else:
    print("✗ No active courier with telegram_id found")
    print("\nChecking all couriers:")
    all_couriers = db.query(User).filter(User.role == UserRole.COURIER).all()
    for c in all_couriers:
        print(f"  ID: {c.id}, Name: {c.full_name}, TG: {c.telegram_id}, Activated: {c.activated_at is not None}")

print("\n" + "=" * 80)
db.close()
