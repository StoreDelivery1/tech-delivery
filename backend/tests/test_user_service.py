import unittest

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService


class UserServiceValidationTests(unittest.TestCase):
    def test_create_manager_requires_store_id(self):
        with self.assertRaises(ValueError):
            UserService.create(
                db=None,
                user=UserCreate(
                    full_name="Manager",
                    role=UserRole.MANAGER,
                    store_id=None,
                ),
            )

    def test_create_admin_store_id_is_forced_to_none(self):
        normalized = UserService._normalize_user_data(
            UserCreate(
                full_name="Admin",
                role=UserRole.ADMIN,
                store_id=7,
            )
        )

        self.assertIsNone(normalized["store_id"])

    def test_create_courier_store_id_is_forced_to_none(self):
        normalized = UserService._normalize_user_data(
            UserCreate(
                full_name="Courier",
                role=UserRole.COURIER,
                store_id=8,
            )
        )

        self.assertIsNone(normalized["store_id"])

    def test_update_manager_requires_store_id(self):
        user = User(role=UserRole.MANAGER, full_name="Manager")

        with self.assertRaises(ValueError):
            UserService._normalize_user_instance(
                user=user,
                data=UserUpdate(full_name="Updated").model_dump(exclude_unset=True),
            )

    def test_update_admin_store_id_is_forced_to_none(self):
        user = User(role=UserRole.ADMIN, full_name="Admin", store_id=9)

        UserService._normalize_user_instance(
            user=user,
            data=UserUpdate(role=UserRole.ADMIN).model_dump(exclude_unset=True),
        )

        self.assertIsNone(user.store_id)


if __name__ == "__main__":
    unittest.main()
