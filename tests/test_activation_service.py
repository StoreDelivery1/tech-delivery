import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.models.user import User
from app.services.activation_service import ActivationService


class TestActivationService(unittest.TestCase):
    def test_generate_code_has_exactly_7_chars(self):
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None

        code = ActivationService.generate_code(db)

        self.assertEqual(len(code), 7)
        self.assertTrue(code.startswith("TD-"))

    def test_generate_code_uses_secrets_choice(self):
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.services.activation_service.secrets.choice", return_value="A") as secure_choice:
            code = ActivationService.generate_code(db)

        self.assertEqual(code, "TD-AAAA")
        self.assertGreaterEqual(secure_choice.call_count, 4)

    def test_generate_code_retries_on_collision(self):
        db = Mock()
        first_existing = User(full_name="Existing", activation_code="TD-AAAA")
        db.query.return_value.filter.return_value.first.side_effect = [first_existing, None]

        with patch("app.services.activation_service.secrets.choice", side_effect=["A", "A", "A", "A", "B", "B", "B", "B"]):
            code = ActivationService.generate_code(db)

        self.assertEqual(code, "TD-BBBB")

    def test_assign_activation_code_lifetime_is_one_hour(self):
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None
        user = User(full_name="Test User")

        before = datetime.now()
        ActivationService.assign_activation_code(db, user)
        after = datetime.now()

        self.assertIsNotNone(user.activation_code_expires_at)
        self.assertGreaterEqual(user.activation_code_expires_at, before + timedelta(minutes=59, seconds=50))
        self.assertLessEqual(user.activation_code_expires_at, after + timedelta(minutes=60, seconds=10))

    def test_assign_activation_code_uses_naive_datetime(self):
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None
        user = User(full_name="Test User")

        ActivationService.assign_activation_code(db, user)

        self.assertIsNotNone(user.activation_code_expires_at)
        self.assertIsNone(user.activation_code_expires_at.tzinfo)

    def test_activate_rejects_expired_code(self):
        db = Mock()
        user = User(
            full_name="Expired User",
            activation_code="TD-EXPR",
            activation_code_expires_at=datetime.now() - timedelta(seconds=1),
        )

        with self.assertRaises(ValueError):
            ActivationService.activate(
                db=db,
                user=user,
                telegram_id=123456,
                username="expired_user",
            )


if __name__ == "__main__":
    unittest.main()
