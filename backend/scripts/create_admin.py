from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.user import User, UserRole, UserStatus


def create_admin():
    db: Session = SessionLocal()

    try:
        admin = (
            db.query(User)
            .filter(User.role == UserRole.ADMIN)
            .first()
        )

        if admin:
            print("✅ Admin already exists")
            return

        admin = User(
            telegram_id=111111111,
            username="admin",
            full_name="System Administrator",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            store_id=None,
            is_online=False,
        )

        db.add(admin)
        db.commit()

        print("✅ Admin created successfully")
        print("Telegram ID: 111111111")

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()