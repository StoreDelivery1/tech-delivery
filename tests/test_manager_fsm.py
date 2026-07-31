import unittest

from app.bot.handlers.manager import (
    build_size_keyboard,
    get_manager_order_error,
    is_priority_control_message,
)
from app.models.order import OrderSize


class TestManagerFSM(unittest.TestCase):
    def test_manager_without_store_returns_friendly_error(self):
        class Manager:
            store_id = None

        self.assertEqual(
            get_manager_order_error(Manager()),
            "❌ Ви не прив'язані до жодного магазину.\n\nБудь ласка, зверніться до адміністратора.",
        )

    def test_control_messages_are_not_priority(self):
        self.assertTrue(is_priority_control_message("⬅️ Змінити мережу"))

    def test_size_keyboard_contains_all_options(self):
        keyboard = build_size_keyboard()
        labels = [button.text for row in keyboard.inline_keyboard for button in row]

        self.assertIn("🟢 Мале (0,2–5 кг)", labels)
        self.assertIn("🟡 Середнє (5,1–15 кг)", labels)
        self.assertIn("🔴 Габарит (понад 15 кг)", labels)

    def test_order_size_enum_values_are_available(self):
        self.assertEqual(OrderSize.SMALL.value, "SMALL")
        self.assertEqual(OrderSize.MEDIUM.value, "MEDIUM")
        self.assertEqual(OrderSize.LARGE.value, "LARGE")


if __name__ == "__main__":
    unittest.main()
