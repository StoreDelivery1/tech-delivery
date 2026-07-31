import unittest

from app.bot.handlers.courier import is_free_orders_button


class TestCourierButton(unittest.TestCase):
    def test_accepts_current_and_legacy_button_labels(self):
        self.assertTrue(is_free_orders_button("📦 Вільні заявки"))
        self.assertTrue(is_free_orders_button("📦 Вільні замовлення"))


if __name__ == "__main__":
    unittest.main()
