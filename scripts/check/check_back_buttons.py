import re

code = open('app/bot/handlers/courier.py').read()

# Find all buttons with "Назад" text
pattern = r'InlineKeyboardButton\([^)]*text="[^"]*Назад[^"]*"[^)]*callback_data="([^"]+)"'
matches = re.findall(pattern, code)

print("All 'Назад' buttons and their callback_data:")
for match in matches:
    print(f"  ⬅️ Назад → {match}")

# Check if any point to manager or admin
bad_callbacks = [m for m in matches if 'manager' in m.lower() or 'admin' in m.lower()]
if bad_callbacks:
    print(f"\n❌ Found back buttons pointing to manager/admin routes:")
    for cb in bad_callbacks:
        print(f"  - {cb}")
else:
    print(f"\n✅ All back buttons use courier-specific callbacks")
