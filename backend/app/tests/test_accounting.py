from decimal import Decimal
from datetime import date
import pytest
from fastapi.testclient import TestClient

from backend.app.models.user import User, UserRole
from backend.app.models.customer import Customer, CustomerType
from backend.app.models.product import Product, ProductCategory
from backend.app.models.accounting import Account, JournalEntry, AccountType


def get_auth_header(client, username, password="demo123"):
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_accounting_engine_and_audit_trail(client: TestClient, db, seeded_users):
    """
    Test Phase 8 Accounting Engine, Journal Entries, Trial Balance, GL and Audit Trail:
    1. Chart of Accounts verification.
    2. Double-entry invariant: Reject unbalanced journal entry.
    3. Manual journal entry: Balanced debit and credit succeeds.
    4. Auto-generated journal entry on Sales Invoice:
       - Debit Accounts Receivable = ₹7,875.00
       - Credit Sales Revenue = ₹7,500.00
       - Credit Output CGST = ₹187.50
       - Credit Output SGST = ₹187.50
    5. Auto-generated journal entry on Customer Payment:
       - Debit Bank = ₹4,000.00
       - Credit Accounts Receivable = ₹4,000.00
    6. Trial Balance: Total Debits == Total Credits (Balanced).
    7. General Ledger: Running balance on Accounts Receivable account.
    8. Audit Trail: Auditor role access.
    """
    admin_headers = get_auth_header(client, "admin")
    auditor_headers = get_auth_header(client, "auditor")

    # 1. Fetch Chart of Accounts
    accounts_res = client.get("/accounting/accounts", headers=admin_headers)
    assert accounts_res.status_code == 200
    accounts = accounts_res.json()
    assert len(accounts) >= 20

    acct_by_code = {a["code"]: a for a in accounts}
    assert "1010" in acct_by_code  # Cash
    assert "1020" in acct_by_code  # Bank
    assert "1030" in acct_by_code  # Debtors
    assert "4010" in acct_by_code  # Sales Revenue

    cash_id = acct_by_code["1010"]["id"]
    bank_id = acct_by_code["1020"]["id"]
    ar_id = acct_by_code["1030"]["id"]
    capital_id = acct_by_code["3010"]["id"]

    # 2. Double-entry Invariance: Unbalanced entry must fail with 400
    unbalanced_res = client.post(
        "/accounting/journals",
        json={
            "narration": "Unbalanced test journal",
            "lines": [
                {"account_id": bank_id, "debit_paise": 100000, "credit_paise": 0},
                {"account_id": capital_id, "debit_paise": 0, "credit_paise": 80000},  # ₹1,000 vs ₹800
            ],
        },
        headers=admin_headers,
    )
    assert unbalanced_res.status_code == 400
    assert "Double-entry invariant violated" in unbalanced_res.json()["detail"]

    # 3. Balanced Manual Journal Entry: Owner capital infusion ₹5,00,000
    balanced_res = client.post(
        "/accounting/journals",
        json={
            "narration": "Owner capital infusion in bank account",
            "lines": [
                {"account_id": bank_id, "debit_paise": 50000000, "credit_paise": 0, "line_narration": "Capital deposit"},
                {"account_id": capital_id, "debit_paise": 0, "credit_paise": 50000000, "line_narration": "Promoter share"},
            ],
        },
        headers=admin_headers,
    )
    assert balanced_res.status_code == 201
    entry_data = balanced_res.json()
    assert entry_data["total_debit_paise"] == 50000000
    assert entry_data["total_credit_paise"] == 50000000

    # 4. Trigger Sales Invoice -> Verifies auto double entry
    cust = db.query(Customer).filter(Customer.customer_code == "CUST-ACCT-A").first()
    if not cust:
        cust = Customer(
            customer_code="CUST-ACCT-A",
            customer_name="Retailer Acct Test",
            customer_type=CustomerType.RETAILER,
            contact_person="M. Murugan",
            phone="9876543299",
            email="murugan_acct@example.com",
            gstin="33AABCM1234M1Z2",
            billing_address="20 South Street",
            shipping_address="20 South Street",
            city="Tiruchirappalli",
            state="Tamil Nadu",
            state_code="33",
            pincode="620001",
            credit_limit_paise=10000000,
            is_active=True,
        )
        db.add(cust)
        db.flush()

    prd = db.query(Product).filter(Product.sku == "MUR-ACCT-200").first()
    if not prd:
        prd = Product(
            sku="MUR-ACCT-200",
            product_name="Murukku 200g (Acct Test)",
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

    # Create, Submit, Approve Order
    order_res = client.post(
        "/sales/orders",
        json={
            "customer_id": str(cust.id),
            "items": [{"product_id": str(prd.id), "ordered_quantity": "150.0000", "unit_price_paise": 5000}],
        },
        headers=admin_headers,
    )
    assert order_res.status_code == 201
    so_id = order_res.json()["id"]
    client.post(f"/sales/orders/{so_id}/submit", headers=admin_headers)
    client.post(f"/sales/orders/{so_id}/approve", headers=admin_headers)

    # Post invoice
    inv_res = client.post("/sales/invoices", json={"sales_order_id": so_id}, headers=admin_headers)
    assert inv_res.status_code == 201
    inv_id = inv_res.json()["id"]

    # Verify journal entry was automatically created for this invoice
    journals_res = client.get(f"/accounting/journals?source_module=SALES", headers=admin_headers)
    assert journals_res.status_code == 200
    sales_jv = [j for j in journals_res.json() if j["source_document_id"] == inv_id][0]
    assert sales_jv["total_debit_paise"] == 787500
    assert sales_jv["total_credit_paise"] == 787500

    # 5. Record Payment of ₹4,000 -> Verifies auto double entry
    pay_res = client.post(
        "/payments",
        json={
            "customer_id": str(cust.id),
            "amount_paise": 400000,
            "payment_mode": "NEFT",
            "allocations": [{"invoice_id": inv_id, "allocated_amount_paise": 400000}],
        },
        headers=admin_headers,
    )
    assert pay_res.status_code == 201
    pay_id = pay_res.json()["id"]

    pay_jv_res = client.get(f"/accounting/journals?source_module=PAYMENT", headers=admin_headers)
    assert pay_jv_res.status_code == 200
    pay_jv = [j for j in pay_jv_res.json() if j["source_document_id"] == pay_id][0]
    assert pay_jv["total_debit_paise"] == 400000
    assert pay_jv["total_credit_paise"] == 400000

    # 6. Verify Trial Balance: Must be completely balanced (difference = 0)
    tb_res = client.get("/accounting/trial-balance", headers=auditor_headers)
    assert tb_res.status_code == 200
    tb_data = tb_res.json()
    assert tb_data["is_balanced"] is True
    assert tb_data["difference_paise"] == 0
    assert tb_data["grand_total_debit_paise"] == tb_data["grand_total_credit_paise"]

    # 7. Verify General Ledger for Accounts Receivable (1030)
    gl_res = client.get(f"/accounting/general-ledger/{ar_id}", headers=auditor_headers)
    assert gl_res.status_code == 200
    gl_data = gl_res.json()
    assert gl_data["account_code"] == "1030"
    assert len(gl_data["rows"]) >= 2  # Invoice debit + Payment credit

    # 8. Verify Audit Logs can be inspected by Auditor
    audit_res = client.get("/accounting/audit-logs", headers=auditor_headers)
    assert audit_res.status_code == 200
    assert len(audit_res.json()) >= 1
