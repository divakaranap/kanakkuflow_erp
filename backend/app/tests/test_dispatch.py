from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from backend.app.models.user import User, UserRole
from backend.app.models.customer import Customer, CustomerType
from backend.app.models.product import Product, ProductCategory
from backend.app.models.inventory import InventoryBalance, InventoryItemType, StockMovement, MovementType
from backend.app.models.sales import SalesOrder, SalesOrderItem, SalesOrderStatus


def get_auth_header(client, username, password="demo123"):
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_dispatch_benchmark_and_stock_deduction(client: TestClient, db, seeded_users):
    """
    Test Phase 6 Dispatch operations:
    1. Initial FG stock: 238 packets.
    2. Retailer A order: 150 packets -> Dispatch 150 -> Stock becomes 88 packets.
    3. Distributor B requests 120 packets -> Available is 88 -> Prevent overselling (shortage 32).
    4. Partial dispatch of 88 packets -> Stock becomes 0 -> Order is PARTIALLY_FULFILLED.
    5. Delivery Challan PDF generation.
    """
    admin_headers = get_auth_header(client, "admin")
    prod_headers = get_auth_header(client, "prod")

    # 1. Setup Product (Murukku 200g)
    prd = db.query(Product).filter(Product.sku == "MUR-200-DSP").first()
    if not prd:
        prd = Product(
            sku="MUR-200-DSP",
            product_name="Murukku 200g (Dispatch Test)",
            category=ProductCategory.MURUKKU,
            pack_size=Decimal("200.00"),
            pack_size_unit="g",
            hsn_code="1905",
            gst_rate=Decimal("0.0500"),
            selling_price_paise=5000,
            base_unit="packet",
            is_active=True,
        )
        db.add(prd)
        db.flush()

    # 2. Setup Retailer A (TN) and Distributor B (KA)
    cust_a = db.query(Customer).filter(Customer.customer_code == "CUST-RET-A-DSP").first()
    if not cust_a:
        cust_a = Customer(
            customer_code="CUST-RET-A-DSP",
            customer_name="Retailer A (Sri Krishna Stores)",
            customer_type=CustomerType.RETAILER,
            contact_person="K. Krishnan",
            phone="9840123456",
            email="krishna_dsp@example.com",
            gstin="33AAAAA0000A1Z5",
            billing_address="14 North Car Street",
            shipping_address="14 North Car Street",
            city="Tiruchirappalli",
            state="Tamil Nadu",
            state_code="33",
            pincode="620006",
            is_active=True,
        )
        db.add(cust_a)
        db.flush()

    cust_b = db.query(Customer).filter(Customer.customer_code == "CUST-DIST-B-DSP").first()
    if not cust_b:
        cust_b = Customer(
            customer_code="CUST-DIST-B-DSP",
            customer_name="Distributor B (Cauvery Dist)",
            customer_type=CustomerType.DISTRIBUTOR,
            contact_person="A. Kumar",
            phone="9840999888",
            email="cauvery@example.com",
            gstin="29AAAAA0000A1Z5",
            billing_address="55 MG Road",
            shipping_address="55 MG Road",
            city="Bangalore",
            state="Karnataka",
            state_code="29",
            pincode="560001",
            is_active=True,
        )
        db.add(cust_b)
        db.flush()

    # 3. Setup Initial FG Stock: exactly 238 packets (as resulting from Phase 4)
    bal = db.query(InventoryBalance).filter(
        InventoryBalance.item_type == InventoryItemType.FG,
        InventoryBalance.item_id == str(prd.id),
    ).first()
    if not bal:
        bal = InventoryBalance(
            item_type=InventoryItemType.FG,
            item_id=str(prd.id),
            cached_qty=Decimal("238.0000"),
            total_value_paise=741132,  # 238 * ~31.14
        )
        db.add(bal)
    else:
        bal.cached_qty = Decimal("238.0000")
        bal.total_value_paise = 741132
    db.commit()

    # 4. Create & Approve Order for Retailer A (150 packets)
    order_a = SalesOrder(
        order_number="SO-DSP-RET-001",
        customer_id=str(cust_a.id),
        place_of_supply_state_code="33",
        status=SalesOrderStatus.APPROVED,
        taxable_amount_paise=750000,
        cgst_paise=18750,
        sgst_paise=18750,
        grand_total_paise=787500,
        created_by=1,
    )
    db.add(order_a)
    db.flush()
    so_item_a = SalesOrderItem(
        sales_order_id=str(order_a.id),
        product_id=str(prd.id),
        ordered_quantity=Decimal("150.0000"),
        fulfilled_quantity=Decimal("0.0000"),
        unit_price_paise=5000,
        gst_rate=Decimal("5.00"),
        taxable_amount_paise=750000,
        cgst_paise=18750,
        sgst_paise=18750,
        line_total_paise=787500,
    )
    db.add(so_item_a)
    db.commit()

    # Check dispatch status before dispatching
    resp_st = client.get(
        f"/dispatches/orders/{order_a.id}/status",
        headers=admin_headers,
    )
    assert resp_st.status_code == 200
    st_data = resp_st.json()
    assert st_data["can_dispatch"] is True
    assert st_data["items"][0]["pending_quantity"] == "150.0000"
    assert st_data["items"][0]["available_stock_quantity"] == "238.0000"

    # 5. Create Draft Dispatch for Retailer A (150 pkts)
    disp_payload = {
        "sales_order_id": str(order_a.id),
        "transporter_name": "TN Fast Cargo",
        "vehicle_number": "TN-45-AB-1234",
        "notes": "Fragile food packets",
        "items": [
            {
                "sales_order_item_id": str(so_item_a.id),
                "product_id": str(prd.id),
                "quantity_dispatched": "150.0000",
            }
        ],
    }
    resp_disp_create = client.post(
        "/dispatches",
        json=disp_payload,
        headers=admin_headers,
    )
    assert resp_disp_create.status_code == 201
    disp_a_id = resp_disp_create.json()["id"]

    # Stock not yet deducted in DRAFT status
    db.refresh(bal)
    assert bal.cached_qty == Decimal("238.0000")

    # 6. Post Dispatch for Retailer A
    resp_post = client.post(
        f"/dispatches/{disp_a_id}/post",
        headers=admin_headers,
    )
    assert resp_post.status_code == 200
    assert resp_post.json()["status"] == "DISPATCHED"

    # Verify inventory is deducted: 238 - 150 = 88 packets!
    db.refresh(bal)
    assert bal.cached_qty == Decimal("88.0000")

    # Verify order is marked FULFILLED
    db.refresh(order_a)
    db.refresh(so_item_a)
    assert order_a.status == SalesOrderStatus.FULFILLED
    assert so_item_a.fulfilled_quantity == Decimal("150.0000")

    # Verify StockMovement ledger entry
    sm = (
        db.query(StockMovement)
        .filter(
            StockMovement.source_type == "DISPATCH",
            StockMovement.source_id == str(disp_a_id),
        )
        .first()
    )
    assert sm is not None
    assert sm.movement_type == MovementType.INVOICE_DISPATCH
    assert sm.qty_delta == Decimal("-150.0000")

    # 7. Distributor B benchmark: requests 120 packets, but available is only 88 packets!
    order_b = SalesOrder(
        order_number="SO-DSP-DIST-002",
        customer_id=str(cust_b.id),
        place_of_supply_state_code="29",
        status=SalesOrderStatus.APPROVED,
        taxable_amount_paise=504000,
        igst_paise=25200,
        grand_total_paise=529200,
        created_by=1,
    )
    db.add(order_b)
    db.flush()
    so_item_b = SalesOrderItem(
        sales_order_id=str(order_b.id),
        product_id=str(prd.id),
        ordered_quantity=Decimal("120.0000"),
        fulfilled_quantity=Decimal("0.0000"),
        unit_price_paise=4200,
        gst_rate=Decimal("5.00"),
        taxable_amount_paise=504000,
        igst_paise=25200,
        line_total_paise=529200,
    )
    db.add(so_item_b)
    db.commit()

    # Attempt to dispatch 120 packets (should FAIL with 400 Insufficient Stock)
    disp_b_fail_payload = {
        "sales_order_id": str(order_b.id),
        "items": [
            {
                "sales_order_item_id": str(so_item_b.id),
                "product_id": str(prd.id),
                "quantity_dispatched": "120.0000",
            }
        ],
    }
    resp_disp_b_fail = client.post(
        "/dispatches",
        json=disp_b_fail_payload,
        headers=admin_headers,
    )
    assert resp_disp_b_fail.status_code == 400
    assert "Insufficient finished goods stock" in resp_disp_b_fail.json()["detail"]
    assert "Shortage: 32" in resp_disp_b_fail.json()["detail"]

    # 8. Partial Dispatch of exactly 88 packets for Distributor B
    disp_b_partial_payload = {
        "sales_order_id": str(order_b.id),
        "items": [
            {
                "sales_order_item_id": str(so_item_b.id),
                "product_id": str(prd.id),
                "quantity_dispatched": "88.0000",
            }
        ],
    }
    resp_disp_b_create = client.post(
        "/dispatches",
        json=disp_b_partial_payload,
        headers=admin_headers,
    )
    assert resp_disp_b_create.status_code == 201
    disp_b_id = resp_disp_b_create.json()["id"]

    # Post partial dispatch
    resp_disp_b_post = client.post(
        f"/dispatches/{disp_b_id}/post",
        headers=admin_headers,
    )
    assert resp_disp_b_post.status_code == 200

    # Stock should now be exactly 0
    db.refresh(bal)
    assert bal.cached_qty == Decimal("0.0000")

    # Order B should be PARTIALLY_FULFILLED
    db.refresh(order_b)
    db.refresh(so_item_b)
    assert order_b.status == SalesOrderStatus.PARTIALLY_FULFILLED
    assert so_item_b.fulfilled_quantity == Decimal("88.0000")

    # 9. Download Delivery Challan PDF
    resp_challan = client.get(
        f"/dispatches/{disp_a_id}/challan",
        headers=admin_headers,
    )
    assert resp_challan.status_code == 200
    assert resp_challan.headers["content-type"] == "application/pdf"
    assert resp_challan.content.startswith(b"%PDF")
