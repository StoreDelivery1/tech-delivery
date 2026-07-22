from sqlalchemy.orm import Session

from app.models.store import Store
from app.schemas.store import StoreCreate


class StoreService:

    @staticmethod
    def create_store(
        db: Session,
        store: StoreCreate,
    ) -> Store:
        new_store = Store(**store.model_dump())

        db.add(new_store)
        db.commit()
        db.refresh(new_store)

        return new_store

    @staticmethod
    def get_stores(
        db: Session,
    ) -> list[Store]:
        return db.query(Store).all()