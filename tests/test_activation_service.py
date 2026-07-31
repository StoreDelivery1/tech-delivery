import unittest
from unittest.mock import Mock

from app.models.user import User
from app.services.activation_service import ActivationService


class TestActivationService(unittest.TestCase):
    def test_assign_activation_code_uses_naive_datetime(self):
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None
        user = User(full_name="Test User")

        ActivationService.assign_activation_code(db, user)

        self.assertIsNotNone(user.activation_code_expires_at)
        self.assertIsNone(user.activation_code_expires_at.tzinfo)


if __name__ == "__main__":
    unittest.main()
