from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.dependencies import get_current_user, require_admin_or_owner
from backend.app.models.user import User
from backend.app.models.supplier import Supplier
from backend.app.schemas.supplier import SupplierCreate, SupplierOut, SupplierUpdate

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get("", response_model=List[SupplierOut])
def list_suppliers(
    search: Optional[str] = Query(None, description="Search by name, code or GSTIN"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Retrieve list of suppliers."""
    query = db.query(Supplier)
    if is_active is not None:
        query = query.filter(Supplier.is_active == is_active)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            (Supplier.supplier_name.ilike(pattern))
            | (Supplier.supplier_code.ilike(pattern))
            | (Supplier.gstin.ilike(pattern))
            | (Supplier.city.ilike(pattern))
        )
    return query.order_by(Supplier.supplier_name.asc()).offset(skip).limit(limit).all()


@router.post("", response_model=SupplierOut, status_code=status.HTTP_201_CREATED)
def create_supplier(
    supplier_in: SupplierCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_owner),
):
    """Create a new supplier (Admin / Owner only)."""
    existing_code = db.query(Supplier).filter(Supplier.supplier_code == supplier_in.supplier_code).first()
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Supplier code '{supplier_in.supplier_code}' already exists",
        )

    supplier = Supplier(**supplier_in.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/{id}", response_model=SupplierOut)
def get_supplier(
    id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get single supplier by UUID."""
    supplier = db.query(Supplier).filter(Supplier.id == id).first()
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return supplier


@router.patch("/{id}", response_model=SupplierOut)
def update_supplier(
    id: str,
    supplier_in: SupplierUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_owner),
):
    """Update supplier details (Admin / Owner only)."""
    supplier = db.query(Supplier).filter(Supplier.id == id).first()
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    update_data = supplier_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(supplier, field, val)

    db.commit()
    db.refresh(supplier)
    return supplier


@router.delete("/{id}", response_model=SupplierOut)
def delete_supplier(
    id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_owner),
):
    """Deactivate supplier (Admin / Owner only)."""
    supplier = db.query(Supplier).filter(Supplier.id == id).first()
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    supplier.is_active = False
    db.commit()
    db.refresh(supplier)
    return supplier
