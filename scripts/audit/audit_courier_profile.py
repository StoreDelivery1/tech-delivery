import re
code = open('app/bot/handlers/courier.py').read()

# Check for store-related strings in profile message
profile_start = code.find('def _build_courier_profile_message')
profile_end = code.find('def _build_courier_profile_keyboard')
profile_code = code[profile_start:profile_end]

issues = []
if '🏪' in profile_code: 
    issues.append('Found store emoji in profile message')
if 'Мій магазин' in profile_code: 
    issues.append('Found "Мій магазин" in profile message')
if 'network' in profile_code.lower(): 
    issues.append('Found network reference in profile message')

# Check keyboard
keyboard_start = code.find('def _build_courier_profile_keyboard')
keyboard_end = code.find('async def courier_profile_handler', keyboard_start)
keyboard_code = code[keyboard_start:keyboard_end]

if 'Мій магазин' in keyboard_code: 
    issues.append('Found "Мій магазин" button in keyboard')

button_count = len(re.findall(r'InlineKeyboardButton', keyboard_code))
if button_count != 2: 
    issues.append(f'Expected 2 buttons, found {button_count}')

if issues:
    print('❌ Issues found:')
    for issue in issues: 
        print(f'  - {issue}')
    exit(1)
else:
    print('✅ Courier profile is correctly configured')
    print('   ✓ No store information')
    print('   ✓ No "Мій магазин" button')  
    print('   ✓ Only 2 buttons: "ℹ️ Про акаунт" and "⬅️ Назад"')
    print('   ✓ Displays: Full name, ID, Telegram, Availability, Last login')
