from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from backend.app.models.user import User, UserRole
from backend.app.models.customer import Customer, CustomerType
from backend.app.models.product import Product, ProductCategory
from backend.app.models.price_list import PriceList, PriceListItem, PriceListCustomerType
from backend.app.models.inventory import InventoryBalance, InventoryItemType
from backend.app.services.gst_service import calculate_gst, validate_gstin, get_place_of_supply


def test_gst_service_intra_and_inter_state():
    """Verify GST calculations for intra-state (TN) and inter-state (KA)."""
    # 1. Retailer A in Tamil Nadu: Intra-state
    # 150 pkts @ ₹50.00 = ₹7,500.00 (750,000 paise)
    res_tn = calculate_gst(
        taxable_amount_paise=750000,
        gst_rate=Decimal("5.00"),
        place_of_supply_state_code="33",
        seller_state_code="33",
    )
    assert res_tn["tax_type"] == "INTRA_STATE"
    assert res_tn["cgst_paise"] == 18750  # ₹187.50
    assert res_tn["sgst_paise"] == 18750  # ₹187.50
    assert res_tn["igst_paise"] == 0
    assert res_tn["total_tax_paise"] == 37500  # ₹375.00
    assert res_tn["grand_total_paise"] == 787500  # ₹7,875.00

    # 2. Distributor B in Karnataka: Inter-state
    res_ka = calculate_gst(
        taxable_amount_paise=750000,
        gst_rate=Decimal("5.00"),
        place_of_supply_state_code="29",
        seller_state_code="33",
    )
    assert res_ka["tax_type"] == "INTER_STATE"
    assert res_ka["cgst_paise"] == 0
    assert res_ka["sgst_paise"] == 0
    assert res_ka["igst_paise"] == 37500  # ₹375.00
    assert res_ka["total_tax_paise"] == 37500
    assert res_ka["grand_total_paise"] == 787500

    # 3. GSTIN validation
    assert validate_gstin("33AAAAA0000A1Z5") is True
    assert validate_gstin("INVALID_GSTIN") is False
    assert get_place_of_supply("33AAAAA0000A1Z5") == "33"
    assert get_place_of_supply("29") == "29"


def get_auth_header(client, username, password="demo123"):
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_sales_order_and_invoice_workflow(client: TestClient, db, seeded_users):
    """
    Test complete Phase 5 Sales lifecycle:
    Order creation (DRAFT) -> Submit -> Admin Approval -> GST Invoice Generation -> PDF download.
    Ensure inventory is NOT prematurely deducted.
    """
    sales_headers = get_auth_header(client, "salesA")
    admin_headers = get_auth_header(client, "admin")
    # 1. Setup Product (Murukku 200g)
    prd = db.query(Product).filter(Product.sku == "MUR-200-SALES").first()
    if not prd:
        prd = Product(
            sku="MUR-200-SALES",
            product_name="Murukku 200g (Sales Test)",
            category=ProductCategory.MURUKKU,
            pack_size=Decimal("200.00"),
            pack_size_unit="g",
            hsn_code="1905",
            gst_rate=Decimal("0.0500"),
            selling_price_paise=5000,  # ₹50.00
            base_unit="packet",
            is_active=True,
        )
        db.add(prd)
        db.flush()

    # 2. Setup Retailer A in Tamil Nadu
    cust_a = db.query(Customer).filter(Customer.customer_code == "CUST-RET-A-TEST").first()
    if not cust_a:
        cust_a = Customer(
            customer_code="CUST-RET-A-TEST",
            customer_name="Retailer A (Sri Krishna Stores)",
            customer_type=CustomerType.RETAILER,
            contact_person="K. Krishnan",
            phone="9840123456",
            email="krishna@example.com",
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

    # 3. Setup Initial FG Stock: 238 packets
    bal = db.query(InventoryBalance).filter(
        InventoryBalance.item_type == InventoryItemType.FG,
        InventoryBalance.item_id == prd.id,
    ).first()
    if not bal:
        bal = InventoryBalance(
            item_type=InventoryItemType.FG,
            item_id=prd.id,
            cached_qty=Decimal("238.0000"),
            total_value_paise=741132,
        )
        db.add(bal)
    else:
        bal.cached_qty = Decimal("238.0000")
    db.commit()

    # 4. Check Stock API
    resp_chk = client.get(
        f"/sales/check-stock?product_id={prd.id}&quantity=150",
        headers=sales_headers,
    )
    assert resp_chk.status_code == 200
    chk_data = resp_chk.json()
    assert chk_data["available_qty"] == "238.0000"
    assert chk_data["is_sufficient"] is True

    # 5. Create Sales Order as Salesman
    so_payload = {
        "customer_id": str(cust_a.id),
        "notes": "Urgent festive delivery",
        "items": [
            {
                "product_id": str(prd.id),
                "ordered_quantity": "150.0000",
                "unit_price_paise": 5000,
            }
        ],
    }
    resp_create = client.post(
        "/sales/orders",
        json=so_payload,
        headers=sales_headers,
    )
    assert resp_create.status_code == 201
    so_data = resp_create.json()
    order_id = so_data["id"]

    assert so_data["status"] == "DRAFT"
    assert so_data["taxable_amount_paise"] == 750000  # ₹7,500.00
    assert so_data["cgst_paise"] == 18750              # ₹187.50
    assert so_data["sgst_paise"] == 18750              # ₹187.50
    assert so_data["igst_paise"] == 0
    assert so_data["grand_total_paise"] == 787500      # ₹7,875.00

    # Verify inventory is NOT deducted
    db.refresh(bal)
    assert bal.cached_qty == Decimal("238.0000")

    # 6. Submit Sales Order
    resp_submit = client.post(
        f"/sales/orders/{order_id}/submit",
        headers=sales_headers,
    )
    assert resp_submit.status_code == 200
    assert resp_submit.json()["status"] == "SUBMITTED"

    # 7. Approve Sales Order as Admin
    resp_appr = client.post(
        f"/sales/orders/{order_id}/approve",
        headers=admin_headers,
    )
    assert resp_appr.status_code == 200
    assert resp_appr.json()["status"] == "APPROVED"

    # Verify inventory STILL not deducted
    db.refresh(bal)
    assert bal.cached_qty == Decimal("238.0000")

    # 8. Create & Post Sales Invoice
    inv_payload = {"sales_order_id": order_id}
    resp_inv = client.post(
        "/sales/invoices",
        json=inv_payload,
        headers=admin_headers,
    )
    assert resp_inv.status_code == 201
    inv_data = resp_inv.json()
    invoice_id = inv_data["id"]

    assert inv_data["status"] == "POSTED"
    assert inv_data["taxable_amount_paise"] == 750000
    assert inv_data["cgst_paise"] == 18750
    assert inv_data["sgst_paise"] == 18750
    assert inv_data["igst_paise"] == 0
    assert inv_data["grand_total_paise"] == 787500
    assert len(inv_data["items"]) == 1
    assert inv_data["items"][0]["product_name"] == "Murukku 200g (Sales Test)"

    # Verify inventory STILL not deducted (will be deducted on Dispatch in Phase 6)
    db.refresh(bal)
    assert bal.cached_qty == Decimal("238.0000")

    # 9. Download PDF Invoice
    resp_pdf = client.get(
        f"/sales/invoices/{invoice_id}/pdf",
        headers=admin_headers,
    )
    assert resp_pdf.status_code == 200
    assert resp_pdf.headers["content-type"] == "application/pdf"
    assert resp_pdf.content.startswith(b"%PDF")
