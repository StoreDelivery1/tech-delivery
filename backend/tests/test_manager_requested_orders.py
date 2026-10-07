import unittest

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.order import Order, OrderPriority, OrderStatus
from app.models.store import Store, StoreNetwork
from app.models.user import User, UserRole, UserStatus
from app.services.manager_service import ManagerService


class TestManagerRequestedOrders(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)

        self.requester_store = self._store("Requester Store")
        self.source_store = self._store("Source Store")
        self.other_store = self._store("Other Store")
        self.requester_manager = self._manager("Requester", self.requester_store)
        self.source_manager = self._manager("Source", self.source_store)
        self.other_manager = self._manager("Other", self.other_store)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def _store(self, name: str) -> Store:
        store = Store(
            name=name,
            address=f"{name} address",
            city="Lviv",
            latitude=49.0,
            longitude=24.0,
            network=StoreNetwork.APPLE_ROOM,
        )
        self.db.add(store)
        self.db.flush()
        return store

    def _manager(self, name: str, store: Store) -> User:
        manager = User(
            telegram_id=1000 + store.id,
            username=name.lower(),
            full_name=name,
            role=UserRole.MANAGER,
            status=UserStatus.ACTIVE,
            store_id=store.id,
        )
        self.db.add(manager)
        self.db.flush()
        return manager

    def _order(
        self,
        *,
        from_store: Store,
        to_store: Store,
        creator: User,
        status: OrderStatus = OrderStatus.WAITING_FOR_COURIER,
        number: str = "ORD-1",
    ) -> Order:
        order = Order(
            number=number,
            from_store_id=from_store.id,
            to_store_id=to_store.id,
            created_by=creator.id,
            description="iPhone 17 Pro Max 256GB — 1 шт.",
            priority=OrderPriority.NORMAL,
            status=status,
        )
        self.db.add(order)
        self.db.flush()
        return order

    def test_source_store_sees_product_request_and_requester_does_not(self):
        order = self._order(
            from_store=self.source_store,
            to_store=self.requester_store,
            creator=self.requester_manager,
        )
        self.db.commit()

        source_orders = ManagerService.get_active_orders_requested_from_store(
            self.db,
            self.source_manager.id,
        )
        requester_orders = ManagerService.get_active_orders_requested_from_store(
            self.db,
            self.requester_manager.id,
        )

        self.assertEqual([item.id for item in source_orders], [order.id])
        self.assertEqual(requester_orders, [])

    def test_standard_transfer_created_by_source_store_is_not_a_product_request(self):
        order = self._order(
            from_store=self.requester_store,
            to_store=self.source_store,
            creator=self.requester_manager,
        )
        self.db.commit()

        self.assertEqual(
            ManagerService.get_active_orders_requested_from_store(self.db, self.requester_manager.id),
            [],
        )
        self.assertEqual(
            ManagerService.get_active_orders_requested_from_store(self.db, self.source_manager.id),
            [],
        )
        self.assertIsNotNone(self.db.get(Order, order.id))

    def test_requested_order_active_statuses_are_included(self):
        active_statuses = (
            OrderStatus.WAITING_FOR_COURIER,
            OrderStatus.ACCEPTED,
            OrderStatus.PICKED_UP,
            OrderStatus.DELIVERING,
            OrderStatus.AWAITING_CONFIRMATION,
            OrderStatus.DELIVERY_PROBLEM,
        )
        orders = [
            self._order(
                from_store=self.source_store,
                to_store=self.requester_store,
                creator=self.requester_manager,
                status=status,
                number=f"ACTIVE-{index}",
            )
            for index, status in enumerate(active_statuses)
        ]
        self.db.commit()

        result = ManagerService.get_active_orders_requested_from_store(
            self.db,
            self.source_manager.id,
        )

        self.assertEqual({order.id for order in result}, {order.id for order in orders})

    def test_completed_delivered_and_canceled_orders_are_excluded(self):
        terminal_statuses = (
            OrderStatus.COMPLETED,
            OrderStatus.DELIVERED,
            OrderStatus.CANCELED,
        )
        for index, status in enumerate(terminal_statuses):
            self._order(
                from_store=self.source_store,
                to_store=self.requester_store,
                creator=self.requester_manager,
                status=status,
                number=f"DONE-{index}",
            )
        self.db.commit()

        self.assertEqual(
            ManagerService.get_active_orders_requested_from_store(self.db, self.source_manager.id),
            [],
        )

    def test_another_store_manager_cannot_get_request_details(self):
        order = self._order(
            from_store=self.source_store,
            to_store=self.requester_store,
            creator=self.requester_manager,
        )
        self.db.commit()

        self.assertIsNone(
            ManagerService.get_active_order_requested_from_store(
                self.db,
                self.other_manager.id,
                order.id,
            )
        )
        self.assertEqual(
            ManagerService.get_active_order_requested_from_store(
                self.db,
                self.source_manager.id,
                order.id,
            ).id,
            order.id,
        )

    def test_missing_order_id_returns_none(self):
        self.assertIsNone(
            ManagerService.get_active_order_requested_from_store(
                self.db,
                self.source_manager.id,
                999999,
            )
        )

    def test_requested_orders_eager_load_display_relationships(self):
        order = self._order(
            from_store=self.source_store,
            to_store=self.requester_store,
            creator=self.requester_manager,
        )
        self.db.commit()

        result = ManagerService.get_active_orders_requested_from_store(
            self.db,
            self.source_manager.id,
        )[0]

        self.assertNotIn("from_store", inspect(result).unloaded)
        self.assertNotIn("to_store", inspect(result).unloaded)
        self.assertNotIn("creator", inspect(result).unloaded)
        self.assertNotIn("store", inspect(result.creator).unloaded)
        self.assertEqual(result.id, order.id)
        self.assertEqual(result.creator.store_id, self.requester_store.id)


if __name__ == "__main__":
    unittest.main()