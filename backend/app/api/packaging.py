from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.dependencies import get_current_user, require_production
from backend.app.models.user import User
from backend.app.models.packaging import PackagingItem, PackagingCategory
from backend.app.schemas.packaging import PackagingCreate, PackagingOut, PackagingUpdate

router = APIRouter(prefix="/packaging", tags=["Packaging"])


@router.get("", response_model=List[PackagingOut])
def list_packaging(
    category: Optional[PackagingCategory] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or code"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List packaging items."""
    query = db.query(PackagingItem)
    if is_active is not None:
        query = query.filter(PackagingItem.is_active == is_active)
    if category:
        query = query.filter(PackagingItem.category == category)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            (PackagingItem.packaging_name.ilike(pattern))
            | (PackagingItem.packaging_code.ilike(pattern))
        )
    return query.order_by(PackagingItem.packaging_name.asc()).offset(skip).limit(limit).all()


@router.post("", response_model=PackagingOut, status_code=status.HTTP_201_CREATED)
def create_packaging(
    packaging_in: PackagingCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_production),
):
    """Create a new packaging item (Production / Admin / Owner only)."""
    existing_code = db.query(PackagingItem).filter(PackagingItem.packaging_code == packaging_in.packaging_code).first()
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Packaging code '{packaging_in.packaging_code}' already exists",
        )

    item = PackagingItem(**packaging_in.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{id}", response_model=PackagingOut)
def get_packaging(
    id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get single packaging item by UUID."""
    item = db.query(PackagingItem).filter(PackagingItem.id == id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Packaging item not found")
    return item


@router.patch("/{id}", response_model=PackagingOut)
def update_packaging(
    id: str,
    packaging_in: PackagingUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_production),
):
    """Update packaging details (Production / Admin / Owner only)."""
    item = db.query(PackagingItem).filter(PackagingItem.id == id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Packaging item not found")

    update_data = packaging_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(item, field, val)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{id}", response_model=PackagingOut)
def delete_packaging(
    id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_production),
):
    """Deactivate packaging item (Production / Admin / Owner only)."""
    item = db.query(PackagingItem).filter(PackagingItem.id == id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Packaging item not found")

    item.is_active = False
    db.commit()
    db.refresh(item)
    return item
