from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.store import Store, StoreNetwork
from app.schemas.store import StoreCreate


class StoreService:

    @staticmethod
    def get_stores(
        db: Session,
    ) -> list[Store]:

        return (
            db.query(Store)
            .order_by(Store.id)
            .all()
        )

    @staticmethod
    def get_store(
        db: Session,
        store_id: int,
    ) -> Store:

        store = db.get(Store, store_id)

        if store is None:
            raise ValueError("Store not found")

        return store

    @staticmethod
    def get_stores_by_network(
        db: Session,
        network: StoreNetwork | str,
    ) -> list[Store]:

        if isinstance(network, str):
            network = StoreNetwork(network)

        return (
            db.query(Store)
            .filter(Store.network == network)
            .order_by(Store.id)
            .all()
        )

    @staticmethod
    def search_stores(
        db: Session,
        query: str,
        network: StoreNetwork | str,
    ) -> list[Store]:

        if isinstance(network, str):
            network = StoreNetwork(network)

        normalized_query = (query or "").strip().lower()

        if not normalized_query:
            return StoreService.get_stores_by_network(db, network)

        like_query = f"%{normalized_query}%"

        return (
            db.query(Store)
            .filter(Store.network == network)
            .filter(
                or_(
                    Store.name.ilike(like_query),
                    Store.address.ilike(like_query),
                    Store.city.ilike(like_query),
                )
            )
            .order_by(Store.id)
            .all()
        )

    @staticmethod
    def create_store(
        db: Session,
        store: StoreCreate,
    ) -> Store:

        new_store = Store(
            **store.model_dump(),
        )

        db.add(new_store)
        db.commit()
        db.refresh(new_store)

        return new_store

    @staticmethod
    def update_store(
        db: Session,
        store_id: int,
        data: StoreCreate,
    ) -> Store:

        store = StoreService.get_store(
            db,
            store_id,
        )

        for key, value in data.model_dump().items():
            setattr(store, key, value)

        db.commit()
        db.refresh(store)

        return store

    @staticmethod
    def delete_store(
        db: Session,
        store_id: int,
    ) -> None:

        store = StoreService.get_store(
            db,
            store_id,
        )

        db.delete(store)
        db.commit()