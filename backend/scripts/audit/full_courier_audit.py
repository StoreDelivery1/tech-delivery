import re
import sys

code = open('app/bot/handlers/courier.py').read()

# Requirements checklist
requirements = {
    'displays_full_name': False,
    'displays_id': False,
    'displays_telegram': False,
    'displays_availability': False,
    'displays_last_login': False,
    'displays_account_note': False,
    'has_pro_akaunt_button': False,
    'has_back_button': False,
    'no_store_field': True,
    'no_network_field': True,
    'no_store_button': True,
    'back_button_uses_courier_menu': False,
}

# Get profile message function
profile_start = code.find('def _build_courier_profile_message')
profile_end = code.find('def _build_courier_profile_keyboard')
profile_code = code[profile_start:profile_end]

# Check profile message content
if 'courier.full_name' in profile_code:
    requirements['displays_full_name'] = True
if 'courier.id' in profile_code:
    requirements['displays_id'] = True
if 'courier.username' in profile_code:
    requirements['displays_telegram'] = True
if '_fmt_availability' in profile_code:
    requirements['displays_availability'] = True
if 'last_login' in profile_code:
    requirements['displays_last_login'] = True
if 'Персональні дані' in profile_code:
    requirements['displays_account_note'] = True
if 'store' in profile_code.lower():
    requirements['no_store_field'] = False
if 'network' in profile_code.lower():
    requirements['no_network_field'] = False

# Get keyboard
keyboard_start = code.find('def _build_courier_profile_keyboard')
keyboard_end = code.find('async def courier_profile_handler', keyboard_start)
keyboard_code = code[keyboard_start:keyboard_end]

# Check buttons
if 'Про акаунт' in keyboard_code:
    requirements['has_pro_akaunt_button'] = True
if 'Назад' in keyboard_code:
    requirements['has_back_button'] = True
if 'Мій магазин' in keyboard_code:
    requirements['no_store_button'] = False

# Check back button handler
back_handler_start = code.find('@router.callback_query(F.data == "courier_back_to_menu")')
back_handler_end = code.find('db.close()', back_handler_start) + len('db.close()')
back_handler = code[back_handler_start:back_handler_end]

if 'courier_main_menu(courier)' in back_handler:
    requirements['back_button_uses_courier_menu'] = True

# Report
print("Courier Profile Audit Results")
print("=" * 50)
all_pass = True
for req, value in requirements.items():
    status = "✅" if value else "❌"
    print(f"{status} {req}: {value}")
    if not value:
        all_pass = False

print("=" * 50)
if all_pass:
    print("✅ All requirements met - no changes needed")
    sys.exit(0)
else:
    print("❌ Issues found - changes required")
    sys.exit(1)
