code = open('app/bot/handlers/courier.py').read()

# Find the back button
import re
back_buttons = re.findall(r'callback_data="([^"]*(?:back|Back|назад|Назад)[^"]*)"', code)
print("Back button callback_data values found:")
for cb in back_buttons:
    print(f"  - {cb}")

# Find corresponding handlers
handlers = re.findall(r'@router\.callback_query\(F\.data == "([^"]*(?:back|Back|назад|Назад)[^"]*)"\)', code)
print("\nBack button handlers found:")
for h in handlers:
    print(f"  - {h}")

# Check if there's a mismatch
print("\nChecking for mismatches...")
all_callbacks = set(back_buttons)
all_handlers = set(handlers)

missing_handlers = all_callbacks - all_handlers
if missing_handlers:
    print(f"  ❌ Callback_data without handlers: {missing_handlers}")
else:
    print(f"  ✅ All callback_data have handlers")

missing_callbacks = all_handlers - all_callbacks
if missing_callbacks:
    print(f"  ⚠️  Unused handlers: {missing_callbacks}")
