from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.store import StoreCreate, StoreResponse
from app.services.store_service import StoreService

router = APIRouter(
    prefix="/stores",
    tags=["Stores"],
)


@router.post("/", response_model=StoreResponse)
def create_store(
    store: StoreCreate,
    db: Session = Depends(get_db),
):
    return StoreService.create_store(
        db=db,
        store=store,
    )


@router.get("/", response_model=list[StoreResponse])
def get_stores(
    db: Session = Depends(get_db),
):
    return StoreService.get_stores(db=db)