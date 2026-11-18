import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.dependencies import get_current_user, require_admin_or_owner
from backend.app.models.user import User
from backend.app.models.customer import Customer, CustomerType
from backend.app.models.product import Product
from backend.app.models.price_list import PriceList, PriceListItem, PriceListCustomerType
from backend.app.schemas.price_list import (
    PriceListCreate,
    PriceListOut,
    PriceListUpdate,
    PriceListItemCreate,
    PriceListItemOut,
    EffectivePriceResponse,
)

router = APIRouter(prefix="/price-lists", tags=["Price Lists"])


@router.get("", response_model=List[PriceListOut])
def list_price_lists(
    customer_type: Optional[PriceListCustomerType] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Retrieve list of price lists."""
    query = db.query(PriceList)
    if is_active is not None:
        query = query.filter(PriceList.is_active == is_active)
    if customer_type:
        query = query.filter(PriceList.customer_type == customer_type)
    return query.order_by(PriceList.name.asc()).offset(skip).limit(limit).all()


@router.post("", response_model=PriceListOut, status_code=status.HTTP_201_CREATED)
def create_price_list(
    price_list_in: PriceListCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_owner),
):
    """Create a new price list (Admin / Owner only)."""
    existing = db.query(PriceList).filter(PriceList.name == price_list_in.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Price list with name '{price_list_in.name}' already exists",
        )

    price_list = PriceList(
        name=price_list_in.name,
        description=price_list_in.description,
        customer_type=price_list_in.customer_type,
        is_active=price_list_in.is_active,
    )
    db.add(price_list)
    db.flush()

    if price_list_in.items:
        for item_data in price_list_in.items:
            product = db.query(Product).filter(Product.id == item_data.product_id).first()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with id '{item_data.product_id}' not found",
                )
            item = PriceListItem(
                price_list_id=price_list.id,
                product_id=item_data.product_id,
                selling_price_paise=item_data.selling_price_paise,
                valid_from=item_data.valid_from,
                valid_until=item_data.valid_until,
            )
            db.add(item)

    db.commit()
    db.refresh(price_list)
    return price_list


@router.get("/effective-price", response_model=EffectivePriceResponse)
def get_effective_price(
    customer_id: str = Query(..., description="Target customer UUID"),
    product_id: str = Query(..., description="Target product UUID"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Resolve effective selling price for a customer and product."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    now = datetime.datetime.now(datetime.timezone.utc)

    # 1. Customer-specific price list
    if customer.price_list_id:
        item = (
            db.query(PriceListItem)
            .join(PriceList)
            .filter(
                PriceListItem.price_list_id == customer.price_list_id,
                PriceListItem.product_id == product.id,
                PriceList.is_active == True,
            )
            .first()
        )
        if item:
            # Check date validity
            if (item.valid_from is None or item.valid_from <= now) and (
                item.valid_until is None or item.valid_until >= now
            ):
                return EffectivePriceResponse(
                    product_id=product.id,
                    sku=product.sku,
                    product_name=product.product_name,
                    selling_price_paise=item.selling_price_paise,
                    source="CUSTOMER_PRICE_LIST",
                    price_list_id=item.price_list_id,
                    price_list_name=item.price_list.name,
                )

    # 2. Customer type price list (RETAILER or DISTRIBUTOR)
    type_price_list = (
        db.query(PriceList)
        .filter(
            PriceList.customer_type == customer.customer_type,
            PriceList.is_active == True,
        )
        .first()
    )
    if type_price_list:
        item = (
            db.query(PriceListItem)
            .filter(
                PriceListItem.price_list_id == type_price_list.id,
                PriceListItem.product_id == product.id,
            )
            .first()
        )
        if item:
            if (item.valid_from is None or item.valid_from <= now) and (
                item.valid_until is None or item.valid_until >= now
            ):
                return EffectivePriceResponse(
                    product_id=product.id,
                    sku=product.sku,
                    product_name=product.product_name,
                    selling_price_paise=item.selling_price_paise,
                    source="CUSTOMER_TYPE_PRICE_LIST",
                    price_list_id=type_price_list.id,
                    price_list_name=type_price_list.name,
                )

    # 3. Product default fallback
    return EffectivePriceResponse(
        product_id=product.id,
        sku=product.sku,
        product_name=product.product_name,
        selling_price_paise=product.selling_price_paise,
        source="PRODUCT_DEFAULT",
        price_list_id=None,
        price_list_name=None,
    )


@router.get("/{id}", response_model=PriceListOut)
def get_price_list(
    id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get price list details with items."""
    price_list = db.query(PriceList).filter(PriceList.id == id).first()
    if not price_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price list not found")
    
    # Enrich product names
    for item in price_list.items:
        if item.product:
            item.product_sku = item.product.sku
            item.product_name = item.product.product_name

    return price_list


@router.patch("/{id}", response_model=PriceListOut)
def update_price_list(
    id: str,
    price_list_in: PriceListUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_owner),
):
    """Update price list metadata (Admin / Owner only)."""
    price_list = db.query(PriceList).filter(PriceList.id == id).first()
    if not price_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price list not found")

    update_data = price_list_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(price_list, field, val)

    db.commit()
    db.refresh(price_list)
    return price_list


@router.post("/{id}/items", response_model=PriceListItemOut, status_code=status.HTTP_201_CREATED)
def add_or_update_price_list_item(
    id: str,
    item_in: PriceListItemCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_owner),
):
    """Add or update a product item in the price list (Admin / Owner only)."""
    price_list = db.query(PriceList).filter(PriceList.id == id).first()
    if not price_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price list not found")

    product = db.query(Product).filter(Product.id == item_in.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    existing_item = (
        db.query(PriceListItem)
        .filter(PriceListItem.price_list_id == id, PriceListItem.product_id == item_in.product_id)
        .first()
    )

    if existing_item:
        existing_item.selling_price_paise = item_in.selling_price_paise
        existing_item.valid_from = item_in.valid_from
        existing_item.valid_until = item_in.valid_until
        db.commit()
        db.refresh(existing_item)
        existing_item.product_sku = product.sku
        existing_item.product_name = product.product_name
        return existing_item
    else:
        new_item = PriceListItem(
            price_list_id=id,
            product_id=item_in.product_id,
            selling_price_paise=item_in.selling_price_paise,
            valid_from=item_in.valid_from,
            valid_until=item_in.valid_until,
        )
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        new_item.product_sku = product.sku
        new_item.product_name = product.product_name
        return new_item
