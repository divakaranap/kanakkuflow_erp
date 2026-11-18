import pytest
from decimal import Decimal
from backend.app.models.product import Product, ProductCategory
from backend.app.models.raw_material import RawMaterial, RawMaterialCategory
from backend.app.models.packaging import PackagingItem, PackagingCategory
from backend.app.models.bom import BOM, BOMItem, BOMStatus
from backend.app.models.inventory import InventoryItemType, StockMovement, MovementType


def get_auth_header(client, username, password="demo123"):
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def production_setup(db, client, seeded_users):
    admin_hdr = get_auth_header(client, "admin")

    # 1. Master product
    prod = Product(
        sku="PRD-PROD-TEST",
        product_name="Murukku Production Item",
        category=ProductCategory.MURUKKU,
        base_unit="packet",
        pack_size=Decimal("200.00"),
        pack_size_unit="g",
        hsn_code="1905",
        gst_rate=Decimal("0.0500"),
        selling_price_paise=5000,
        reorder_level=Decimal("20.0000"),
        is_active=True,
    )
    flour = RawMaterial(
        material_code="RM-FLOUR-PTEST",
        material_name="Rice Flour Test",
        category=RawMaterialCategory.FLOUR,
        base_unit="kg",
        reorder_level=Decimal("10.0000"),
        is_active=True,
    )
    pouch = PackagingItem(
        packaging_code="PKG-POUCH-PTEST",
        packaging_name="Pouch Test",
        category=PackagingCategory.POUCH,
        base_unit="piece",
        reorder_level=Decimal("50.0000"),
        is_active=True,
    )
    db.add_all([prod, flour, pouch])
    db.commit()
    db.refresh(prod)
    db.refresh(flour)
    db.refresh(pouch)

    # 2. BOM
    bom = BOM(
        bom_code="BOM-PROD-TEST-V1",
        product_id=prod.id,
        version=1,
        batch_yield_packets=Decimal("200.0000"),
        tolerance_pct=Decimal("3.00"),
        status=BOMStatus.ACTIVE,
        created_by=seeded_users["admin"].id,
        items=[
            BOMItem(item_type=InventoryItemType.RAW, item_id=flour.id, quantity_per_batch=Decimal("40.0000"), unit="kg"),
            BOMItem(item_type=InventoryItemType.PACKAGING, item_id=pouch.id, quantity_per_batch=Decimal("200.0000"), unit="piece"),
        ],
    )
    db.add(bom)
    db.commit()
    db.refresh(bom)

    return {"prod": prod, "flour": flour, "pouch": pouch, "bom": bom}


def test_production_insufficient_stock_rejection(client, seeded_users, production_setup):
    prod_hdr = get_auth_header(client, "prod")
    prod = production_setup["prod"]
    flour = production_setup["flour"]
    pouch = production_setup["pouch"]

    # No opening stock initialized for flour/pouch yet
    # Creating a draft run
    run_res = client.post(
        "/production-runs",
        json={
            "product_id": prod.id,
            "batch_number": "BATCH-001",
            "number_of_batches": "1.00",
            "actual_good_output": "190.0000",
            "materials": [
                {"item_type": "RAW", "item_id": flour.id, "issued_quantity": "40.0000", "unit": "kg"},
                {"item_type": "PACKAGING", "item_id": pouch.id, "issued_quantity": "200.0000", "unit": "piece"},
            ],
        },
        headers=prod_hdr,
    )
    assert run_res.status_code == 201
    run_id = run_res.json()["id"]

    # Attempting to post when stock is 0 must fail with HTTP 400 Insufficient Inventory
    post_res = client.post(f"/production-runs/{run_id}/post", headers=prod_hdr)
    assert post_res.status_code == 400
    assert "Insufficient inventory" in post_res.json()["detail"]


def test_production_run_posting_and_stock_updates(client, db, seeded_users, production_setup):
    admin_hdr = get_auth_header(client, "admin")
    prod_hdr = get_auth_header(client, "prod")
    prod = production_setup["prod"]
    flour = production_setup["flour"]
    pouch = production_setup["pouch"]

    # 1. Initialize opening stocks
    client.post("/inventory/opening-stock", json={
        "item_type": "RAW", "item_id": flour.id, "quantity": "100.0000", "unit_cost_paise": 4200
    }, headers=admin_hdr)
    client.post("/inventory/opening-stock", json={
        "item_type": "PACKAGING", "item_id": pouch.id, "quantity": "500.0000", "unit_cost_paise": 250
    }, headers=admin_hdr)

    # 2. Create production run
    run_res = client.post(
        "/production-runs",
        json={
            "product_id": prod.id,
            "batch_number": "BATCH-PROD-OK",
            "number_of_batches": "1.00",
            "actual_good_output": "188.0000",
            "damaged_packaging": "6.0000",
            "materials": [
                {"item_type": "RAW", "item_id": flour.id, "issued_quantity": "40.0000", "unit": "kg"},
                {"item_type": "PACKAGING", "item_id": pouch.id, "issued_quantity": "194.0000", "unit": "piece"},
            ],
            "overheads": [
                {"expense_type": "LABOUR", "amount_paise": 120000, "description": "Factory labour"},
            ],
        },
        headers=prod_hdr,
    )
    assert run_res.status_code == 201
    run_id = run_res.json()["id"]

    # 3. Post production run
    post_res = client.post(f"/production-runs/{run_id}/post", headers=prod_hdr)
    assert post_res.status_code == 200
    posted_run = post_res.json()
    assert posted_run["status"] == "POSTED"

    # 4. Verify Raw Material stock reduced: 100 - 40 = 60 kg
    flour_summary = client.get(f"/stock/summary/RAW/{flour.id}", headers=prod_hdr).json()
    assert Decimal(str(flour_summary["current_stock"])) == Decimal("60.0000")

    # 5. Verify Packaging stock reduced: 500 - 194 = 306 pcs
    pouch_summary = client.get(f"/stock/summary/PACKAGING/{pouch.id}", headers=prod_hdr).json()
    assert Decimal(str(pouch_summary["current_stock"])) == Decimal("306.0000")

    # 6. Verify Finished Goods stock increased: 0 + 188 = 188 packets
    fg_summary = client.get(f"/stock/summary/FG/{prod.id}", headers=prod_hdr).json()
    assert Decimal(str(fg_summary["current_stock"])) == Decimal("188.0000")

    # 7. Verify scrap movement specifically created for the 6 damaged pouches
    scrap_movements = db.query(StockMovement).filter(
        StockMovement.movement_type == MovementType.PRODUCTION_SCRAP,
        StockMovement.source_id == run_id,
    ).all()
    assert len(scrap_movements) == 1
    assert Decimal(str(scrap_movements[0].qty_delta)) == Decimal("-6.0000")

    # 8. Prevent duplicate posting
    repost = client.post(f"/production-runs/{run_id}/post", headers=prod_hdr)
    assert repost.status_code == 400
