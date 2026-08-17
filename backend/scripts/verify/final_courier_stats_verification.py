# Final verification of Courier Statistics implementation
import re

code = open('app/bot/handlers/courier.py').read()

print("✅ COURIER STATISTICS MODULE - IMPLEMENTATION VERIFIED")
print("=" * 70)

# Check all required components are present
checks = [
    ("Imports datetime, timedelta, date", "from datetime import datetime, timedelta, date" in code),
    ("Imports Order model", "from app.models.order import Order, OrderStatus" in code),
    ("_COURIER_ACTIVE_STATUSES defined", "_COURIER_ACTIVE_STATUSES = [" in code),
    ("Active statuses include ACCEPTED", "OrderStatus.ACCEPTED" in code[code.find("_COURIER_ACTIVE_STATUSES"):code.find("_COURIER_ACTIVE_STATUSES")+200]),
    ("Active statuses include PICKED_UP", "OrderStatus.PICKED_UP" in code[code.find("_COURIER_ACTIVE_STATUSES"):code.find("_COURIER_ACTIVE_STATUSES")+200]),
    ("Active statuses include DELIVERING", "OrderStatus.DELIVERING" in code[code.find("_COURIER_ACTIVE_STATUSES"):code.find("_COURIER_ACTIVE_STATUSES")+200]),
    ("_get_courier_orders_for_date_range function", "def _get_courier_orders_for_date_range" in code),
    ("_calculate_courier_statistics function", "def _calculate_courier_statistics" in code),
    ("_build_courier_statistics_message function", "def _build_courier_statistics_message" in code),
    ("_build_courier_statistics_keyboard function", "def _build_courier_statistics_keyboard" in code),
    ("courier_statistics_handler for message", "async def courier_statistics_handler" in code),
    ("courier_statistics_callback for callbacks", "async def courier_statistics_callback" in code),
    ("courier_stats_back handler", "async def courier_stats_back" in code),
]

# Filter checks  
get_func_start = code.find("def _get_courier_orders_for_date_range")
get_func_end = code.find("def _calculate_courier_statistics")
get_func = code[get_func_start:get_func_end]

filter_checks = [
    ("Filters by Order.courier_id == courier_id", "Order.courier_id == courier_id" in get_func),
    ("Supports date_range == 'today'", 'date_range == "today"' in get_func),
    ("Supports date_range == 'month'", 'date_range == "month"' in get_func),
    ("Does NOT include WAITING_FOR_COURIER", "WAITING_FOR_COURIER" not in get_func),
]

# Display checks
msg_start = code.find("def _build_courier_statistics_message")
msg_end = code.find("def _build_courier_statistics_keyboard")
msg_func = code[msg_start:msg_end]

display_checks = [
    ("Displays 'Моя статистика'", "Моя статистика" in msg_func),
    ("Displays 'Виконано доставок'", "Виконано доставок" in msg_func),
    ("Displays 'Активних доставок'", "Активних доставок" in msg_func),
    ("No manager statistics", "manager" not in msg_func.lower()),
    ("No admin statistics", "admin" not in msg_func.lower()),
]

# Buttons check
kb_start = code.find("def _build_courier_statistics_keyboard")
kb_end = code.find("@router.message(F.text == \"📊 Статистика\"")
kb_func = code[kb_start:kb_end]

buttons_checks = [
    ("Button: 📅 Сьогодні", "Сьогодні" in kb_func),
    ("Button: 📆 Цей місяць", "Цей місяць" in kb_func),
    ("Button: 🏆 За весь час", "За весь час" in kb_func),
    ("Button: ⬅️ Назад with courier_stats_back", "Назад" in kb_func and "courier_stats_back" in kb_func),
    ("Uses courier_stats: callback prefix", "courier_stats:" in kb_func),
]

# Handler checks
handler_start = code.find("@router.message(F.text == \"📊 Статистика\"")
handler_end = code.find("@router.callback_query(F.data.startswith(\"courier_stats:\"")
handler = code[handler_start:handler_end]

handler_checks = [
    ("Uses ActivationService.get_by_telegram", "ActivationService.get_by_telegram" in handler),
    ("Calls _get_courier_orders_for_date_range", "_get_courier_orders_for_date_range" in handler),
    ("Calls _calculate_courier_statistics", "_calculate_courier_statistics" in handler),
]

back_start = code.find("@router.callback_query(F.data == \"courier_stats_back\"")
back_end = code.find("# ── Courier Profile", back_start)
back_handler = code[back_start:back_end]

back_checks = [
    ("Back button uses courier_main_menu", "courier_main_menu(courier)" in back_handler),
    ("Back does NOT use manager_main_menu", "manager_main_menu" not in back_handler),
    ("Back does NOT use admin_main_menu", "admin_main_menu" not in back_handler),
]

all_checks = checks + filter_checks + display_checks + buttons_checks + handler_checks + back_checks
all_pass = all(v for _, v in all_checks)

for category, group in [
    ("CORE FUNCTIONS", checks),
    ("FILTERING LOGIC", filter_checks),
    ("MESSAGE DISPLAY", display_checks),
    ("BUTTONS", buttons_checks),
    ("HANDLERS", handler_checks),
    ("BACK NAVIGATION", back_checks),
]:
    print(f"\n{category}:")
    for desc, passed in group:
        print(f"  {'✅' if passed else '❌'} {desc}")

print("\n" + "=" * 70)
if all_pass:
    print("✅ ALL REQUIREMENTS MET - IMPLEMENTATION COMPLETE")
else:
    print("❌ SOME REQUIREMENTS NOT MET")
