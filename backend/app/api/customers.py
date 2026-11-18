from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.dependencies import get_current_user, require_admin_or_owner
from backend.app.models.user import User, UserRole
from backend.app.models.customer import Customer, CustomerType
from backend.app.schemas.customer import CustomerCreate, CustomerOut, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", response_model=List[CustomerOut])
def list_customers(
    search: Optional[str] = Query(None, description="Search by name, code or GSTIN"),
    customer_type: Optional[CustomerType] = Query(None, description="Filter by Retailer or Distributor"),
    state: Optional[str] = Query(None, description="Filter by state"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve list of customers with filtering, search, and pagination."""
    query = db.query(Customer)

    # Salesman territory filter: if user is SALESMAN and assigned_salesman is tracked
    if current_user.role == UserRole.SALESMAN:
        # Salesman sees their assigned customers or all active customers in territory
        query = query.filter((Customer.assigned_salesman_id == current_user.id) | (Customer.assigned_salesman_id.is_(None)))

    if is_active is not None:
        query = query.filter(Customer.is_active == is_active)
    if customer_type:
        query = query.filter(Customer.customer_type == customer_type)
    if state:
        query = query.filter(Customer.state.ilike(f"%{state}%"))
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            (Customer.customer_name.ilike(search_pattern))
            | (Customer.customer_code.ilike(search_pattern))
            | (Customer.gstin.ilike(search_pattern))
            | (Customer.city.ilike(search_pattern))
        )

    return query.order_by(Customer.customer_name.asc()).offset(skip).limit(limit).all()


@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_in: CustomerCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_owner),
):
    """Create a new customer (Admin / Owner only)."""
    # Check duplicate code
    existing_code = db.query(Customer).filter(Customer.customer_code == customer_in.customer_code).first()
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer code '{customer_in.customer_code}' already exists",
        )

    customer = Customer(**customer_in.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{id}", response_model=CustomerOut)
def get_customer(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get single customer by UUID."""
    customer = db.query(Customer).filter(Customer.id == id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


@router.patch("/{id}", response_model=CustomerOut)
def update_customer(
    id: str,
    customer_in: CustomerUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_owner),
):
    """Update customer details (Admin / Owner only)."""
    customer = db.query(Customer).filter(Customer.id == id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    update_data = customer_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(customer, field, val)

    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{id}", response_model=CustomerOut)
def delete_customer(
    id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_owner),
):
    """Soft-delete / deactivate customer to maintain financial and order auditability."""
    customer = db.query(Customer).filter(Customer.id == id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    customer.is_active = False
    db.commit()
    db.refresh(customer)
    return customer
