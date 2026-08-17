from app.database.base import Base
from app.database.session import engine

# Імпортуємо всі моделі
from app.models.user import User

Base.metadata.create_all(bind=engine)

print("✅ Всі таблиці створено!")
