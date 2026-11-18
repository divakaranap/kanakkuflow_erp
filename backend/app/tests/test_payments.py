from decimal import Decimal
from datetime import date
import pytest
from fastapi.testclient import TestClient

from backend.app.models.user import User, UserRole
from backend.app.models.customer import Customer, CustomerType
from backend.app.models.product import Product, ProductCategory
from backend.app.models.sales import SalesOrder, SalesOrderItem, SalesInvoice, SalesOrderStatus, InvoiceStatus
from backend.app.models.payment import CustomerPayment, PaymentAllocation, CustomerLedgerEntry, PaymentMode, PaymentStatus


def get_auth_header(client, username, password="demo123"):
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_payments_receivables_and_customer_ledger(client: TestClient, db, seeded_users):
    """
    Test Phase 7 Complete Payment, Allocation, Ledger and Receivables Ageing:
    1. Retailer A has Sales Invoice for ₹7,875 (787,500 paise).
    2. Retailer A pays ₹4,000 (400,000 paise) via UPI.
       - Validate invoice amount_paid becomes ₹4,000, remaining is ₹3,875.
       - Ledger: Debit ₹7,875, Credit ₹4,000 -> Running Balance ₹3,875.
    3. Over-allocation check: Allocating ₹4,500 against remaining ₹3,875 must fail with 400.
    4. Second payment of remaining ₹3,875 (387,500 paise):
       - Invoice becomes fully paid (amount_paid = ₹7,875).
       - Ledger: Running balance becomes ₹0.
    5. Receivables Ageing report verification:
       - Shows accurate age buckets and customer breakdown.
    6. PDF Payment Receipt generation.
    """
    admin_headers = get_auth_header(client, "admin")
    owner_headers = get_auth_header(client, "owner")

    # 1. Create Customer: Retailer A
    cust = db.query(Customer).filter(Customer.customer_code == "CUST-PAY-A").first()
    if not cust:
        cust = Customer(
            customer_code="CUST-PAY-A",
            customer_name="Retailer A (Payment Test)",
            customer_type=CustomerType.RETAILER,
            contact_person="R. Raman",
            phone="9876543210",
            email="raman_pay@example.com",
            gstin="33AABCR1234R1Z1",
            billing_address="12 Big Bazaar Street",
            shipping_address="12 Big Bazaar Street",
            city="Tiruchirappalli",
            district="Tiruchirappalli",
            state="Tamil Nadu",
            state_code="33",
            pincode="620002",
            credit_limit_paise=10000000,
            is_active=True,
        )
        db.add(cust)
        db.flush()

    # 2. Create Product
    prd = db.query(Product).filter(Product.sku == "MUR-PAY-200").first()
    if not prd:
        prd = Product(
            sku="MUR-PAY-200",
            product_name="Murukku 200g (Pay Test)",
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

    # 3. Create and Post an Invoice for ₹7,875 (150 pkts * ₹50 = ₹7,500 + 5% GST = ₹7,875)
    order_res = client.post(
        "/sales/orders",
        json={
            "customer_id": str(cust.id),
            "order_date": str(date.today()),
            "items": [
                {
                    "product_id": str(prd.id),
                    "ordered_quantity": "150.0000",
                    "unit_price_paise": 5000,
                    "discount_paise": 0,
                }
            ],
            "notes": "Test order for payment flow",
        },
        headers=admin_headers,
    )
    assert order_res.status_code == 201
    order_data = order_res.json()
    order_id = order_data["id"]

    # Submit order
    sub_res = client.post(f"/sales/orders/{order_id}/submit", headers=admin_headers)
    assert sub_res.status_code == 200

    # Approve order
    appr_res = client.post(f"/sales/orders/{order_id}/approve", headers=admin_headers)
    assert appr_res.status_code == 200

    # Post invoice
    inv_res = client.post("/sales/invoices", json={"sales_order_id": order_id}, headers=admin_headers)
    assert inv_res.status_code == 201
    inv_data = inv_res.json()
    inv_id = inv_data["id"]
    grand_total_paise = inv_data["grand_total_paise"]
    assert grand_total_paise == 787500  # ₹7,875.00

    # Verify customer ledger has the invoice debit entry
    stmt_res = client.get(f"/payments/ledger/{cust.id}", headers=admin_headers)
    assert stmt_res.status_code == 200
    stmt_data = stmt_res.json()
    assert stmt_data["closing_balance_paise"] == 787500
    assert len(stmt_data["entries"]) >= 1
    inv_entry = [e for e in stmt_data["entries"] if e["reference_document_id"] == inv_id][0]
    assert inv_entry["debit_paise"] == 787500
    assert inv_entry["credit_paise"] == 0

    # Verify unpaid invoices endpoint
    unpaid_res = client.get(f"/payments/unpaid-invoices/{cust.id}", headers=admin_headers)
    assert unpaid_res.status_code == 200
    unpaid_list = unpaid_res.json()
    assert len(unpaid_list) == 1
    assert unpaid_list[0]["id"] == inv_id
    assert unpaid_list[0]["remaining_unpaid_paise"] == 787500

    # 4. Record First Partial Payment: ₹4,000 (400,000 paise) via UPI
    pay1_res = client.post(
        "/payments",
        json={
            "customer_id": str(cust.id),
            "payment_date": str(date.today()),
            "amount_paise": 400000,
            "payment_mode": "UPI",
            "reference_number": "UPI-IND-8829104",
            "notes": "Partial advance via GPay",
            "allocations": [
                {
                    "invoice_id": inv_id,
                    "allocated_amount_paise": 400000,
                }
            ],
        },
        headers=admin_headers,
    )
    assert pay1_res.status_code == 201
    pay1_data = pay1_res.json()
    assert pay1_data["amount_paise"] == 400000
    assert len(pay1_data["allocations"]) == 1
    pay1_id = pay1_data["id"]

    # Verify invoice remaining balance
    unpaid_after_pay1 = client.get(f"/payments/unpaid-invoices/{cust.id}", headers=admin_headers).json()
    assert len(unpaid_after_pay1) == 1
    assert unpaid_after_pay1[0]["amount_paid_paise"] == 400000
    assert unpaid_after_pay1[0]["remaining_unpaid_paise"] == 387500  # ₹3,875 remaining

    # Verify ledger statement
    stmt_after_pay1 = client.get(f"/payments/ledger/{cust.id}", headers=admin_headers).json()
    assert stmt_after_pay1["total_debit_paise"] == 787500
    assert stmt_after_pay1["total_credit_paise"] == 400000
    assert stmt_after_pay1["closing_balance_paise"] == 387500  # ₹3,875 remaining receivable

    # 5. Over-allocation check: Attempting to allocate ₹4,500 when only ₹3,875 is unpaid must fail
    excess_res = client.post(
        "/payments",
        json={
            "customer_id": str(cust.id),
            "amount_paise": 450000,
            "payment_mode": "NEFT",
            "allocations": [
                {
                    "invoice_id": inv_id,
                    "allocated_amount_paise": 450000,
                }
            ],
        },
        headers=admin_headers,
    )
    assert excess_res.status_code == 400
    assert "exceeds remaining unpaid balance" in excess_res.json()["detail"]

    # 6. Receivables Ageing Report check
    ageing_res = client.get("/payments/receivables/ageing", headers=admin_headers)
    assert ageing_res.status_code == 200
    ageing_data = ageing_res.json()
    cust_ageing = [c for c in ageing_data["customers"] if c["customer_id"] == str(cust.id)][0]
    assert cust_ageing["total_outstanding_paise"] == 387500

    # 7. Record Second Payment: ₹3,875 (387,500 paise) to fully clear the balance
    pay2_res = client.post(
        "/payments",
        json={
            "customer_id": str(cust.id),
            "payment_date": str(date.today()),
            "amount_paise": 387500,
            "payment_mode": "NEFT",
            "reference_number": "UTR-HDFC-991244",
            "bank_name": "HDFC Bank",
            "notes": "Balance settlement",
            "allocations": [
                {
                    "invoice_id": inv_id,
                    "allocated_amount_paise": 387500,
                }
            ],
        },
        headers=admin_headers,
    )
    assert pay2_res.status_code == 201

    # Verify customer ledger closing balance is now 0
    stmt_after_pay2 = client.get(f"/payments/ledger/{cust.id}", headers=admin_headers).json()
    assert stmt_after_pay2["closing_balance_paise"] == 0
    assert stmt_after_pay2["total_credit_paise"] == 787500

    # Verify no unpaid invoices remain
    unpaid_after_pay2 = client.get(f"/payments/unpaid-invoices/{cust.id}", headers=admin_headers).json()
    assert len(unpaid_after_pay2) == 0

    # 8. Test Payment Receipt PDF download
    rcpt_pdf_res = client.get(f"/payments/{pay1_id}/receipt", headers=admin_headers)
    assert rcpt_pdf_res.status_code == 200
    assert rcpt_pdf_res.headers["content-type"] == "application/pdf"
    assert rcpt_pdf_res.content.startswith(b"%PDF-")
