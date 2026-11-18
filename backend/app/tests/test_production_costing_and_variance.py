import pytest
from decimal import Decimal
from backend.app.models.supplier import Supplier
from backend.app.models.product import Product, ProductCategory
from backend.app.models.raw_material import RawMaterial, RawMaterialCategory
from backend.app.models.packaging import PackagingItem, PackagingCategory
from backend.app.models.bom import BOM, BOMItem, BOMStatus


def get_auth_header(client, username, password="demo123"):
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_full_benchmark_production_run_lifecycle(client, db, seeded_users):
    """
    NIT Trichy Internship Evaluation - Complete Benchmark Integration Test:
    1. Preconditions:
       - Opening stocks: Flour 100kg @ ₹42, Oil 30L @ ₹140, Spice 5kg @ ₹200,
         Pouches 500pcs @ ₹2.50, Cartons 30pcs @ ₹15, Murukku 50 pkts @ ₹35
       - Purchase: Flour 60kg @ ₹45/kg => Flour balance = 160kg, Weighted Avg = ₹43.125/kg
       - BOM: Murukku 200g (Yield: 200 pkts, Tol: 3%)
    2. Execute 1 Batch:
       - Actual Flour: 40 kg (planned 40 kg, variance 0%)
       - Actual Oil: 10.5 L (planned 10 L, variance +5%, WARNING alert)
       - Actual Spice: 1.2 kg (planned 1.2 kg, variance 0%)
       - Actual Pouches: 194 pcs (188 good + 6 damaged)
       - Actual Cartons: 9 pcs (planned 10 pcs)
       - Actual Good Output: 188 pkts (expected 200 pkts, variance -6%, WARNING alert)
       - Damaged Pouches: 6 pcs
       - Overheads: Labour ₹1,200, Gas/Power ₹600
    3. Assertions:
       - Post-production stock:
         Flour = 120 kg, Oil = 19.5 L, Spice = 3.8 kg, Pouches = 306, Cartons = 21, FG = 238 pkts
       - Costing:
         Total cost = ₹5,855.00, Cost per packet ≈ ₹31.14
    """
    admin_hdr = get_auth_header(client, "admin")
    prod_hdr = get_auth_header(client, "prod")

    # Step 1: Create Master Data
    murukku = Product(
        sku="BENCH-MUR-200",
        product_name="Murukku 200 g Benchmark",
        category=ProductCategory.MURUKKU,
        base_unit="packet",
        pack_size=Decimal("200.00"),
        pack_size_unit="g",
        hsn_code="1905",
        gst_rate=Decimal("0.0500"),
        selling_price_paise=5000,  # ₹50.00
        reorder_level=Decimal("50.0000"),
        packets_per_carton=20,
        is_active=True,
    )
    flour = RawMaterial(
        material_code="BENCH-RM-FLOUR",
        material_name="Rice & Urad Flour",
        category=RawMaterialCategory.FLOUR,
        base_unit="kg",
        reorder_level=Decimal("30.0000"),
        is_active=True,
    )
    oil = RawMaterial(
        material_code="BENCH-RM-OIL",
        material_name="Refined Cooking Oil",
        category=RawMaterialCategory.OIL,
        base_unit="litre",
        reorder_level=Decimal("10.0000"),
        is_active=True,
    )
    spice = RawMaterial(
        material_code="BENCH-RM-SPICE",
        material_name="Salt & Spice Mix",
        category=RawMaterialCategory.SPICE,
        base_unit="kg",
        reorder_level=Decimal("2.0000"),
        is_active=True,
    )
    pouch = PackagingItem(
        packaging_code="BENCH-PKG-POUCH",
        packaging_name="200 g Printed Pouch",
        category=PackagingCategory.POUCH,
        base_unit="piece",
        reorder_level=Decimal("100.0000"),
        is_active=True,
    )
    carton = PackagingItem(
        packaging_code="BENCH-PKG-CARTON",
        packaging_name="Outer Master Carton",
        category=PackagingCategory.CARTON,
        base_unit="piece",
        reorder_level=Decimal("15.0000"),
        is_active=True,
    )
    supplier = Supplier(
        supplier_code="BENCH-SUP-01",
        supplier_name="National Agro Commodities",
        phone="9876543210",
        gstin="33AAAAA9999A1Z9",
        address="Trichy Agro Market",
        city="Tiruchirappalli",
        state="Tamil Nadu",
        state_code="33",
        pincode="620001",
        is_active=True,
    )
    db.add_all([murukku, flour, oil, spice, pouch, carton, supplier])
    db.commit()

    # Step 2: Initialize Opening Stocks
    stocks = [
        ("RAW", flour.id, "100.0000", 4200),     # 100 kg @ ₹42/kg
        ("RAW", oil.id, "30.0000", 14000),       # 30 L @ ₹140/L
        ("RAW", spice.id, "5.0000", 20000),      # 5 kg @ ₹200/kg
        ("PACKAGING", pouch.id, "500.0000", 250),# 500 pcs @ ₹2.50/pc
        ("PACKAGING", carton.id, "30.0000", 1500),# 30 pcs @ ₹15/pc
        ("FG", murukku.id, "50.0000", 3500),     # 50 pkts @ ₹35/pkt
    ]
    for itype, iid, qty, cost in stocks:
        op_res = client.post("/inventory/opening-stock", json={
            "item_type": itype, "item_id": iid, "quantity": qty, "unit_cost_paise": cost
        }, headers=admin_hdr)
        assert op_res.status_code == 201

    # Step 3: Purchase Flour 60 kg @ ₹45.00/kg
    po_res = client.post(
        "/purchases",
        json={
            "supplier_id": supplier.id,
            "supplier_invoice_number": "INV-BENCH-PURCHASE-01",
            "lines": [
                {
                    "item_type": "RAW",
                    "item_id": flour.id,
                    "quantity": "60.0000",
                    "unit": "kg",
                    "unit_rate_paise": 4500,
                    "tax_rate": "0.0500",
                }
            ],
        },
        headers=prod_hdr,
    )
    assert po_res.status_code == 201
    po_id = po_res.json()["id"]

    # Post purchase
    post_po = client.post(f"/purchases/{po_id}/post", headers=prod_hdr)
    assert post_po.status_code == 200

    # Verify Flour balance and moving weighted average: 160 kg @ ₹43.125/kg (₹6,900.00)
    flour_val = client.get(f"/stock/valuation/RAW/{flour.id}", headers=admin_hdr).json()
    assert Decimal(str(flour_val["quantity"])) == Decimal("160.0000")
    assert flour_val["total_value_paise"] == 690000
    assert flour_val["weighted_avg_rate_paise"] in (4312, 4313)

    # Step 4: Create Benchmark Active BOM
    bom_res = client.post(
        "/boms",
        json={
            "product_id": murukku.id,
            "batch_yield_packets": "200.0000",
            "tolerance_pct": "3.00",
            "description": "Benchmark BOM for Murukku 200g",
            "items": [
                {"item_type": "RAW", "item_id": flour.id, "quantity_per_batch": "40.0000", "unit": "kg"},
                {"item_type": "RAW", "item_id": oil.id, "quantity_per_batch": "10.0000", "unit": "litre"},
                {"item_type": "RAW", "item_id": spice.id, "quantity_per_batch": "1.2000", "unit": "kg"},
                {"item_type": "PACKAGING", "item_id": pouch.id, "quantity_per_batch": "200.0000", "unit": "piece"},
                {"item_type": "PACKAGING", "item_id": carton.id, "quantity_per_batch": "10.0000", "unit": "piece"},
            ],
        },
        headers=prod_hdr,
    )
    assert bom_res.status_code == 201
    bom_id = bom_res.json()["id"]
    client.post(f"/boms/{bom_id}/activate", headers=admin_hdr)

    # Step 5: Execute 1 Batch Production Run with Actuals
    run_payload = {
        "product_id": murukku.id,
        "bom_id": bom_id,
        "batch_number": "BATCH-2026-NIT-01",
        "number_of_batches": "1.00",
        "actual_good_output": "188.0000",
        "damaged_packaging": "6.0000",
        "notes": "NIT Trichy Benchmark Production Run",
        "materials": [
            {"item_type": "RAW", "item_id": flour.id, "issued_quantity": "40.0000", "unit": "kg"},
            {"item_type": "RAW", "item_id": oil.id, "issued_quantity": "10.5000", "unit": "litre"},
            {"item_type": "RAW", "item_id": spice.id, "issued_quantity": "1.2000", "unit": "kg"},
            {"item_type": "PACKAGING", "item_id": pouch.id, "issued_quantity": "194.0000", "unit": "piece"},
            {"item_type": "PACKAGING", "item_id": carton.id, "issued_quantity": "9.0000", "unit": "piece"},
        ],
        "overheads": [
            {"expense_type": "LABOUR", "amount_paise": 120000, "description": "Factory labour charge"},
            {"expense_type": "GAS", "amount_paise": 60000, "description": "LPG fuel / power"},
        ],
    }
    create_run_res = client.post("/production-runs", json=run_payload, headers=prod_hdr)
    assert create_run_res.status_code == 201
    run_id = create_run_res.json()["id"]

    # Step 6: Verify Variance Analysis Pre-Posting
    var_res = client.get(f"/production-runs/{run_id}/variance", headers=prod_hdr)
    assert var_res.status_code == 200
    var_data = var_res.json()

    # Yield variance must be -6.00% (alert WARNING)
    assert Decimal(str(var_data["yield_variance_pct"])) == Decimal("-6.00")
    assert var_data["yield_status"] == "WARNING"

    # Oil variance must be +5.00% (alert WARNING)
    oil_var = next(it for it in var_data["material_variances"] if it["item_id"] == oil.id)
    assert Decimal(str(oil_var["variance_pct"])) == Decimal("5.00")
    assert oil_var["status"] == "WARNING"

    # Flour and spice must be 0% (OK)
    flour_var = next(it for it in var_data["material_variances"] if it["item_id"] == flour.id)
    assert Decimal(str(flour_var["variance_pct"])) == Decimal("0.00")
    assert flour_var["status"] == "OK"

    # Step 7: Verify Costing Pre-Posting
    cost_res = client.get(f"/production-runs/{run_id}/costing", headers=prod_hdr)
    assert cost_res.status_code == 200
    cost_data = cost_res.json()

    # Material & Packaging cost = ₹4,055.00 (405,500 paise)
    assert cost_data["total_material_cost_paise"] == 405500
    # Overheads = ₹1,800.00 (180,000 paise)
    assert cost_data["total_overheads_paise"] == 180000
    # Total production cost = ₹5,855.00 (585,500 paise)
    assert cost_data["total_production_cost_paise"] == 585500
    # Cost per packet = 585500 / 188 ≈ ₹31.14 (3114 paise)
    assert cost_data["cost_per_packet_paise"] == 3114
    assert Decimal(str(cost_data["cost_per_packet_decimal"])) == Decimal("31.1436")
    # Gross margin = 5000 - 3114 = 1886 paise (₹18.86)
    assert cost_data["gross_margin_paise"] == 1886

    # Step 8: Post Production Run Atomically
    post_run_res = client.post(f"/production-runs/{run_id}/post", headers=prod_hdr)
    assert post_run_res.status_code == 200
    posted_data = post_run_res.json()
    assert posted_data["status"] == "POSTED"
    assert posted_data["total_production_cost_paise"] == 585500

    # Step 9: EXACT BENCHMARK STOCK ASSERTIONS IN INVENTORY LEDGER
    # Flour = 120 kg
    flour_bal = client.get(f"/stock/summary/RAW/{flour.id}", headers=admin_hdr).json()
    assert Decimal(str(flour_bal["current_stock"])) == Decimal("120.0000")

    # Oil = 19.5 L
    oil_bal = client.get(f"/stock/summary/RAW/{oil.id}", headers=admin_hdr).json()
    assert Decimal(str(oil_bal["current_stock"])) == Decimal("19.5000")

    # Spice = 3.8 kg
    spice_bal = client.get(f"/stock/summary/RAW/{spice.id}", headers=admin_hdr).json()
    assert Decimal(str(spice_bal["current_stock"])) == Decimal("3.8000")

    # Pouches = 306 pcs
    pouch_bal = client.get(f"/stock/summary/PACKAGING/{pouch.id}", headers=admin_hdr).json()
    assert Decimal(str(pouch_bal["current_stock"])) == Decimal("306.0000")

    # Cartons = 21 pcs
    carton_bal = client.get(f"/stock/summary/PACKAGING/{carton.id}", headers=admin_hdr).json()
    assert Decimal(str(carton_bal["current_stock"])) == Decimal("21.0000")

    # Finished Murukku 200 g = 238 packets (50 opening + 188 output)
    murukku_bal = client.get(f"/stock/summary/FG/{murukku.id}", headers=admin_hdr).json()
    assert Decimal(str(murukku_bal["current_stock"])) == Decimal("238.0000")
