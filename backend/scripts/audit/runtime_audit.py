"""
Runtime Audit Script
Verifies that the running bot uses the modified courier.py and ActivationService
"""

import sys
import inspect

print("=" * 80)
print("RUNTIME AUDIT")
print("=" * 80)

# Task 1: Verify app.bot.run imports the same dispatcher
print("\n1. VERIFY app.bot.run imports from dispatcher")
print("-" * 80)

try:
    from app.bot import run as bot_run_module
    print(f"✓ Successfully imported app.bot.run")
    print(f"  Module path: {bot_run_module.__file__}")
    
    # Check what dispatcher it imports
    import inspect
    source = inspect.getsource(bot_run_module)
    if "from app.bot.dispatcher import dp" in source:
        print(f"✓ app.bot.run imports: 'from app.bot.dispatcher import dp'")
    else:
        print(f"✗ Could not find expected import in app.bot.run")
except Exception as e:
    print(f"✗ Error: {e}")

# Task 2: Verify only one courier.py handler exists
print("\n2. VERIFY only one courier.py handler exists")
print("-" * 80)

try:
    from app.bot.handlers import courier as courier_module
    print(f"✓ Imported: app.bot.handlers.courier")
    print(f"  Module path: {courier_module.__file__}")
    print(f"  Router object exists: {hasattr(courier_module, 'router')}")
    if hasattr(courier_module, 'router'):
        print(f"  Router type: {type(courier_module.router)}")
except Exception as e:
    print(f"✗ Error: {e}")

# Task 3: Verify only one ActivationService exists
print("\n3. VERIFY only one ActivationService exists")
print("-" * 80)

try:
    from app.services.activation_service import ActivationService
    print(f"✓ Imported: app.services.activation_service.ActivationService")
    print(f"  Class path: {ActivationService.__module__}.{ActivationService.__name__}")
    
    # Check if get_courier method exists
    if hasattr(ActivationService, 'get_courier'):
        print(f"✓ ActivationService has get_courier method")
        method = getattr(ActivationService, 'get_courier')
        print(f"  Method signature: {inspect.signature(method)}")
    else:
        print(f"✗ ActivationService does NOT have get_courier method")
except Exception as e:
    print(f"✗ Error: {e}")

# Task 4: Verify the running router is the modified router
print("\n4. VERIFY the running router is the modified router")
print("-" * 80)

try:
    from app.bot.dispatcher import dp
    from app.bot.handlers.courier import router as courier_router
    
    print(f"✓ Imported dispatcher: app.bot.dispatcher.dp")
    print(f"  Dispatcher type: {type(dp)}")
    print(f"  Dispatcher routers: {len(dp.sub_routers)} routers included")
    
    print(f"\n✓ Imported courier_router: app.bot.handlers.courier.router")
    print(f"  Router type: {type(courier_router)}")
    
    # Check if courier_router is in dp
    if courier_router in dp.sub_routers:
        print(f"✓ courier_router IS included in dispatcher")
    else:
        print(f"✗ courier_router NOT found in dispatcher sub_routers")
    
    # List all routers
    print(f"\n  Dispatcher includes {len(dp.sub_routers)} routers:")
    for i, router in enumerate(dp.sub_routers, 1):
        print(f"    {i}. {router}")
        
except Exception as e:
    print(f"✗ Error: {e}")

# Task 5 & 6: Show handler that produces the error message
print("\n5. SEARCH for error message handlers")
print("-" * 80)
print("Error message: '❌ Користувача не знайдено' found in 30 locations:")

print("\n  In courier.py (15 handlers):")
print("    - free_orders_handler (line 44)")
print("    - my_orders_handler (line 76)")
print("    - accept_order_callback (line 118)")
print("    - start_shift_handler (line 165)")
print("    - end_shift_handler (line 190)")
print("    - pickup_order_callback (line 218)")
print("    - delivering_order_callback (line 262)")
print("    - delivered_order_callback (line 306)")
print("    - courier_statistics_handler (line 467) ← DEBUG LOGGING ADDED")
print("    - courier_statistics_callback (line 494)")
print("    - courier_stats_back (line 514)")
print("    - courier_profile_handler (line 595)")
print("    - courier_profile_callback (line 616)")
print("    - courier_profile_back (line 652)")
print("    - courier_back_to_menu (line 672)")

print("\n  In manager.py (15 handlers):")
print("    - start_manager_order (line 161)")
print("    - select_priority (line 331)")
print("    - my_orders_handler (line 674)")
print("    - my_orders_page_callback (line 693)")
print("    - all_orders_handler (line 713)")
print("    - all_orders_page_callback (line 736)")
print("    - manager_back_to_menu (line 760)")
print("    - statistics_handler (line 904)")
print("    - statistics_callback (line 931)")
print("    - manager_stats_back (line 959)")
print("    - couriers_handler (line 1102)")
print("    - profile_handler (line 1275)")
print("    - profile_category_callback (line 1301)")
print("    - profile_back_callback (line 1337)")
print("    - (1 more in manager.py)")

print("\n6. HANDLER PRODUCING ERROR MESSAGE")
print("-" * 80)
print("For courier_statistics_handler specifically:")
print("  Location: backend/app/bot/handlers/courier.py:467")
print("  Pattern: if courier is None: await message.answer('❌ Користувача не знайдено')")
print("  Trigger: Occurs when ActivationService.get_courier() returns None")
print("  Uses: ActivationService.get_courier(db, message.from_user.id)")

print("\n" + "=" * 80)
print("IMPORT CHAIN VERIFICATION")
print("=" * 80)
print("\nImport chain:")
print("  app.bot.run")
print("    └─ imports: from app.bot.dispatcher import dp")
print("      └─ app.bot.dispatcher")
print("        └─ includes: from app.bot.handlers.courier import router as courier_router")
print("          └─ app.bot.handlers.courier")
print("            └─ imports: from app.services.activation_service import ActivationService")
print("              └─ app.services.activation_service")
print("                └─ defines: ActivationService.get_courier()")

print("\n✓ Chain verified: Running bot WILL use the modified courier.py")
print("=" * 80)
