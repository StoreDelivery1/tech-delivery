from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import admin_required
from app.dependencies import get_db
from app.models.user import User
from app.schemas.store import StoreCreate, StoreResponse
from app.services.store_service import StoreService

router = APIRouter(
    prefix="/stores",
    tags=["Stores"],
)


@router.get(
    "/",
    response_model=list[StoreResponse],
)
def get_stores(
    db: Session = Depends(get_db),
):
    return StoreService.get_stores(db)


@router.get(
    "/{store_id}",
    response_model=StoreResponse,
)
def get_store(
    store_id: int,
    db: Session = Depends(get_db),
):
    try:
        return StoreService.get_store(
            db,
            store_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )


@router.post(
    "/",
    response_model=StoreResponse,
)
def create_store(
    store: StoreCreate,
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db),
):
    return StoreService.create_store(
        db,
        store,
    )


@router.patch(
    "/{store_id}",
    response_model=StoreResponse,
)
def update_store(
    store_id: int,
    store: StoreCreate,
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db),
):
    try:
        return StoreService.update_store(
            db,
            store_id,
            store,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )


@router.delete(
    "/{store_id}",
)
def delete_store(
    store_id: int,
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db),
):
    try:
        StoreService.delete_store(
            db,
            store_id,
        )

        return {
            "message": "Store deleted successfully",
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )