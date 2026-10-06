import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.order import Order
from app.models.store import Store, StoreNetwork
from app.models.user import User, UserRole, UserStatus
from app.bot.utils.store_formatter import display_store_name
from app.core.store_location_mapping import (
    NON_STORE_COURIER_DEPARTMENTS,
    SHEET_LOCATION_DISPLAY_NAMES,
    SHEET_LOCATION_STORE_NAMES,
    STORE_NAME_DISPLAY_NAMES,
    UNRESOLVED_SHEET_LOCATIONS,
)
from app.services.staff_sync_service import parse_staff_rows, role_for_position, sync_staff_rows


HEADERS = [
    "ПІБ",
    "Telegram username",
    "Магазин",
    "Посада",
    "Звільнений Так/Ні",
    "Telegram ID",
    "Графік",
]


class TestStaffSyncService(unittest.TestCase):
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
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    @staticmethod
    def sheet_row(
        full_name="Test Person",
        username="",
        store="Test Store",
        position="Продавець",
        dismissed="Ні",
        telegram_id="123456",
        schedule="Р ВХ",
    ):
        return [full_name, username, store, position, dismissed, telegram_id, schedule]

    def test_positions_map_only_courier_titles_to_courier(self):
        self.assertEqual(role_for_position("Кур'єр"), UserRole.COURIER)
        self.assertEqual(role_for_position("Водій - кур'єр"), UserRole.COURIER)
        self.assertEqual(role_for_position("Менеджер"), UserRole.SELLER)

    def test_multiline_dismissal_header_is_recognized(self):
        headers = HEADERS.copy()
        headers[4] = "  Звільнений\r\n Так\\Ні  "

        rows, rows_found = parse_staff_rows(
            [headers, self.sheet_row(dismissed="Ні")]
        )

        self.assertEqual(rows_found, 1)
        self.assertFalse(rows[0].dismissed)
        self.assertEqual(rows[0].errors, ())

    def test_workday_z_uses_same_store_alias_as_r(self):
        results = {}

        with patch(
            "app.services.staff_sync_service.SHEET_LOCATION_STORE_NAMES",
            {"Test Store": "Test Store"},
        ):
            for index, schedule in enumerate(("Р", "З"), start=1):
                report = sync_staff_rows(
                    self.db,
                    [
                        HEADERS,
                        self.sheet_row(
                            full_name=f"Employee {index}",
                            store="Test Store",
                            telegram_id=str(100000 + index),
                            schedule=schedule,
                        ),
                    ],
                    dry_run=False,
                )
                user = self.db.query(User).filter(User.telegram_id == 100000 + index).one()
                results[schedule] = user.store_id
                self.assertEqual(report.created, 1)
                self.assertEqual(report.skipped, 0)
                self.assertEqual(report.schedules_validated, 1)

        self.assertEqual(results["Р"], self.store.id)
        self.assertEqual(results["З"], results["Р"])

    def test_display_mapping_does_not_change_original_store_name(self):
        store = Store(name="ЛГО")

        self.assertEqual(display_store_name(store), "ЛГО")
        self.assertEqual(store.name, "ЛГО")

    def test_client_repairs_alias_uses_store_name_and_display_name(self):
        sheet_location = "Відділ сервісу ( клієнтські ремонти)"
        store = Store(name="Сервісний Центр")

        self.assertEqual(SHEET_LOCATION_STORE_NAMES[sheet_location], "Сервісний Центр")
        self.assertEqual(SHEET_LOCATION_DISPLAY_NAMES[sheet_location], "Сервіс Данилишина")
        self.assertEqual(STORE_NAME_DISPLAY_NAMES["Сервісний Центр"], "Сервіс Данилишина")
        self.assertEqual(display_store_name(store), "Сервіс Данилишина")
        self.assertEqual(store.name, "Сервісний Центр")

    def test_confirmed_aliases_and_location_statuses_are_configured(self):
        self.assertTrue(SHEET_LOCATION_STORE_NAMES)
        self.assertTrue(all(isinstance(name, str) for name in SHEET_LOCATION_STORE_NAMES.values()))
        previous_sheet_aliases = {
            "Appleroom Львів (Городоцька 3)",
            "Appleroom Львів (Пр. Шевченка 3)",
            "Appleroom Львів (Пр.Свободи 9)",
            "Appleroom Львів (ТРЦ King Cross)",
            "Appleroom Львів (ТРЦ Victoria Gardens [Паркінг])",
            "Appleroom Львів (ТРЦ Victoria Gardens)",
            "Appleroom Львів (ТЦ Форум)",
            "Ябко Львів (Victoria Gardens 2)",
            "Ябко Львів (Victoria Gardens)",
            "Ябко Львів (ГОРОДОЦЬКА)",
            "Ябко Львів (Привокзальна)",
            "Ябко Львів (Проспект)",
            "Ябко Львів (Спартак)",
            "Ябко Львів (ТРЦ NewPoint)",
            "Ябко Львів (ТЦ Great)",
            "Ябко Львів (Форум)",
            "Ябко Львів (ШЕВСЬКА)",
            "Ябко Львів King Cross",
            "Відділ сервісу ( клієнтські ремонти)",
            "Львівський ГО",
        }
        self.assertTrue(previous_sheet_aliases.issubset(SHEET_LOCATION_STORE_NAMES))
        self.assertEqual(SHEET_LOCATION_STORE_NAMES["Відділ сервісу"], "Сервісний Центр")
        self.assertEqual(SHEET_LOCATION_STORE_NAMES["Гавришкевича"], "Гавришкевича 5")
        self.assertEqual(
            SHEET_LOCATION_STORE_NAMES["Appleroom Львів (ТРЦ Victoria Gardens)"],
            "ТРЦ Victoria Gardens (Паркінг)",
        )
        self.assertEqual(UNRESOLVED_SHEET_LOCATIONS, {})
        self.assertEqual(
            NON_STORE_COURIER_DEPARTMENTS,
            {"Відділ транспортної логістики"},
        )
        self.assertEqual(SHEET_LOCATION_DISPLAY_NAMES["Львівський ГО"], "ЛГО")

    def test_alias_resolves_existing_store_id_in_dry_run(self):
        user = User(
            telegram_id=123456,
            full_name="Existing User",
            role=UserRole.SELLER,
            status=UserStatus.ACTIVE,
        )
        self.db.add(user)
        self.db.commit()

        with patch(
            "app.services.staff_sync_service.SHEET_LOCATION_STORE_NAMES",
            {"Sheet alias": self.store.name},
        ):
            report = sync_staff_rows(
                self.db,
                [HEADERS, self.sheet_row(store="Sheet alias")],
                dry_run=True,
            )

        self.assertEqual(report.alias_rows_available, 1)
        self.assertEqual(report.alias_rows_processed, 1)
        self.assertEqual(report.updated, 1)
        self.assertEqual(report.location_issues, [])
        self.assertIsNone(user.store_id)

    def test_targeted_username_with_store_override_only_updates_one_user(self):
        target = User(
            telegram_id=123456,
            username="Turkovetss",
            full_name="Existing Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
        )
        self.db.add(target)
        self.db.commit()

        report = sync_staff_rows(
            self.db,
            [
                HEADERS,
                self.sheet_row(
                    username="Turkovetss",
                    store="Unmapped department",
                ),
                self.sheet_row(
                    full_name="Other Employee",
                    username="other_user",
                    telegram_id="654321",
                ),
            ],
            dry_run=True,
            only_username="@turkovetss",
            store_id_override=self.store.id,
        )

        self.assertEqual(report.rows_found, 1)
        self.assertEqual(report.updated, 1)
        self.assertEqual(len(report.targeted_preview), 1)
        self.assertEqual(report.targeted_preview[0]["store_id"], self.store.id)
        self.assertEqual(report.targeted_preview[0]["role"], UserRole.ADMIN.value)
        self.assertTrue(report.targeted_preview[0]["preserve_admin_role"])
        self.assertEqual(target.full_name, "Existing Admin")
        self.assertIsNone(
            self.db.query(User).filter(User.telegram_id == 654321).first()
        )

    def test_targeted_username_rejects_ambiguous_sheet_rows(self):
        with self.assertRaisesRegex(ValueError, "found 2"):
            sync_staff_rows(
                self.db,
                [
                    HEADERS,
                    self.sheet_row(username="duplicate"),
                    self.sheet_row(telegram_id="654321", username="Duplicate"),
                ],
                only_username="duplicate",
            )

    def test_targeted_apply_creates_only_the_selected_username(self):
        report = sync_staff_rows(
            self.db,
            [
                HEADERS,
                self.sheet_row(
                    full_name="Selected Employee",
                    username="selected_user",
                    telegram_id="123456",
                    store="Unmapped department",
                ),
                self.sheet_row(
                    full_name="Other Employee",
                    username="other_user",
                    telegram_id="654321",
                ),
            ],
            dry_run=False,
            only_username="selected_user",
            store_id_override=self.store.id,
        )

        self.assertEqual(report.rows_found, 1)
        self.assertEqual(report.created, 1)
        self.assertEqual(self.db.query(User).count(), 1)
        selected = self.db.query(User).one()
        self.assertEqual(selected.username, "selected_user")
        self.assertEqual(selected.store_id, self.store.id)
        self.assertIsNone(
            self.db.query(User).filter(User.telegram_id == 654321).first()
        )

    def test_service_alias_uses_id_from_matching_database_store(self):
        service_store = Store(
            name="Сервісний Центр",
            address="Сервісний Центр",
            city="Львів",
            latitude=49.82,
            longitude=24.0,
            network=StoreNetwork.JABKO,
        )
        user = User(
            telegram_id=123456,
            username="service_employee",
            full_name="Service Employee",
            role=UserRole.SELLER,
            status=UserStatus.ACTIVE,
        )
        self.db.add_all([service_store, user])
        self.db.commit()

        report = sync_staff_rows(
            self.db,
            [HEADERS, self.sheet_row(username="service_employee", store="Відділ сервісу")],
            dry_run=True,
            only_username="service_employee",
        )

        self.assertEqual(report.skipped, 0)
        self.assertEqual(report.alias_rows_available, 1)
        self.assertEqual(report.alias_rows_processed, 1)
        self.assertEqual(report.targeted_preview[0]["store_id"], service_store.id)
        self.assertIsNone(user.store_id)

    def test_missing_store_is_skipped_without_creation(self):
        report = sync_staff_rows(
            self.db,
            [HEADERS, self.sheet_row(store="Відділ аксесуарів")],
            dry_run=True,
        )

        self.assertEqual(report.skipped, 1)
        self.assertEqual(report.unresolved_locations, {"Відділ аксесуарів": 1})
        self.assertEqual(report.create_required_locations, {})
        self.assertEqual(self.db.query(Store).count(), 1)

    def test_transport_department_is_courier_without_store_assignment(self):
        existing = User(
            telegram_id=123456,
            full_name="Existing Courier",
            role=UserRole.SELLER,
            status=UserStatus.ACTIVE,
            store_id=self.store.id,
        )
        self.db.add(existing)
        self.db.commit()

        report = sync_staff_rows(
            self.db,
            [
                HEADERS,
                self.sheet_row(
                    store="Відділ транспортної логістики",
                    position="Продавець",
                    schedule="ВХ",
                ),
                self.sheet_row(
                    full_name="New Courier",
                    store="Відділ транспортної логістики",
                    position="Менеджер",
                    telegram_id="654321",
                ),
            ],
            dry_run=False,
        )

        self.assertEqual(report.non_store_department_rows, 2)
        self.assertEqual(report.updated, 1)
        self.assertEqual(report.created, 1)
        self.assertEqual(report.skipped, 0)
        self.assertEqual(existing.role, UserRole.COURIER)
        self.assertIsNone(existing.store_id)
        new_user = self.db.query(User).filter(User.telegram_id == 654321).one()
        self.assertEqual(new_user.role, UserRole.COURIER)
        self.assertIsNone(new_user.store_id)
        self.assertEqual(new_user.status, UserStatus.ACTIVE)
        self.assertEqual(self.db.query(Store).count(), 1)

    def test_dry_run_does_not_create_or_update_users(self):
        existing = User(
            telegram_id=123456,
            username="old_username",
            full_name="Old Name",
            role=UserRole.MANAGER,
            status=UserStatus.ACTIVE,
            store_id=None,
        )
        self.db.add(existing)
        self.db.commit()

        report = sync_staff_rows(
            self.db,
            [HEADERS, self.sheet_row(), self.sheet_row(telegram_id="")],
            dry_run=True,
        )

        self.assertEqual(report.rows_found, 2)
        self.assertEqual(report.updated, 1)
        self.assertEqual(report.skipped, 1)
        self.assertEqual(len(report.missing_telegram_ids), 1)
        self.assertEqual(existing.full_name, "Old Name")
        self.assertEqual(existing.role, UserRole.MANAGER)
        self.assertIsNone(existing.store_id)
        self.assertIsNone(
            self.db.query(User).filter(User.telegram_id == 654321).first()
        )

    def test_apply_creates_seller_and_preserves_empty_username(self):
        existing = User(
            telegram_id=123456,
            username="keep_this_username",
            full_name="Old Name",
            role=UserRole.MANAGER,
            status=UserStatus.ACTIVE,
        )
        self.db.add(existing)
        self.db.commit()

        report = sync_staff_rows(
            self.db,
            [
                HEADERS,
                self.sheet_row(full_name="Updated Name", dismissed="Так"),
                self.sheet_row(
                    full_name="New Courier",
                    position="Водій - кур'єр",
                    telegram_id="654321",
                ),
            ],
            dry_run=False,
        )

        self.assertEqual(report.updated, 1)
        self.assertEqual(report.created, 1)
        self.assertEqual(report.blocked, 1)
        self.assertEqual(existing.full_name, "Updated Name")
        self.assertEqual(existing.username, "keep_this_username")
        self.assertEqual(existing.role, UserRole.SELLER)
        self.assertEqual(existing.status, UserStatus.INACTIVE)
        self.assertEqual(existing.store_id, self.store.id)
        new_user = self.db.query(User).filter(User.telegram_id == 654321).one()
        self.assertEqual(new_user.role, UserRole.COURIER)
        self.assertIsNone(new_user.username)

    def test_admin_role_is_preserved_while_status_and_location_sync(self):
        admin = User(
            telegram_id=123456,
            full_name="Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
        )
        self.db.add(admin)
        self.db.commit()

        sync_staff_rows(
            self.db,
            [HEADERS, self.sheet_row(position="Продавець", dismissed="Так")],
            dry_run=False,
        )

        self.assertEqual(admin.role, UserRole.ADMIN)
        self.assertEqual(admin.status, UserStatus.INACTIVE)
        self.assertEqual(admin.store_id, self.store.id)

    def test_missing_or_ambiguous_location_skips_entire_row(self):
        second_store = Store(
            name="Test Store",
            address="Another address",
            city="Lviv",
            latitude=49.1,
            longitude=24.1,
            network=StoreNetwork.JABKO,
        )
        self.db.add(second_store)
        self.db.commit()

        report = sync_staff_rows(
            self.db,
            [HEADERS, self.sheet_row(store="Test Store")],
            dry_run=False,
        )

        self.assertEqual(report.skipped, 1)
        self.assertEqual(len(report.location_issues), 1)
        self.assertIsNone(
            self.db.query(User).filter(User.telegram_id == 123456).first()
        )

    def test_invalid_schedule_is_skipped_and_logged(self):
        report = sync_staff_rows(
            self.db,
            [HEADERS, self.sheet_row(schedule="Ротація")],
            dry_run=True,
        )

        self.assertEqual(report.skipped, 1)
        self.assertTrue(any("Schedule" in error for error in report.errors))

    def test_nonempty_malformed_telegram_id_is_an_error_not_a_missing_id(self):
        report = sync_staff_rows(
            self.db,
            [HEADERS, self.sheet_row(telegram_id="not-an-id")],
            dry_run=True,
        )

        self.assertEqual(report.skipped, 1)
        self.assertEqual(report.missing_telegram_ids, [])
        self.assertTrue(any("digits only" in error for error in report.errors))


if __name__ == "__main__":
    unittest.main()