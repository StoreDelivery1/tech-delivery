import unittest
from datetime import datetime, timedelta
import re
from unittest.mock import Mock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.order import Order
from app.models.store import Store, StoreNetwork
from app.models.user import User, UserRole, UserStatus
from app.services.activation_service import ActivationService


class TestActivationService(unittest.TestCase):
    def test_get_manager_includes_active_seller_but_rejects_inactive_seller(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        db = Session(engine)
        store = Store(
            name="Test Store",
            address="Address",
            city="Lviv",
            latitude=49.0,
            longitude=24.0,
            network=StoreNetwork.APPLE_ROOM,
        )
        db.add(store)
        db.flush()
        active_seller = User(
            telegram_id=501,
            full_name="Active Seller",
            role=UserRole.SELLER,
            status=UserStatus.ACTIVE,
            store_id=store.id,
        )
        inactive_seller = User(
            telegram_id=502,
            full_name="Inactive Seller",
            role=UserRole.SELLER,
            status=UserStatus.INACTIVE,
            store_id=store.id,
        )
        db.add_all([active_seller, inactive_seller])
        db.commit()

        self.assertEqual(ActivationService.get_manager(db, 501).role, UserRole.SELLER)
        self.assertIsNone(ActivationService.get_manager(db, 502))

        db.close()
        engine.dispose()

    def test_generate_code_has_td_prefix_and_total_length_10(self):
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None

        code = ActivationService.generate_code(db)

        self.assertTrue(code.startswith("TD-"))
        self.assertEqual(len(code), 10)
        self.assertEqual(len(code.split("-", 1)[1]), 7)

    def test_generate_code_suffix_contains_only_upper_alnum(self):
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None

        code = ActivationService.generate_code(db)
        suffix = code.split("-", 1)[1]

        self.assertIsNotNone(re.fullmatch(r"[A-Z0-9]{7}", suffix))

    def test_generate_code_uses_secrets_choice(self):
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.services.activation_service.secrets.choice", return_value="A") as secure_choice:
            code = ActivationService.generate_code(db)

        self.assertEqual(code, "TD-AAAAAAA")
        self.assertGreaterEqual(secure_choice.call_count, 7)

    def test_generate_code_values_are_not_deterministically_identical(self):
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None

        with patch(
            "app.services.activation_service.secrets.choice",
            side_effect=[
                "A", "A", "A", "A", "A", "A", "A",
                "B", "B", "B", "B", "B", "B", "B",
            ],
        ):
            first = ActivationService.generate_code(db)
            second = ActivationService.generate_code(db)

        self.assertNotEqual(first, second)

    def test_generate_code_retries_on_collision(self):
        db = Mock()
        first_existing = User(full_name="Existing", activation_code="TD-AAAAAAA")
        db.query.return_value.filter.return_value.first.side_effect = [first_existing, None]

        with patch(
            "app.services.activation_service.secrets.choice",
            side_effect=[
                "A", "A", "A", "A", "A", "A", "A",
                "B", "B", "B", "B", "B", "B", "B",
            ],
        ):
            code = ActivationService.generate_code(db)

        self.assertEqual(code, "TD-BBBBBBB")

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
            activation_code="TD-EXPR123",
            activation_code_expires_at=datetime.now() - timedelta(seconds=1),
        )

        with self.assertRaises(ValueError):
            ActivationService.activate(
                db=db,
                user=user,
                telegram_id=123456,
                username="expired_user",
            )

    def test_reset_telegram_assigns_60_minute_expiry(self):
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None
        user = User(full_name="Reset User", telegram_id=999, username="reset")

        before = datetime.now()
        ActivationService.reset_telegram(db, user)
        after = datetime.now()

        self.assertIsNone(user.telegram_id)
        self.assertIsNone(user.username)
        self.assertIsNotNone(user.activation_code)
        self.assertTrue(user.activation_code.startswith("TD-"))
        self.assertEqual(len(user.activation_code), 10)
        self.assertGreaterEqual(user.activation_code_expires_at, before + timedelta(minutes=59, seconds=50))
        self.assertLessEqual(user.activation_code_expires_at, after + timedelta(minutes=60, seconds=10))


if __name__ == "__main__":
    unittest.main()
