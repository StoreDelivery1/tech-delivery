import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.core.security import get_current_user
from app.models.user import User, UserRole, UserStatus


class _FakeDb:
    def __init__(self, user):
        self._user = user

    def get(self, model, key):
        return self._user


class TestCurrentUserSecurity(unittest.TestCase):
    def test_inactive_http_jwt_user_is_rejected(self):
        inactive_user = User(
            id=1,
            full_name="Inactive",
            role=UserRole.MANAGER,
            status=UserStatus.INACTIVE,
            telegram_id=100,
        )

        with patch("app.core.security.decode_access_token", return_value={"sub": "1"}):
            with self.assertRaises(HTTPException) as ctx:
                get_current_user(token="token", db=_FakeDb(inactive_user))

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "User is inactive")


if __name__ == "__main__":
    unittest.main()
