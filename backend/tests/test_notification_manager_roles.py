import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.order import Order
from app.models.store import Store, StoreNetwork
from app.models.user import User, UserRole, UserStatus
from app.services.notification_service import NotificationService


class TestNotificationManagerRoles(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.store = Store(
            name="Test Store",
            address="Address",
            city="Lviv",
            latitude=49.0,
            longitude=24.0,
            network=StoreNetwork.APPLE_ROOM,
        )
        self.db.add(self.store)
        self.db.flush()
        self.manager = User(
            full_name="Manager",
            role=UserRole.MANAGER,
            status=UserStatus.ACTIVE,
            telegram_id=601,
            store_id=self.store.id,
        )
        self.seller = User(
            full_name="Seller",
            role=UserRole.SELLER,
            status=UserStatus.ACTIVE,
            telegram_id=602,
            store_id=self.store.id,
        )
        self.inactive_seller = User(
            full_name="Inactive Seller",
            role=UserRole.SELLER,
            status=UserStatus.INACTIVE,
            telegram_id=603,
            store_id=self.store.id,
        )
        self.unlinked_seller = User(
            full_name="Unlinked Seller",
            role=UserRole.SELLER,
            status=UserStatus.ACTIVE,
            store_id=self.store.id,
        )
        self.db.add_all([self.manager, self.seller, self.inactive_seller, self.unlinked_seller])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def _order(self):
        return SimpleNamespace(
            id=1,
            number="ORDER-1",
            to_store_id=self.store.id,
            to_store=self.store,
            from_store=self.store,
            courier=SimpleNamespace(full_name="Courier", telegram_id=999),
        )

    @staticmethod
    def _recipient_ids(bot):
        return {call.kwargs["chat_id"] for call in bot.send_message.await_args_list}

    def test_incoming_status_notification_reaches_active_manager_and_seller(self):
        bot = AsyncMock()
        with patch.object(NotificationService, "_build_details_keyboard", return_value=None):
            asyncio.run(
                NotificationService.notify_incoming_delivery_status_change(
                    self.db, bot, self._order(), "In transit"
                )
            )

        self.assertEqual(self._recipient_ids(bot), {601, 602})

    def test_arrival_notification_reaches_active_manager_and_seller(self):
        bot = AsyncMock()
        with patch.object(NotificationService, "_build_details_keyboard", return_value=None):
            asyncio.run(NotificationService.notify_incoming_delivery_arrived(self.db, bot, self._order()))

        self.assertEqual(self._recipient_ids(bot), {601, 602})

    def test_delivery_confirmation_request_reaches_active_manager_and_seller(self):
        bot = AsyncMock()
        asyncio.run(
            NotificationService.notify_delivery_confirmation_request(
                self.db, bot, self._order()
            )
        )

        self.assertEqual(self._recipient_ids(bot), {601, 602})


if __name__ == "__main__":
    unittest.main()
