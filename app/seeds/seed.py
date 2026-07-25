from app.database.session import SessionLocal
from app.models.store import Store
from app.models.user import User, UserRole, UserStatus


def seed():

    db = SessionLocal()

    try:
        # ---------- Stores ----------

        if db.query(Store).count() == 0:

            stores = [
                Store(
                    name="Victoria Gardens",
                    address="Кульпарківська 226А",
                    city="Львів",
                    latitude=49.809,
                    longitude=23.973,
                ),
                Store(
                    name="Forum Lviv",
                    address="Під Дубом 7Б",
                    city="Львів",
                    latitude=49.850,
                    longitude=24.026,
                ),
                Store(
                    name="King Cross",
                    address="Стрийська 30",
                    city="Сокільники",
                    latitude=49.774,
                    longitude=24.015,
                ),
            ]

            db.add_all(stores)
            db.commit()

            print("✓ Stores created")

        first_store = db.query(Store).first()

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