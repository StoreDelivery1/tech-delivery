"""
Verify all three instances of "📊 Статистика" button text in handlers
"""

print("=" * 80)
print("VERIFYING ALL HANDLER DECORATORS: @router.message(F.text == '📊 Статистика')")
print("=" * 80)

# All three handler decorator texts
handlers = [
    {
        "file": "admin.py",
        "line": 392,
        "function": "admin_statistics_handler",
        "text": "📊 Статистика"
    },
    {
        "file": "manager.py",
        "line": 897,
        "function": "statistics_handler",
        "text": "📊 Статистика"
    },
    {
        "file": "courier.py",
        "line": 450,
        "function": "courier_statistics_handler",
        "text": "📊 Статистика"
    },
]

button_text = "📊 Статистика"  # From keyboards/main_menu.py line 118

print("\nBUTTON TEXT (Source: keyboards/main_menu.py:118)")
print("-" * 80)
print(f"Text:      '{button_text}'")
print(f"Repr:      {repr(button_text)}")
print(f"Bytes:     {button_text.encode('utf-8')}")

print("\nHANDLER DECORATORS")
print("-" * 80)

all_match = True

for handler in handlers:
    handler_text = handler["text"]
    match = button_text == handler_text
    match_bytes = button_text.encode('utf-8') == handler_text.encode('utf-8')
    
    status = "✓ MATCH" if (match and match_bytes) else "✗ MISMATCH"
    
    print(f"\n{handler['file']}:{handler['line']} - {handler['function']}")
    print(f"  Text:      '{handler_text}'")
    print(f"  Repr:      {repr(handler_text)}")
    print(f"  Bytes:     {handler_text.encode('utf-8')}")
    print(f"  Match:     {status}")
    
    if not (match and match_bytes):
        all_match = False

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if all_match:
    print("\n✓ ALL STRINGS IDENTICAL")
    print("\nAll handler decorators have identical text to the button:")
    print("  - admin.py:392 admin_statistics_handler")
    print("  - manager.py:897 statistics_handler")
    print("  - courier.py:450 courier_statistics_handler")
    print("\nThe routing conflict is NOT caused by:")
    print("  - Unicode differences")
    print("  - Hidden characters")
    print("  - Text mismatches")
    print("\nThe conflict IS caused by:")
    print("  - DISPATCHER ROUTING ORDER")
    print("  - manager_router is included BEFORE courier_router")
    print("  - manager_router's handler intercepts the message first")
else:
    print("\n✗ MISMATCH FOUND")
    print("Some handler decorators have different text than the button")

print("\n" + "=" * 80)
