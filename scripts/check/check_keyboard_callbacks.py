with open('app/bot/handlers/courier.py', 'rb') as f:
    content = f.read()
    
# Find the line with "Назад" and callback_data in the profile keyboard
import re
text = content.decode('utf-8')

# Get the profile keyboard section
start_idx = text.find('def _build_courier_profile_keyboard')
end_idx = text.find('async def courier_profile_handler', start_idx)
section = text[start_idx:end_idx]

# Find all callback_data in this section
callbacks = re.findall(r'callback_data="([^"]+)"', section)
print("Callbacks in _build_courier_profile_keyboard():")
for cb in callbacks:
    print(f"  {cb}")

# Find the exact back button callback
back_match = re.search(r'text="[^"]*Назад[^"]*"[^}]*?callback_data="([^"]+)"', section, re.DOTALL)
if back_match:
    print(f"\nBack button callback_data: {back_match.group(1)}")
