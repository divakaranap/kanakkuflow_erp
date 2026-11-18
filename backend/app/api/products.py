from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.dependencies import get_current_user, require_admin_or_owner
from backend.app.models.user import User
from backend.app.models.product import Product, ProductCategory
from backend.app.schemas.product import ProductCreate, ProductOut, ProductUpdate

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=List[ProductOut])
def list_products(
    category: Optional[ProductCategory] = Query(None, description="Filter by product category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or SKU"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Retrieve list of products with search and filtering."""
    query = db.query(Product)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    if category:
        query = query.filter(Product.category == category)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            (Product.product_name.ilike(pattern))
            | (Product.sku.ilike(pattern))
            | (Product.hsn_code.ilike(pattern))
        )
    return query.order_by(Product.product_name.asc()).offset(skip).limit(limit).all()


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_owner),
):
    """Create a new product (Admin / Owner only)."""
    existing_sku = db.query(Product).filter(Product.sku == product_in.sku).first()
    if existing_sku:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with SKU '{product_in.sku}' already exists",
        )

    product = Product(**product_in.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{id}", response_model=ProductOut)
def get_product(
    id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get single product by UUID."""
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.patch("/{id}", response_model=ProductOut)
def update_product(
    id: str,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_owner),
):
    """Update product details (Admin / Owner only)."""
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    update_data = product_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(product, field, val)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{id}", response_model=ProductOut)
def delete_product(
    id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_owner),
):
    """Deactivate product (Admin / Owner only)."""
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    product.is_active = False
    db.commit()
    db.refresh(product)
    return product
