import unittest

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.permissions import admin_required, manager_required
from app.models.store import Store, StoreNetwork
from app.models.user import User, UserRole, UserStatus
from app.routers.managers import get_my_orders, get_my_profile


class TestManagerRoleAccess(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        from app.database.base import Base
        from app.models.order import Order

        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
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
            self.store_id = store.id
            self.manager = User(
                full_name="Manager",
                role=UserRole.MANAGER,
                status=UserStatus.ACTIVE,
                store_id=store.id,
            )
            self.seller = User(
                full_name="Seller",
                role=UserRole.SELLER,
                status=UserStatus.ACTIVE,
                store_id=store.id,
            )
            self.unassigned_seller = User(
                full_name="Unassigned Seller",
                role=UserRole.SELLER,
                status=UserStatus.ACTIVE,
            )
            self.courier = User(
                full_name="Courier",
                role=UserRole.COURIER,
                status=UserStatus.ACTIVE,
            )
            db.add_all([self.manager, self.seller, self.unassigned_seller, self.courier])
            db.commit()
            for user in (self.manager, self.seller, self.unassigned_seller, self.courier):
                db.refresh(user)

    def tearDown(self):
        self.engine.dispose()

    def test_seller_can_use_manager_profile_and_orders_api(self):
        with Session(self.engine) as db:
            profile = get_my_profile(current_user=self.seller, db=db)
            orders = get_my_orders(current_user=self.seller, db=db)

        self.assertEqual(profile.role, UserRole.SELLER)
        self.assertEqual(orders, [])

    def test_manager_can_use_manager_api(self):
        with Session(self.engine) as db:
            profile = get_my_profile(current_user=self.manager, db=db)

        self.assertEqual(profile.role, UserRole.MANAGER)

    def test_seller_without_store_is_denied_manager_api(self):
        with self.assertRaises(HTTPException) as context:
            manager_required(current_user=self.unassigned_seller)
        self.assertEqual(context.exception.status_code, 403)
        self.assertEqual(context.exception.detail, "Manager must be assigned to a store")

    def test_courier_is_not_allowed_manager_api(self):
        with self.assertRaises(HTTPException) as context:
            manager_required(current_user=self.courier)
        self.assertEqual(context.exception.status_code, 403)

    def test_seller_is_not_allowed_admin_api_or_dependency(self):
        self.assertIs(manager_required(current_user=self.seller), self.seller)
        with self.assertRaises(HTTPException) as context:
            admin_required(current_user=self.seller)
        self.assertEqual(context.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
