import re

code = open('app/bot/handlers/courier.py').read()

# Find profile message function
profile_start = code.find('def _build_courier_profile_message')
profile_end = code.find('def _build_courier_profile_keyboard')
profile_code = code[profile_start:profile_end]

# Check for store references
issues = []
if 'store' in profile_code.lower():
    store_lines = [line for line in profile_code.split('\n') if 'store' in line.lower()]
    for line in store_lines:
        issues.append(f"Found 'store': {line.strip()}")

if '🏪' in profile_code:
    issues.append("Found store emoji 🏪")
    
if 'Магазин' in profile_code:
    issues.append("Found 'Магазин'")
    
if 'Мережа' in profile_code:
    issues.append("Found 'Мережа'")

if 'network' in profile_code.lower():
    issues.append("Found 'network'")

# Check keyboard
keyboard_start = code.find('def _build_courier_profile_keyboard')
keyboard_end = code.find('async def courier_profile_handler', keyboard_start)
keyboard_code = code[keyboard_start:keyboard_end]

if 'Мій магазин' in keyboard_code:
    issues.append("Found 'Мій магазин' button in keyboard")

if issues:
    print("❌ Issues found in courier profile:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("✅ Courier profile is clean - no store references found")
    print("\nProfile message displays:")
    print("  - 👤 ПІБ")
    print("  - 🆔 ID")
    print("  - 📱 Telegram")
    print("  - 🟢/🟡/⚫ Availability")
    print("  - 🕒 Last login")
    print("  - 🔒 Персональні дані...")
