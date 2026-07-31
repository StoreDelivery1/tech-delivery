"""
Verify Courier button text vs handler decorator text
Compare byte-for-byte for exact match
"""

import sys
import unicodedata

print("=" * 80)
print("BUTTON TEXT vs HANDLER DECORATOR COMPARISON")
print("=" * 80)

# Button text from keyboards/main_menu.py line 118
button_text = "📊 Статистика"

# Handler decorator text from handlers/courier.py line 450
handler_text = "📊 Статистика"

print("\n1. BUTTON TEXT (from keyboards/main_menu.py:118)")
print("-" * 80)
print(f"String:           '{button_text}'")
print(f"Repr:             {repr(button_text)}")
print(f"Length:           {len(button_text)} characters")
print(f"Bytes (UTF-8):    {button_text.encode('utf-8')}")
print(f"Byte length:      {len(button_text.encode('utf-8'))} bytes")

print("\n2. HANDLER DECORATOR TEXT (from handlers/courier.py:450)")
print("-" * 80)
print(f"String:           '{handler_text}'")
print(f"Repr:             {repr(handler_text)}")
print(f"Length:           {len(handler_text)} characters")
print(f"Bytes (UTF-8):    {handler_text.encode('utf-8')}")
print(f"Byte length:      {len(handler_text.encode('utf-8'))} bytes")

print("\n3. CHARACTER-BY-CHARACTER ANALYSIS")
print("-" * 80)

button_chars = list(button_text)
handler_chars = list(handler_text)

print(f"Button has {len(button_chars)} characters")
print(f"Handler has {len(handler_chars)} characters")

if len(button_chars) == len(handler_chars):
    print("\n✓ Same number of characters")
    for i, (bc, hc) in enumerate(zip(button_chars, handler_chars)):
        if bc == hc:
            print(f"  [{i}] '{bc}' == '{hc}' ✓ (U+{ord(bc):04X})")
        else:
            print(f"  [{i}] '{bc}' != '{hc}' ✗ (U+{ord(bc):04X} vs U+{ord(hc):04X})")
else:
    print(f"\n✗ Different number of characters: {len(button_chars)} vs {len(handler_chars)}")
    for i in range(max(len(button_chars), len(handler_chars))):
        bc = button_chars[i] if i < len(button_chars) else "MISSING"
        hc = handler_chars[i] if i < len(handler_chars) else "MISSING"
        if bc == hc:
            print(f"  [{i}] '{bc}' == '{hc}' ✓")
        else:
            print(f"  [{i}] '{bc}' != '{hc}' ✗")

print("\n4. UNICODE NORMALIZATION CHECK")
print("-" * 80)

button_nfc = unicodedata.normalize('NFC', button_text)
button_nfd = unicodedata.normalize('NFD', button_text)
handler_nfc = unicodedata.normalize('NFC', handler_text)
handler_nfd = unicodedata.normalize('NFD', handler_text)

print(f"Button NFC:  {repr(button_nfc)}")
print(f"Handler NFC: {repr(handler_nfc)}")
print(f"Button NFD:  {repr(button_nfd)}")
print(f"Handler NFD: {repr(handler_nfd)}")

print("\n5. EXACT COMPARISON")
print("-" * 80)

if button_text == handler_text:
    print("✓ IDENTICAL - Strings are exactly equal")
else:
    print("✗ DIFFERENT - Strings are NOT equal")
    print(f"  Button == Handler: {button_text == handler_text}")
    print(f"  Button repr:       {repr(button_text)}")
    print(f"  Handler repr:      {repr(handler_text)}")

if button_text.encode('utf-8') == handler_text.encode('utf-8'):
    print("✓ IDENTICAL - UTF-8 bytes are exactly equal")
else:
    print("✗ DIFFERENT - UTF-8 bytes are NOT equal")

print("\n6. BYTE-FOR-BYTE COMPARISON")
print("-" * 80)

button_bytes = button_text.encode('utf-8')
handler_bytes = handler_text.encode('utf-8')

print(f"Button bytes:  {button_bytes}")
print(f"Handler bytes: {handler_bytes}")
print(f"Bytes equal:   {button_bytes == handler_bytes}")

if button_bytes != handler_bytes:
    print("\n✗ BYTES DIFFER - Showing differences:")
    for i, (bb, hb) in enumerate(zip(button_bytes, handler_bytes)):
        if bb != hb:
            print(f"  Position {i}: {bb:02x} vs {hb:02x} ({chr(bb) if 32 <= bb < 127 else '?'} vs {chr(hb) if 32 <= hb < 127 else '?'})")
    if len(button_bytes) != len(handler_bytes):
        print(f"  Length difference: {len(button_bytes)} vs {len(handler_bytes)}")

print("\n7. CONCLUSION")
print("-" * 80)

if button_text == handler_text and button_bytes == handler_bytes:
    print("✓ VERIFICATION PASSED")
    print("  Button text and handler decorator text are IDENTICAL")
    print("  No Unicode variations or hidden characters detected")
    print("  The routing conflict is NOT caused by text mismatch")
else:
    print("✗ VERIFICATION FAILED")
    print("  Button text and handler decorator text are DIFFERENT")
    print("  This could explain the routing issue")
    print("\nDifferences found:")
    if button_text != handler_text:
        print(f"  String comparison: NOT EQUAL")
    if button_bytes != handler_bytes:
        print(f"  Byte comparison: NOT EQUAL")

print("\n" + "=" * 80)
