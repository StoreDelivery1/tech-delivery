from app.database.session import SessionLocal
from app.models.store import Store, StoreNetwork
from app.models.user import User, UserRole, UserStatus


def seed():

    db = SessionLocal()

    try:
        # ---------- Stores ----------

        existing_store_ids = [store.id for store in db.query(Store).all()]
        if existing_store_ids:
            db.query(User).filter(User.store_id.in_(existing_store_ids)).update(
                {User.store_id: None},
                synchronize_session=False,
            )
            db.query(Store).delete(synchronize_session=False)

        stores = [
            Store(
                name="ТРЦ Victoria Gardens (Паркінг)",
                address="Гавришкевича 5",
                city="Львів",
                latitude=49.809,
                longitude=23.973,
                network=StoreNetwork.APPLE_ROOM,
                is_active=True,
            ),
            Store(
                name="Гавришкевича 5",
                address="Гавришкевича 5",
                city="Львів",
                latitude=49.814,
                longitude=24.006,
                network=StoreNetwork.APPLE_ROOM,
                is_active=True,
            ),
            Store(
                name="Галицька 1",
                address="Галицька 1",
                city="Львів",
                latitude=49.839,
                longitude=24.029,
                network=StoreNetwork.APPLE_ROOM,
                is_active=True,
            ),
            Store(
                name="Городоцька 3",
                address="Городоцька 3",
                city="Львів",
                latitude=49.819,
                longitude=24.02,
                network=StoreNetwork.APPLE_ROOM,
                is_active=True,
            ),
            Store(
                name="Пр. Свободи 35",
                address="Пр. Свободи 35",
                city="Львів",
                latitude=49.835,
                longitude=24.011,
                network=StoreNetwork.APPLE_ROOM,
                is_active=True,
            ),
            Store(
                name="Пр. Шевченка 3",
                address="Пр. Шевченка 3",
                city="Львів",
                latitude=49.841,
                longitude=24.009,
                network=StoreNetwork.APPLE_ROOM,
                is_active=True,
            ),
            Store(
                name="Пр. Свободи 9",
                address="Пр. Свободи 9",
                city="Львів",
                latitude=49.839,
                longitude=24.014,
                network=StoreNetwork.APPLE_ROOM,
                is_active=True,
            ),
            Store(
                name="Сервісний Центр",
                address="Сервісний Центр",
                city="Львів",
                latitude=49.82,
                longitude=24.0,
                network=StoreNetwork.APPLE_ROOM,
                is_active=True,
            ),
            Store(
                name="ТРЦ King Cross",
                address="Стрийська 30",
                city="Львів",
                latitude=49.774,
                longitude=24.015,
                network=StoreNetwork.APPLE_ROOM,
                is_active=True,
            ),
            Store(
                name="ТРЦ Victoria Gardens",
                address="Кульпарківська 226А",
                city="Львів",
                latitude=49.809,
                longitude=23.973,
                network=StoreNetwork.APPLE_ROOM,
                is_active=True,
            ),
            Store(
                name="ТРЦ Спартак",
                address="ТРЦ Спартак",
                city="Львів",
                latitude=49.815,
                longitude=24.0,
                network=StoreNetwork.APPLE_ROOM,
                is_active=True,
            ),
            Store(
                name="ТЦ Форум",
                address="Під Дубом 7Б",
                city="Львів",
                latitude=49.850,
                longitude=24.026,
                network=StoreNetwork.APPLE_ROOM,
                is_active=True,
            ),
            Store(
                name="Victoria Gardens",
                address="Кульпарківська 226А",
                city="Львів",
                latitude=49.809,
                longitude=23.973,
                network=StoreNetwork.JABKO,
                is_active=True,
            ),
            Store(
                name="Victoria Gardens 2",
                address="Кульпарківська 226А",
                city="Львів",
                latitude=49.809,
                longitude=23.974,
                network=StoreNetwork.JABKO,
                is_active=True,
            ),
            Store(
                name="ГОРОДОЦЬКА",
                address="ГОРОДОЦЬКА",
                city="Львів",
                latitude=49.82,
                longitude=24.021,
                network=StoreNetwork.JABKO,
                is_active=True,
            ),
            Store(
                name="Дорошенка",
                address="Дорошенка",
                city="Львів",
                latitude=49.827,
                longitude=24.016,
                network=StoreNetwork.JABKO,
                is_active=True,
            ),
            Store(
                name="Пр. Шевченка",
                address="Пр. Шевченка",
                city="Львів",
                latitude=49.841,
                longitude=24.009,
                network=StoreNetwork.JABKO,
                is_active=True,
            ),
            Store(
                name="Привокзальна",
                address="Привокзальна",
                city="Львів",
                latitude=49.833,
                longitude=24.0,
                network=StoreNetwork.JABKO,
                is_active=True,
            ),
            Store(
                name="Проспект",
                address="Проспект",
                city="Львів",
                latitude=49.837,
                longitude=24.008,
                network=StoreNetwork.JABKO,
                is_active=True,
            ),
            Store(
                name="Сервісний Центр",
                address="Сервісний Центр",
                city="Львів",
                latitude=49.82,
                longitude=24.0,
                network=StoreNetwork.JABKO,
                is_active=True,
            ),
            Store(
                name="Спартак",
                address="Спартак",
                city="Львів",
                latitude=49.815,
                longitude=24.0,
                network=StoreNetwork.JABKO,
                is_active=True,
            ),
            Store(
                name="Театральна",
                address="Театральна",
                city="Львів",
                latitude=49.84,
                longitude=24.012,
                network=StoreNetwork.JABKO,
                is_active=True,
            ),
            Store(
                name="ТРЦ NewPoint",
                address="ТРЦ NewPoint",
                city="Львів",
                latitude=49.829,
                longitude=24.005,
                network=StoreNetwork.JABKO,
                is_active=True,
            ),
            Store(
                name="ТЦ Great",
                address="ТЦ Great",
                city="Львів",
                latitude=49.828,
                longitude=24.007,
                network=StoreNetwork.JABKO,
                is_active=True,
            ),
            Store(
                name="Форум",
                address="Форум",
                city="Львів",
                latitude=49.849,
                longitude=24.026,
                network=StoreNetwork.JABKO,
                is_active=True,
            ),
            Store(
                name="Франка",
                address="Франка",
                city="Львів",
                latitude=49.839,
                longitude=24.01,
                network=StoreNetwork.JABKO,
                is_active=True,
            ),
            Store(
                name="ШЕВСЬКА",
                address="ШЕВСЬКА",
                city="Львів",
                latitude=49.842,
                longitude=24.008,
                network=StoreNetwork.JABKO,
                is_active=True,
            ),
            Store(
                name="King Cross",
                address="Стрийська 30",
                city="Львів",
                latitude=49.774,
                longitude=24.015,
                network=StoreNetwork.JABKO,
                is_active=True,
            ),
        ]

        db.add_all(stores)
        db.commit()

        first_store = db.query(Store).order_by(Store.id).first()

        print("✓ Stores created")

        # ---------- Admin ----------

        if (
            db.query(User)
            .filter(User.role == UserRole.ADMIN)
            .first()
            is None
        ):

            admin = User(
                telegram_id=111111111,
                username="admin",
                full_name="System Admin",
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
            )

            db.add(admin)
            db.commit()

            print("✓ Admin created")

        # ---------- Manager ----------

        if (
            db.query(User)
            .filter(User.role == UserRole.MANAGER)
            .first()
            is None
        ):

            manager = User(
                telegram_id=222222222,
                username="manager",
                full_name="Main Manager",
                role=UserRole.MANAGER,
                status=UserStatus.ACTIVE,
                store_id=first_store.id,
            )

            db.add(manager)
            db.commit()

            print("✓ Manager created")

        # ---------- Courier ----------

        if (
            db.query(User)
            .filter(User.role == UserRole.COURIER)
            .first()
            is None
        ):

            courier = User(
                telegram_id=333333333,
                username="courier",
                full_name="Main Courier",
                role=UserRole.COURIER,
                status=UserStatus.ACTIVE,
                store_id=first_store.id,
            )

            db.add(courier)
            db.commit()

            print("✓ Courier created")

        print("\nSeed completed successfully!")

    finally:
        db.close()


if __name__ == "__main__":
    seed()