import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.bot.utils.order_formatter import format_order
from app.database.base import Base
from app.models.order import Order, OrderPriority, OrderStatus
from app.models.store import Store, StoreNetwork
from app.models.user import User, UserRole, UserStatus
from app.schemas.order import ManagerOrderCreate
from app.services.courier_service import CourierService
from app.services.order_service import OrderService


class TestCourierAvailableOrders(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)

        self.requester_store = self._create_store("Requester Store")
        self.source_store = self._create_store("Source Store")
        self.manager = User(
            telegram_id=1001,
            username="manager",
            full_name="Store Manager",
            role=UserRole.MANAGER,
            status=UserStatus.ACTIVE,
            store_id=self.requester_store.id,
        )
        self.db.add(self.manager)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def _create_store(self, name: str) -> Store:
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

    def test_regular_and_product_orders_share_courier_available_list_and_format(self):
        regular_order = OrderService.create_order(
            db=self.db,
            order=ManagerOrderCreate(
                to_store_id=self.source_store.id,
                description="Regular shipment item",
            ),
            current_user=self.manager,
        )
        product_order = OrderService.create_order_with_stores(
            db=self.db,
            current_user=self.manager,
            from_store_id=self.source_store.id,
            to_store_id=self.requester_store.id,
            description="iPhone 17 Pro Max 256GB — 1 шт.",
        )
        unavailable_order = Order(
            number="NON-WAITING-ORDER",
            from_store_id=self.source_store.id,
            to_store_id=self.requester_store.id,
            created_by=self.manager.id,
            description="Already assigned shipment",
            priority=OrderPriority.NORMAL,
            status=OrderStatus.ACCEPTED,
        )
        self.db.add(unavailable_order)
        self.db.commit()

        open_orders = CourierService.get_open_orders(self.db)
        open_order_ids = {order.id for order in open_orders}

        self.assertEqual(
            open_order_ids,
            {regular_order.id, product_order.id},
        )
        self.assertEqual(product_order.from_store_id, self.source_store.id)
        self.assertEqual(product_order.to_store_id, self.requester_store.id)
        self.assertEqual(product_order.status, OrderStatus.WAITING_FOR_COURIER)
        self.assertNotIn(unavailable_order.id, open_order_ids)

        regular_format = format_order(regular_order)
        product_format = format_order(product_order)
        for formatted_order in (regular_format, product_format):
            self.assertIn("<b>Звідки:</b>", formatted_order)
            self.assertIn("<b>Куди:</b>", formatted_order)
            self.assertNotIn("Замовлення товару", formatted_order)
        self.assertIn("iPhone 17 Pro Max 256GB — 1 шт.", product_format)
        normalized_regular = regular_format.replace(regular_order.number, "<number>").replace(
            regular_order.description,
            "<description>",
        )
        normalized_product = product_format.replace(product_order.number, "<number>").replace(
            product_order.description,
            "<description>",
        )
        regular_sections = [
            line.split(":", 1)[0]
            for line in normalized_regular.splitlines()
            if "</b>:" in line
        ]
        product_sections = [
            line.split(":", 1)[0]
            for line in normalized_product.splitlines()
            if "</b>:" in line
        ]
        self.assertEqual(regular_sections, product_sections)
        self.assertIn(self.source_store.name, product_format)
        self.assertIn(self.requester_store.name, product_format)


if __name__ == "__main__":
    unittest.main()
