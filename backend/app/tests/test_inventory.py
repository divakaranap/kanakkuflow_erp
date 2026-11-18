import pytest
from decimal import Decimal
from backend.app.models.raw_material import RawMaterial, RawMaterialCategory
from backend.app.models.packaging import PackagingItem, PackagingCategory
from backend.app.models.product import Product, ProductCategory


def get_auth_header(client, username, password="demo123"):
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_items(db):
    """Seed one raw material, one packaging item, and one product."""
    rm = RawMaterial(
        material_code="RM-TEST-FLOUR",
        material_name="Test Rice Flour",
        category=RawMaterialCategory.FLOUR,
        base_unit="kg",
        reorder_level=Decimal("40.0000"),
        is_active=True,
    )
    pkg = PackagingItem(
        packaging_code="PKG-TEST-POUCH",
        packaging_name="Test 200g Pouch",
        category=PackagingCategory.POUCH,
        base_unit="piece",
        reorder_level=Decimal("100.0000"),
        is_active=True,
    )
    prod = Product(
        sku="PRD-TEST-MURUKKU",
        product_name="Test Murukku 200g",
        category=ProductCategory.MURUKKU,
        base_unit="packet",
        pack_size=Decimal("200.00"),
        pack_size_unit="g",
        hsn_code="1905",
        gst_rate=Decimal("0.0500"),
        selling_price_paise=5000,
        reorder_level=Decimal("20.0000"),
        packets_per_carton=20,
        is_active=True,
    )
    db.add_all([rm, pkg, prod])
    db.commit()
    db.refresh(rm)
    db.refresh(pkg)
    db.refresh(prod)
    return {"rm": rm, "pkg": pkg, "prod": prod}


def test_opening_stock_initialization(client, seeded_users, sample_items):
    admin_hdr = get_auth_header(client, "admin")
    rm = sample_items["rm"]

    # 1. Initialize opening stock: 100 kg @ ₹42/kg
    payload = {
        "item_type": "RAW",
        "item_id": rm.id,
        "quantity": "100.0000",
        "unit_cost_paise": 4200,
        "notes": "Opening stock flour",
    }
    res = client.post("/inventory/opening-stock", json=payload, headers=admin_hdr)
    assert res.status_code == 201
    data = res.json()
    assert data["movement_type"] == "OPENING"
    assert Decimal(str(data["qty_delta"])) == Decimal("100.0000")
    assert data["unit_cost_paise"] == 4200
    assert data["total_value_paise"] == 420000

    # 2. Prevent duplicate opening stock initialization
    dup_res = client.post("/inventory/opening-stock", json=payload, headers=admin_hdr)
    assert dup_res.status_code == 400
    assert "already been initialized" in dup_res.json()["detail"]

    # 3. Prevent non-admin/owner initialization (salesA)
    sales_hdr = get_auth_header(client, "salesA")
    unauth_res = client.post("/inventory/opening-stock", json=payload, headers=sales_hdr)
    assert unauth_res.status_code == 403


def test_stock_summary_and_low_stock(client, seeded_users, sample_items):
    admin_hdr = get_auth_header(client, "admin")
    rm = sample_items["rm"]

    # Initialize below reorder level (30 kg <= 40 kg reorder level)
    payload = {
        "item_type": "RAW",
        "item_id": rm.id,
        "quantity": "30.0000",
        "unit_cost_paise": 4200,
    }
    client.post("/inventory/opening-stock", json=payload, headers=admin_hdr)

    # Fetch summary
    res = client.get("/stock/summary", headers=admin_hdr)
    assert res.status_code == 200
    items = res.json()
    flour_item = next(it for it in items if it["item_id"] == rm.id)
    assert Decimal(str(flour_item["current_stock"])) == Decimal("30.0000")
    assert flour_item["is_low_stock"] is True

    # Low stock filter
    low_res = client.get("/stock/summary?low_stock_only=true", headers=admin_hdr)
    assert low_res.status_code == 200
    assert any(it["item_id"] == rm.id for it in low_res.json())


def test_inventory_adjustments_workflow(client, seeded_users, sample_items):
    prod_hdr = get_auth_header(client, "prod")
    admin_hdr = get_auth_header(client, "admin")
    auditor_hdr = get_auth_header(client, "auditor")
    pkg = sample_items["pkg"]

    # 1. Initialize opening stock: 500 pcs @ ₹2.50
    client.post("/inventory/opening-stock", json={
        "item_type": "PACKAGING",
        "item_id": pkg.id,
        "quantity": "500.0000",
        "unit_cost_paise": 250,
    }, headers=admin_hdr)

    # 2. Production user creates an adjustment (DECREASE 15 pcs due to damage)
    adj_payload = {
        "item_type": "PACKAGING",
        "item_id": pkg.id,
        "adjustment_type": "DECREASE",
        "quantity": "15.0000",
        "reason": "Water damage in store shelf B",
    }
    adj_res = client.post("/inventory/adjustments", json=adj_payload, headers=prod_hdr)
    assert adj_res.status_code == 201
    adj_data = adj_res.json()
    assert adj_data["status"] == "DRAFT"
    adj_id = adj_data["id"]

    # 3. Auditor cannot post adjustment (403)
    aud_res = client.post(f"/inventory/adjustments/{adj_id}/post", headers=auditor_hdr)
    assert aud_res.status_code == 403

    # 4. Admin posts adjustment
    post_res = client.post(f"/inventory/adjustments/{adj_id}/post", headers=admin_hdr)
    assert post_res.status_code == 200
    assert post_res.json()["status"] == "POSTED"

    # 5. Check balance reduced: 500 - 15 = 485
    summary_res = client.get(f"/stock/summary/PACKAGING/{pkg.id}", headers=admin_hdr)
    assert summary_res.status_code == 200
    assert Decimal(str(summary_res.json()["current_stock"])) == Decimal("485.0000")
