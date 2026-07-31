import re

code = open('app/bot/handlers/courier.py').read()

print("Courier Statistics Module Verification")
print("=" * 60)

# Find statistics functions
requirements = {
    'Has _get_courier_orders_for_date_range': False,
    'Has _calculate_courier_statistics': False,
    'Has _build_courier_statistics_message': False,
    'Has _build_courier_statistics_keyboard': False,
    'Has courier_statistics_handler': False,
    'Has courier_statistics_callback': False,
    'Has courier_stats_back handler': False,
}

for req in requirements:
    if req == 'Has _get_courier_orders_for_date_range':
        if '_get_courier_orders_for_date_range' in code:
            requirements[req] = True
    elif req == 'Has _calculate_courier_statistics':
        if '_calculate_courier_statistics' in code:
            requirements[req] = True
    elif req == 'Has _build_courier_statistics_message':
        if '_build_courier_statistics_message' in code:
            requirements[req] = True
    elif req == 'Has _build_courier_statistics_keyboard':
        if '_build_courier_statistics_keyboard' in code:
            requirements[req] = True
    elif req == 'Has courier_statistics_handler':
        if 'async def courier_statistics_handler' in code:
            requirements[req] = True
    elif req == 'Has courier_statistics_callback':
        if 'async def courier_statistics_callback' in code:
            requirements[req] = True
    elif req == 'Has courier_stats_back handler':
        if 'async def courier_stats_back' in code:
            requirements[req] = True

# Statistics content checks
stats_start = code.find('def _get_courier_orders_for_date_range')
stats_end = code.find('def _build_courier_statistics_message')
stats_func = code[stats_start:stats_end]

content_checks = {
    'Filters by Order.courier_id': 'Order.courier_id == courier_id' in stats_func,
    'Date range support (today)': 'date_range == "today"' in stats_func,
    'Date range support (month)': 'date_range == "month"' in stats_func,
    'No system-wide stats': 'WAITING_FOR_COURIER' not in stats_func,
}

message_start = code.find('def _build_courier_statistics_message')
message_end = code.find('def _build_courier_statistics_keyboard')
message_func = code[message_start:message_end]

msg_checks = {
    'Displays "Моя статистика"': 'Моя статистика' in message_func,
    'Displays "Виконано доставок"': 'Виконано доставок' in message_func,
    'Displays "Активних доставок"': 'Активних доставок' in message_func,
    'NO manager stats': 'manager' not in message_func.lower(),
    'NO admin stats': 'admin' not in message_func.lower(),
}

kb_start = code.find('def _build_courier_statistics_keyboard')
kb_end = code.find('@router.message(F.text == "📊 Статистика")')
kb_func = code[kb_start:kb_end]

kb_checks = {
    'Button: 📅 Сьогодні': 'Сьогодні' in kb_func,
    'Button: 📆 Цей місяць': 'Цей місяць' in kb_func,
    'Button: 🏆 За весь час': 'За весь час' in kb_func,
    'Button: ⬅️ Назад': 'Назад' in kb_func,
    'Uses courier_stats: prefix': 'courier_stats:' in kb_func,
    'Back uses courier_stats_back': 'courier_stats_back' in kb_func,
}

handler_start = code.find('@router.message(F.text == "📊 Статистика")')
handler_end = code.find('@router.callback_query(F.data.startswith("courier_stats:"')
handler = code[handler_start:handler_end]

handler_checks = {
    'Handler filters by current courier': 'ActivationService.get_by_telegram' in handler,
    'Gets courier orders for date range': '_get_courier_orders_for_date_range' in handler,
    'Calculates statistics': '_calculate_courier_statistics' in handler,
    'Uses courier_main_menu': 'courier_main_menu' in code[code.find('courier_stats_back'):code.find('courier_stats_back')+1000],
    'No manager_main_menu': 'manager_main_menu' not in code[code.find('courier_stats_back'):code.find('courier_stats_back')+1000],
    'No admin_main_menu': 'admin_main_menu' not in code[code.find('courier_stats_back'):code.find('courier_stats_back')+1000],
}

for category, checks in [
    ('FUNCTIONS', requirements),
    ('STATISTICS LOGIC', content_checks),
    ('MESSAGE CONTENT', msg_checks),
    ('BUTTONS', kb_checks),
    ('HANDLERS', handler_checks),
]:
    print(f"\n{category}:")
    for check, result in checks.items():
        print(f"  {'✅' if result else '❌'} {check}")

all_pass = all([all(v for v in checks.values()) for checks in [requirements, content_checks, msg_checks, kb_checks, handler_checks]])
print("\n" + "=" * 60)
if all_pass:
    print("✅ ALL REQUIREMENTS MET")
else:
    print("❌ SOME REQUIREMENTS NOT MET")
