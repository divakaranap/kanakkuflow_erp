from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.models.user import User, UserRole
from backend.app.models.customer import Customer, CustomerType
from backend.app.models.supplier import Supplier
from backend.app.models.product import Product, ProductCategory
from backend.app.models.raw_material import RawMaterial, RawMaterialCategory
from backend.app.models.packaging import PackagingItem, PackagingCategory
from backend.app.models.sales import SalesOrderStatus, InvoiceStatus
from backend.app.models.dispatch import DispatchStatus
from backend.app.models.payment import PaymentMode, PaymentStatus
from backend.app.models.accounting import JournalEntry, AuditLog
from backend.app.services.accounting_service import seed_chart_of_accounts, get_trial_balance
from backend.app.services.audit_service import log_audit_event


def get_auth_header(client: TestClient, username: str, password: str = "demo123"):
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_master_e2e_order_to_audit_benchmark_lifecycle(client: TestClient, db, seeded_users):
    """
    MASTER END-TO-END BENCHMARK INTEGRATION TEST (NIT Tiruchirappalli Challenge Evaluation)
    ======================================================================================
    This single test executes the complete 8-stage manufacturing ERP lifecycle:
      Step A: Raw Material Purchase & Initial Stock Setup
      Step B: Standard BOM Recipe Definition for Murukku 200g
      Step C: Production Run Execution with Yield Variance Analysis (238 packets yield)
      Step D: Sales Order & GST Invoice Generation for Retailer A (150 packets @ ₹50 = ₹7,875)
      Step E: Dispatch Execution & Finished Goods Stock Reduction (238 -> 88 packets)
      Step F: Stock Shortage Detection & Partial Fulfillment for Distributor B (88 -> 0 packets)
      Step G: Partial Customer Payment Recording & Receivables Ageing (₹4,000 paid, ₹3,875 balance)
      Step H: Immutable Double-Entry Ledger, Balanced Trial Balance & Audit Trail Verification
    """
    admin_hdr = get_auth_header(client, "admin")
    prod_hdr = get_auth_header(client, "prod")
    sales_hdr = get_auth_header(client, "salesA")
    auditor_hdr = get_auth_header(client, "auditor")

    # Seed Standard Chart of Accounts
    seed_chart_of_accounts(db)

    # -------------------------------------------------------------------------
    # STEP A: Raw Material Purchase & Initial Stock Setup
    # -------------------------------------------------------------------------
    # 1. Create Supplier
    supplier = Supplier(
        supplier_code="SUP-E2E-AGRO",
        supplier_name="Madurai Agro Commodities",
        contact_person="Muthuvel",
        phone="9876543210",
        email="muthu@maduraiagro.com",
        gstin="33AABCM1234D1Z5",
        address="Bazaar Street, Madurai",
        city="Madurai",
        state="Tamil Nadu",
        state_code="33",
        pincode="625001",
        is_active=True,
    )
    db.add(supplier)
    db.flush()

    # 2. Create Raw Materials
    flour = RawMaterial(
        material_code="RM-RICE-E2E",
        material_name="Rice Flour (E2E Benchmark)",
        category=RawMaterialCategory.FLOUR,
        base_unit="kg",
        reorder_level=Decimal("20.0000"),
        is_active=True,
    )
    oil = RawMaterial(
        material_code="RM-OIL-E2E",
        material_name="Cooking Oil (E2E Benchmark)",
        category=RawMaterialCategory.OIL,
        base_unit="litre",
        reorder_level=Decimal("10.0000"),
        is_active=True,
    )
    spice = RawMaterial(
        material_code="RM-SPICE-E2E",
        material_name="Spice Mix (E2E Benchmark)",
        category=RawMaterialCategory.SPICE,
        base_unit="kg",
        reorder_level=Decimal("2.0000"),
        is_active=True,
    )
    # 3. Create Packaging
    pouch = PackagingItem(
        packaging_code="PKG-POUCH-E2E",
        packaging_name="Murukku 200g Printed Pouch (E2E)",
        category=PackagingCategory.POUCH,
        base_unit="piece",
        reorder_level=Decimal("200.0000"),
        is_active=True,
    )
    carton = PackagingItem(
        packaging_code="PKG-BOX-E2E",
        packaging_name="Corrugated Shipping Box (E2E)",
        category=PackagingCategory.CARTON,
        base_unit="piece",
        reorder_level=Decimal("10.0000"),
        is_active=True,
    )
    # 4. Create Product: Murukku 200g
    murukku = Product(
        sku="MUR-200-E2E",
        product_name="Murukku 200g (E2E Benchmark)",
        category=ProductCategory.MURUKKU,
        base_unit="packet",
        pack_size=Decimal("200.00"),
        pack_size_unit="g",
        hsn_code="1905",
        gst_rate=Decimal("0.0500"),
        selling_price_paise=5000,  # ₹50.00
        reorder_level=Decimal("50.0000"),
        is_active=True,
    )
    db.add_all([flour, oil, spice, pouch, carton, murukku])
    db.flush()

    # 5. Record Opening Stock
    # Flour 100 kg @ ₹40.00/kg (4,000 paise)
    client.post("/inventory/opening-stock", json={
        "item_type": "RAW", "item_id": flour.id, "quantity": "100.0000", "unit_cost_paise": 4000
    }, headers=admin_hdr)
    # Oil 50 L @ ₹120.00/L (12,000 paise)
    client.post("/inventory/opening-stock", json={
        "item_type": "RAW", "item_id": oil.id, "quantity": "50.0000", "unit_cost_paise": 12000
    }, headers=admin_hdr)
    # Spice 10 kg @ ₹150.00/kg (15,000 paise)
    client.post("/inventory/opening-stock", json={
        "item_type": "RAW", "item_id": spice.id, "quantity": "10.0000", "unit_cost_paise": 15000
    }, headers=admin_hdr)
    # Pouches 1000 pcs @ ₹1.50/pc (150 paise)
    client.post("/inventory/opening-stock", json={
        "item_type": "PACKAGING", "item_id": pouch.id, "quantity": "1000.0000", "unit_cost_paise": 150
    }, headers=admin_hdr)
    # Cartons 100 pcs @ ₹15.00/pc (1,500 paise)
    client.post("/inventory/opening-stock", json={
        "item_type": "PACKAGING", "item_id": carton.id, "quantity": "100.0000", "unit_cost_paise": 1500
    }, headers=admin_hdr)
    # Opening FG Murukku: 0 packets
    client.post("/inventory/opening-stock", json={
        "item_type": "FG", "item_id": murukku.id, "quantity": "0.0000", "unit_cost_paise": 3200
    }, headers=admin_hdr)

    # -------------------------------------------------------------------------
    # STEP B: Standard BOM Recipe Definition for Murukku 200g
    # -------------------------------------------------------------------------
    # Standard 1 Batch = 250 packets output (50 kg net finished goods)
    bom_res = client.post(
        "/boms",
        json={
            "product_id": murukku.id,
            "batch_yield_packets": "250.0000",
            "tolerance_pct": "5.00",
            "description": "Standard Recipe for Murukku 200g (250 pkts)",
            "items": [
                {"item_type": "RAW", "item_id": flour.id, "quantity_per_batch": "35.0000", "unit": "kg"},
                {"item_type": "RAW", "item_id": oil.id, "quantity_per_batch": "5.0000", "unit": "litre"},
                {"item_type": "RAW", "item_id": spice.id, "quantity_per_batch": "1.0000", "unit": "kg"},
                {"item_type": "PACKAGING", "item_id": pouch.id, "quantity_per_batch": "250.0000", "unit": "piece"},
                {"item_type": "PACKAGING", "item_id": carton.id, "quantity_per_batch": "12.5000", "unit": "piece"},
            ],
        },
        headers=prod_hdr,
    )
    assert bom_res.status_code == 201
    bom_id = bom_res.json()["id"]

    # Activate BOM
    client.post(f"/boms/{bom_id}/activate", headers=admin_hdr)

    # -------------------------------------------------------------------------
    # STEP C: Production Run with Yield Variance (238 packets actual yield)
    # -------------------------------------------------------------------------
    run_payload = {
        "product_id": murukku.id,
        "bom_id": bom_id,
        "batch_number": "BATCH-E2E-BENCHMARK-01",
        "number_of_batches": "1.00",
        "actual_good_output": "238.0000",  # Actual output: 238 pkts (planned 250)
        "damaged_packaging": "12.0000",
        "notes": "E2E Benchmark Run with 238 packets output",
        "materials": [
            {"item_type": "RAW", "item_id": flour.id, "issued_quantity": "35.0000", "unit": "kg"},
            {"item_type": "RAW", "item_id": oil.id, "issued_quantity": "5.0000", "unit": "litre"},
            {"item_type": "RAW", "item_id": spice.id, "issued_quantity": "1.0000", "unit": "kg"},
            {"item_type": "PACKAGING", "item_id": pouch.id, "issued_quantity": "250.0000", "unit": "piece"},
            {"item_type": "PACKAGING", "item_id": carton.id, "issued_quantity": "12.0000", "unit": "piece"},
        ],
        "overheads": [
            {"expense_type": "LABOUR", "amount_paise": 100000, "description": "Production staff labour"},
            {"expense_type": "GAS", "amount_paise": 50000, "description": "LPG heating fuel"},
        ],
    }
    create_run_res = client.post("/production-runs", json=run_payload, headers=prod_hdr)
    assert create_run_res.status_code == 201
    run_id = create_run_res.json()["id"]

    # Verify Variance Analysis Pre-Posting:
    # Yield variance = ((238 - 250) / 250) * 100 = -4.80%
    var_res = client.get(f"/production-runs/{run_id}/variance", headers=prod_hdr)
    assert var_res.status_code == 200
    var_data = var_res.json()
    assert Decimal(str(var_data["yield_variance_pct"])) == Decimal("-4.80")
    assert Decimal(str(var_data["actual_good_output"])) == Decimal("238.0000")

    # Post Production Run
    post_run_res = client.post(f"/production-runs/{run_id}/post", headers=prod_hdr)
    assert post_run_res.status_code == 200

    # Verify FG Murukku stock is now exactly 238 packets
    fg_stock = client.get(f"/stock/summary/FG/{murukku.id}", headers=admin_hdr).json()
    assert Decimal(str(fg_stock["current_stock"])) == Decimal("238.0000")

    # -------------------------------------------------------------------------
    # STEP D: Sales Order & GST Invoice for Retailer A (150 pkts @ ₹50 = ₹7,875)
    # -------------------------------------------------------------------------
    # Create Customer: Retailer A in Tamil Nadu (Intra-state, Code 33)
    retailer_a = Customer(
        customer_code="CUST-RET-A-E2E",
        customer_name="Sri Krishna Stores (Retailer A)",
        customer_type=CustomerType.RETAILER,
        contact_person="Natarajan",
        phone="9876543211",
        email="krishna.stores@example.com",
        gstin="33AAAAA0000A1Z5",
        billing_address="10 South Masi St, Madurai",
        shipping_address="10 South Masi St, Madurai",
        city="Madurai",
        district="Madurai",
        state="Tamil Nadu",
        state_code="33",
        pincode="625001",
        credit_limit_paise=5000000,
        is_active=True,
    )
    # Create Customer: Distributor B in Karnataka (Inter-state, Code 29)
    distributor_b = Customer(
        customer_code="CUST-DIST-B-E2E",
        customer_name="Bengaluru Distributors (Distributor B)",
        customer_type=CustomerType.DISTRIBUTOR,
        contact_person="Venkatesh",
        phone="9876543212",
        email="blr.dist@example.com",
        gstin="29AAAAA0000A1Z5",
        billing_address="45 Commercial St, Bengaluru",
        shipping_address="45 Commercial St, Bengaluru",
        city="Bengaluru",
        district="Bengaluru",
        state="Karnataka",
        state_code="29",
        pincode="560001",
        credit_limit_paise=10000000,
        is_active=True,
    )
    db.add_all([retailer_a, distributor_b])
    db.flush()

    # Retailer A orders 150 pkts @ ₹50.00
    so_res = client.post(
        "/sales/orders",
        json={
            "customer_id": retailer_a.id,
            "notes": "Retailer A benchmark order for 150 packets",
            "items": [
                {
                    "product_id": murukku.id,
                    "ordered_quantity": 150,
                    "unit_price_paise": 5000,
                }
            ],
        },
        headers=sales_hdr,
    )
    assert so_res.status_code == 201
    order_a_data = so_res.json()
    order_a_id = order_a_data["id"]
    order_a_item_id = order_a_data["items"][0]["id"]

    # Submit and Approve Sales Order
    client.post(f"/sales/orders/{order_a_id}/submit", headers=sales_hdr)
    client.post(f"/sales/orders/{order_a_id}/approve", headers=admin_hdr)

    # Generate and Post GST Invoice for Retailer A
    inv_res = client.post("/sales/invoices", json={"sales_order_id": order_a_id}, headers=admin_hdr)
    assert inv_res.status_code == 201
    inv_data = inv_res.json()
    invoice_a_id = inv_data["id"]

    # Verify EXACT benchmark amounts:
    # 150 pkts * ₹50 = ₹7,500.00 taxable (750,000 paise)
    # Intra-state 5% GST: CGST 2.5% = ₹187.50 (18,750 paise), SGST 2.5% = ₹187.50 (18,750 paise), IGST = 0
    # Grand total = ₹7,875.00 (787,500 paise)
    assert inv_data["taxable_amount_paise"] == 750000
    assert inv_data["cgst_paise"] == 18750
    assert inv_data["sgst_paise"] == 18750
    assert inv_data["igst_paise"] == 0
    assert inv_data["total_tax_paise"] == 37500
    assert inv_data["grand_total_paise"] == 787500

    # CRITICAL INVARIANCE: Inventory must NOT be deducted by invoice generation!
    fg_stock_after_inv = client.get(f"/stock/summary/FG/{murukku.id}", headers=admin_hdr).json()
    assert Decimal(str(fg_stock_after_inv["current_stock"])) == Decimal("238.0000")

    # -------------------------------------------------------------------------
    # STEP E: Dispatch Execution & Finished Goods Stock Reduction (238 -> 88 pkts)
    # -------------------------------------------------------------------------
    dispatch_res = client.post(
        "/dispatches",
        json={
            "sales_order_id": order_a_id,
            "vehicle_number": "TN-59-AB-1234",
            "driver_name": "Selvam",
            "driver_phone": "9876543219",
            "transporter_name": "Sri Krishna Express",
            "notes": "Delivered to Retailer A in Madurai",
            "items": [
                {
                    "sales_order_item_id": order_a_item_id,
                    "product_id": murukku.id,
                    "quantity_dispatched": "150.0000",
                }
            ],
        },
        headers=prod_hdr,
    )
    assert dispatch_res.status_code == 201
    dispatch_id = dispatch_res.json()["id"]

    # Post Dispatch to atomically reduce finished goods stock
    post_dispatch_res = client.post(f"/dispatches/{dispatch_id}/post", headers=prod_hdr)
    assert post_dispatch_res.status_code == 200

    # Stock must now drop from 238 to exactly 88 packets (238 - 150 = 88)
    fg_stock_after_disp = client.get(f"/stock/summary/FG/{murukku.id}", headers=admin_hdr).json()
    assert Decimal(str(fg_stock_after_disp["current_stock"])) == Decimal("88.0000")

    # -------------------------------------------------------------------------
    # STEP F: Stock Shortage Detection & Partial Fulfillment for Distributor B
    # -------------------------------------------------------------------------
    # Distributor B attempts to order 120 packets
    stock_chk_res = client.get(f"/sales/check-stock?product_id={murukku.id}&quantity=120", headers=sales_hdr)
    assert stock_chk_res.status_code == 200
    chk_info = stock_chk_res.json()
    assert Decimal(str(chk_info["available_qty"])) == Decimal("88.0000")
    assert Decimal(str(chk_info["requested_qty"])) == Decimal("120.0000")
    assert chk_info["is_sufficient"] is False
    assert Decimal(str(chk_info["shortage_qty"])) == Decimal("32.0000")  # 120 - 88 = 32 packets shortage prevented!

    # Fulfill available 88 packets for Distributor B
    so_b_res = client.post(
        "/sales/orders",
        json={
            "customer_id": distributor_b.id,
            "notes": "Partial fulfillment of available 88 packets",
            "items": [
                {
                    "product_id": murukku.id,
                    "ordered_quantity": 88,
                    "unit_price_paise": 5000,
                }
            ],
        },
        headers=sales_hdr,
    )
    assert so_b_res.status_code == 201
    order_b_data = so_b_res.json()
    order_b_id = order_b_data["id"]
    order_b_item_id = order_b_data["items"][0]["id"]

    client.post(f"/sales/orders/{order_b_id}/submit", headers=sales_hdr)
    client.post(f"/sales/orders/{order_b_id}/approve", headers=admin_hdr)
    client.post("/sales/invoices", json={"sales_order_id": order_b_id}, headers=admin_hdr)

    # Dispatch remaining 88 packets
    disp_b_res = client.post(
        "/dispatches",
        json={
            "sales_order_id": order_b_id,
            "vehicle_number": "KA-01-EF-5678",
            "items": [
                {
                    "sales_order_item_id": order_b_item_id,
                    "product_id": murukku.id,
                    "quantity_dispatched": "88.0000",
                }
            ],
        },
        headers=prod_hdr,
    )
    assert disp_b_res.status_code == 201
    client.post(f"/dispatches/{disp_b_res.json()['id']}/post", headers=prod_hdr)

    # Stock must now drop from 88 to exactly 0 packets!
    fg_stock_final = client.get(f"/stock/summary/FG/{murukku.id}", headers=admin_hdr).json()
    assert Decimal(str(fg_stock_final["current_stock"])) == Decimal("0.0000")

    # -------------------------------------------------------------------------
    # STEP G: Customer Payment & Receivables Ageing (₹4,000 paid, ₹3,875 balance)
    # -------------------------------------------------------------------------
    # Retailer A owes ₹7,875.00. Records partial payment of ₹4,000.00 via Bank Transfer.
    pay_res = client.post(
        "/payments",
        json={
            "customer_id": retailer_a.id,
            "payment_date": str(inv_data["invoice_date"]),
            "amount_paise": 400000,  # ₹4,000.00
            "payment_mode": PaymentMode.NEFT.value,
            "reference_number": "UTR-BENCHMARK-4000",
            "allocations": [
                {
                    "invoice_id": invoice_a_id,
                    "allocated_amount_paise": 400000,
                }
            ],
        },
        headers=sales_hdr,
    )
    assert pay_res.status_code == 201

    # Verify Customer Ledger:
    # Debit: Invoice ₹7,875.00
    # Credit: Payment ₹4,000.00
    # Net Outstanding Balance: ₹3,875.00 (387,500 paise)
    ledger_res = client.get(f"/payments/ledger/{retailer_a.id}", headers=sales_hdr)
    assert ledger_res.status_code == 200
    ledger_data = ledger_res.json()
    assert ledger_data["closing_balance_paise"] == 387500
    assert ledger_data["total_debit_paise"] == 787500
    assert ledger_data["total_credit_paise"] == 400000

    # Verify Receivables Ageing:
    ageing_res = client.get("/payments/receivables/ageing", headers=auditor_hdr)
    assert ageing_res.status_code == 200
    ageing_data = ageing_res.json()
    assert ageing_data["total_receivables_paise"] >= 387500
    retailer_a_bucket = next(c for c in ageing_data["customers"] if c["customer_id"] == retailer_a.id)
    assert retailer_a_bucket["total_outstanding_paise"] == 387500
    assert retailer_a_bucket["not_due_paise"] + retailer_a_bucket["days_0_to_30_paise"] == 387500

    # -------------------------------------------------------------------------
    # STEP H: Immutable Double-Entry Ledger, Balanced Trial Balance & Audit Trail
    # -------------------------------------------------------------------------
    # 1. Verify Trial Balance is balanced: sum(Debits) == sum(Credits)
    tb = get_trial_balance(db)
    assert tb.is_balanced is True
    assert tb.difference_paise == 0
    assert tb.grand_total_debit_paise == tb.grand_total_credit_paise
    assert tb.grand_total_debit_paise > 0

    # 2. Record & Verify Audit Trail
    admin_user = db.query(User).filter(User.username == "admin").first()
    log_audit_event(
        db,
        user=admin_user,
        action="BENCHMARK_E2E_VERIFIED",
        entity_type="SYSTEM",
        entity_id="bench-01",
        details="NIT Trichy 8-stage benchmark lifecycle verified successfully",
    )
    db.commit()

    audit_res = client.get("/accounting/audit-logs", headers=auditor_hdr)
    assert audit_res.status_code == 200
    audit_logs = audit_res.json()
    assert len(audit_logs) >= 1
    assert any(a["action"] == "BENCHMARK_E2E_VERIFIED" for a in audit_logs)

    # 3. Verify Executive Dashboard summary endpoint reflects all benchmark figures
    dash_res = client.get("/analytics/dashboard-summary", headers=admin_hdr)
    assert dash_res.status_code == 200
    dash_summary = dash_res.json()
    assert dash_summary["sales"]["total_revenue_paise"] > 0
    assert dash_summary["production"]["total_packets_produced"] >= 238
    assert dash_summary["finance"]["total_collections_paise"] >= 400000
    assert dash_summary["top_products"][0]["product_name"] == murukku.product_name
