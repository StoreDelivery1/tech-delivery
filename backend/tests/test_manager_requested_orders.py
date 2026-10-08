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

    def _courier(self, name: str = "Courier") -> User:
        courier = User(
            telegram_id=9001,
            username=name.lower(),
            full_name=name,
            role=UserRole.COURIER,
            status=UserStatus.ACTIVE,
        )
        self.db.add(courier)
        self.db.flush()
        return courier

    def _order(
        self,
        *,
        from_store: Store,
        to_store: Store,
        creator: User,
        status: OrderStatus = OrderStatus.WAITING_FOR_COURIER,
        number: str = "ORD-1",
        courier_id: int | None = None,
    ) -> Order:
        order = Order(
            number=number,
            from_store_id=from_store.id,
            to_store_id=to_store.id,
            created_by=creator.id,
            courier_id=courier_id,
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
        requested_statuses = (
            OrderStatus.WAITING_FOR_COURIER,
            OrderStatus.ACCEPTED,
        )
        orders = [
            self._order(
                from_store=self.source_store,
                to_store=self.requester_store,
                creator=self.requester_manager,
                status=status,
                number=f"ACTIVE-{index}",
            )
            for index, status in enumerate(requested_statuses)
        ]
        self.db.commit()

        result = ManagerService.get_active_orders_requested_from_store(
            self.db,
            self.source_manager.id,
        )

        self.assertEqual({order.id for order in result}, {order.id for order in orders})

    def test_product_orders_picked_up_or_later_are_hidden_from_requested_list(self):
        transferred_statuses = (
            OrderStatus.PICKED_UP,
            OrderStatus.DELIVERING,
            OrderStatus.AWAITING_CONFIRMATION,
            OrderStatus.DELIVERY_PROBLEM,
            OrderStatus.COMPLETED,
            OrderStatus.DELIVERED,
            OrderStatus.CANCELED,
        )
        for index, status in enumerate(transferred_statuses):
            self._order(
                from_store=self.source_store,
                to_store=self.requester_store,
                creator=self.requester_manager,
                status=status,
                number=f"TRANSFERRED-{index}",
            )
        self.db.commit()

        result = ManagerService.get_active_orders_requested_from_store(
            self.db,
            self.source_manager.id,
        )

        self.assertEqual(result, [])

    def test_accepted_product_order_is_hidden_from_incoming_until_pickup_but_regular_is_not(self):
        courier = self._courier()
        product_order = self._order(
            from_store=self.source_store,
            to_store=self.requester_store,
            creator=self.requester_manager,
            status=OrderStatus.ACCEPTED,
            number="PRODUCT-ACCEPTED",
            courier_id=courier.id,
        )
        regular_order = self._order(
            from_store=self.source_store,
            to_store=self.requester_store,
            creator=self.source_manager,
            status=OrderStatus.ACCEPTED,
            number="REGULAR-ACCEPTED",
            courier_id=courier.id,
        )
        picked_up_product_order = self._order(
            from_store=self.source_store,
            to_store=self.requester_store,
            creator=self.requester_manager,
            status=OrderStatus.PICKED_UP,
            number="PRODUCT-PICKED-UP",
            courier_id=courier.id,
        )
        self.db.commit()

        incoming = ManagerService.get_incoming_active_deliveries(
            self.db,
            self.requester_manager.id,
        )
        incoming_ids = {order.id for order in incoming}

        self.assertNotIn(product_order.id, incoming_ids)
        self.assertIn(regular_order.id, incoming_ids)
        self.assertIn(picked_up_product_order.id, incoming_ids)
        self.assertEqual(
            ManagerService.get_incoming_delivery_count(self.db, self.requester_manager.id),
            len(incoming),
        )

    def test_transfer_moves_product_order_to_picked_up_and_between_lists(self):
        courier = self._courier()
        order = self._order(
            from_store=self.source_store,
            to_store=self.requester_store,
            creator=self.requester_manager,
            status=OrderStatus.ACCEPTED,
            courier_id=courier.id,
        )
        self.db.commit()

        transferred = ManagerService.transfer_requested_product_order_to_courier(
            self.db,
            self.source_manager.id,
            order.id,
        )

        self.assertEqual(transferred.status, OrderStatus.PICKED_UP)
        self.assertEqual(transferred.courier_id, courier.id)
        self.assertEqual(
            ManagerService.get_active_orders_requested_from_store(self.db, self.source_manager.id),
            [],
        )
        self.assertEqual(
            [item.id for item in ManagerService.get_incoming_active_deliveries(self.db, self.requester_manager.id)],
            [order.id],
        )
        with self.assertRaisesRegex(ValueError, "Only accepted"):
            ManagerService.transfer_requested_product_order_to_courier(
                self.db,
                self.source_manager.id,
                order.id,
            )
        self.assertEqual(order.status, OrderStatus.PICKED_UP)

    def test_transfer_rejects_invalid_cases_without_changing_status(self):
        courier = self._courier()
        wrong_store_order = self._order(
            from_store=self.source_store,
            to_store=self.requester_store,
            creator=self.requester_manager,
            status=OrderStatus.ACCEPTED,
            number="WRONG-STORE",
            courier_id=courier.id,
        )
        no_courier_order = self._order(
            from_store=self.source_store,
            to_store=self.requester_store,
            creator=self.requester_manager,
            status=OrderStatus.ACCEPTED,
            number="NO-COURIER",
        )
        waiting_order = self._order(
            from_store=self.source_store,
            to_store=self.requester_store,
            creator=self.requester_manager,
            status=OrderStatus.WAITING_FOR_COURIER,
            number="WAITING",
            courier_id=courier.id,
        )
        regular_order = self._order(
            from_store=self.source_store,
            to_store=self.requester_store,
            creator=self.source_manager,
            status=OrderStatus.ACCEPTED,
            number="REGULAR",
            courier_id=courier.id,
        )
        self.db.commit()

        cases = (
            (self.other_manager.id, wrong_store_order, "does not belong"),
            (self.source_manager.id, no_courier_order, "no assigned courier"),
            (self.source_manager.id, waiting_order, "Only accepted"),
            (self.source_manager.id, regular_order, "not a product request"),
        )
        for manager_id, order, error in cases:
            original_status = order.status
            with self.subTest(order=order.number):
                with self.assertRaisesRegex(ValueError, error):
                    ManagerService.transfer_requested_product_order_to_courier(
                        self.db,
                        manager_id,
                        order.id,
                    )
                self.assertEqual(order.status, original_status)

    def test_transfer_rejects_inactive_manager_without_changing_status(self):
        courier = self._courier()
        order = self._order(
            from_store=self.source_store,
            to_store=self.requester_store,
            creator=self.requester_manager,
            status=OrderStatus.ACCEPTED,
            courier_id=courier.id,
        )
        self.source_manager.status = UserStatus.INACTIVE
        self.db.commit()

        with self.assertRaisesRegex(ValueError, "not active"):
            ManagerService.transfer_requested_product_order_to_courier(
                self.db,
                self.source_manager.id,
                order.id,
            )
        self.assertEqual(order.status, OrderStatus.ACCEPTED)

    def test_transfer_rejects_missing_order_and_invalid_manager_identity(self):
        courier = self._courier()
        order = self._order(
            from_store=self.source_store,
            to_store=self.requester_store,
            creator=self.requester_manager,
            status=OrderStatus.ACCEPTED,
            courier_id=courier.id,
        )
        unassigned_manager = User(
            telegram_id=9100,
            username="unassigned",
            full_name="Unassigned Manager",
            role=UserRole.MANAGER,
            status=UserStatus.ACTIVE,
        )
        self.db.add(unassigned_manager)
        self.db.commit()

        with self.assertRaisesRegex(ValueError, "Order not found"):
            ManagerService.transfer_requested_product_order_to_courier(
                self.db,
                self.source_manager.id,
                999999,
            )
        with self.assertRaisesRegex(ValueError, "not a manager"):
            ManagerService.transfer_requested_product_order_to_courier(
                self.db,
                courier.id,
                order.id,
            )
        with self.assertRaisesRegex(ValueError, "not assigned to a store"):
            ManagerService.transfer_requested_product_order_to_courier(
                self.db,
                unassigned_manager.id,
                order.id,
            )
        self.assertEqual(order.status, OrderStatus.ACCEPTED)

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