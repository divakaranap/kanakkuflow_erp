from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.dependencies import get_current_user, require_production
from backend.app.models.user import User
from backend.app.models.raw_material import RawMaterial, RawMaterialCategory
from backend.app.schemas.raw_material import RawMaterialCreate, RawMaterialOut, RawMaterialUpdate

router = APIRouter(prefix="/raw-materials", tags=["Raw Materials"])


@router.get("", response_model=List[RawMaterialOut])
def list_raw_materials(
    category: Optional[RawMaterialCategory] = Query(None, description="Filter by raw material category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or code"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List raw materials."""
    query = db.query(RawMaterial)
    if is_active is not None:
        query = query.filter(RawMaterial.is_active == is_active)
    if category:
        query = query.filter(RawMaterial.category == category)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            (RawMaterial.material_name.ilike(pattern))
            | (RawMaterial.material_code.ilike(pattern))
        )
    return query.order_by(RawMaterial.material_name.asc()).offset(skip).limit(limit).all()


@router.post("", response_model=RawMaterialOut, status_code=status.HTTP_201_CREATED)
def create_raw_material(
    material_in: RawMaterialCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_production),
):
    """Create a new raw material (Production / Admin / Owner only)."""
    existing_code = db.query(RawMaterial).filter(RawMaterial.material_code == material_in.material_code).first()
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Material code '{material_in.material_code}' already exists",
        )

    material = RawMaterial(**material_in.model_dump())
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


@router.get("/{id}", response_model=RawMaterialOut)
def get_raw_material(
    id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get single raw material by UUID."""
    material = db.query(RawMaterial).filter(RawMaterial.id == id).first()
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Raw material not found")
    return material


@router.patch("/{id}", response_model=RawMaterialOut)
def update_raw_material(
    id: str,
    material_in: RawMaterialUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_production),
):
    """Update raw material details (Production / Admin / Owner only)."""
    material = db.query(RawMaterial).filter(RawMaterial.id == id).first()
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Raw material not found")

    update_data = material_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(material, field, val)

    db.commit()
    db.refresh(material)
    return material


@router.delete("/{id}", response_model=RawMaterialOut)
def delete_raw_material(
    id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_production),
):
    """Deactivate raw material (Production / Admin / Owner only)."""
    material = db.query(RawMaterial).filter(RawMaterial.id == id).first()
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Raw material not found")

    material.is_active = False
    db.commit()
    db.refresh(material)
    return material
