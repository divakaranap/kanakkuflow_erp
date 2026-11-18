import pytest
from decimal import Decimal
from backend.app.models.product import Product, ProductCategory
from backend.app.models.raw_material import RawMaterial, RawMaterialCategory
from backend.app.models.packaging import PackagingItem, PackagingCategory


def get_auth_header(client, username, password="demo123"):
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def bom_setup(db):
    product = Product(
        sku="PRD-BOM-MURUKKU",
        product_name="Murukku Pack 200g",
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
    flour = RawMaterial(
        material_code="RM-FLOUR-BOM",
        material_name="Rice & Urad Flour",
        category=RawMaterialCategory.FLOUR,
        base_unit="kg",
        reorder_level=Decimal("10.0000"),
        is_active=True,
    )
    oil = RawMaterial(
        material_code="RM-OIL-BOM",
        material_name="Cooking Oil",
        category=RawMaterialCategory.OIL,
        base_unit="litre",
        reorder_level=Decimal("10.0000"),
        is_active=True,
    )
    pouch = PackagingItem(
        packaging_code="PKG-POUCH-BOM",
        packaging_name="Printed Pouch 200g",
        category=PackagingCategory.POUCH,
        base_unit="piece",
        reorder_level=Decimal("50.0000"),
        is_active=True,
    )
    db.add_all([product, flour, oil, pouch])
    db.commit()
    db.refresh(product)
    db.refresh(flour)
    db.refresh(oil)
    db.refresh(pouch)
    return {"product": product, "flour": flour, "oil": oil, "pouch": pouch}


def test_bom_crud_and_versioning(client, seeded_users, bom_setup):
    admin_hdr = get_auth_header(client, "admin")
    prod_hdr = get_auth_header(client, "prod")
    product = bom_setup["product"]
    flour = bom_setup["flour"]
    oil = bom_setup["oil"]
    pouch = bom_setup["pouch"]

    # 1. Create first BOM version (V1)
    bom_payload1 = {
        "product_id": product.id,
        "batch_yield_packets": "200.0000",
        "tolerance_pct": "3.00",
        "description": "Standard Recipe V1",
        "items": [
            {"item_type": "RAW", "item_id": flour.id, "quantity_per_batch": "40.0000", "unit": "kg"},
            {"item_type": "RAW", "item_id": oil.id, "quantity_per_batch": "10.0000", "unit": "litre"},
            {"item_type": "PACKAGING", "item_id": pouch.id, "quantity_per_batch": "200.0000", "unit": "piece"},
        ],
    }
    res1 = client.post("/boms", json=bom_payload1, headers=prod_hdr)
    assert res1.status_code == 201
    bom1 = res1.json()
    assert bom1["version"] == 1
    assert bom1["status"] == "DRAFT"
    bom1_id = bom1["id"]

    # 2. Activate BOM V1
    act_res = client.post(f"/boms/{bom1_id}/activate", headers=admin_hdr)
    assert act_res.status_code == 200
    assert act_res.json()["status"] == "ACTIVE"

    # 3. Create second BOM version (V2) with modified oil quantity
    bom_payload2 = {
        "product_id": product.id,
        "batch_yield_packets": "200.0000",
        "tolerance_pct": "3.00",
        "description": "Improved Crispy Recipe V2",
        "items": [
            {"item_type": "RAW", "item_id": flour.id, "quantity_per_batch": "40.0000", "unit": "kg"},
            {"item_type": "RAW", "item_id": oil.id, "quantity_per_batch": "11.0000", "unit": "litre"},
            {"item_type": "PACKAGING", "item_id": pouch.id, "quantity_per_batch": "200.0000", "unit": "piece"},
        ],
    }
    res2 = client.post("/boms", json=bom_payload2, headers=prod_hdr)
    assert res2.status_code == 201
    bom2 = res2.json()
    assert bom2["version"] == 2
    bom2_id = bom2["id"]

    # 4. Activate V2: verify V1 becomes ARCHIVED and V2 becomes ACTIVE
    client.post(f"/boms/{bom2_id}/activate", headers=admin_hdr)
    active_res = client.get(f"/boms/active/{product.id}", headers=prod_hdr)
    assert active_res.status_code == 200
    active_bom = active_res.json()
    assert active_bom["id"] == bom2_id
    assert active_bom["version"] == 2

    old_v1 = client.get(f"/boms/{bom1_id}", headers=prod_hdr).json()
    assert old_v1["status"] == "ARCHIVED"


def test_bom_scaling(client, seeded_users, bom_setup):
    prod_hdr = get_auth_header(client, "prod")
    product = bom_setup["product"]
    flour = bom_setup["flour"]
    pouch = bom_setup["pouch"]

    res = client.post(
        "/boms",
        json={
            "product_id": product.id,
            "batch_yield_packets": "200.0000",
            "tolerance_pct": "3.00",
            "items": [
                {"item_type": "RAW", "item_id": flour.id, "quantity_per_batch": "40.0000", "unit": "kg"},
                {"item_type": "PACKAGING", "item_id": pouch.id, "quantity_per_batch": "200.0000", "unit": "piece"},
            ],
        },
        headers=prod_hdr,
    )
    bom_id = res.json()["id"]

    # Scale for 2 batches
    scale_res = client.get(f"/boms/{bom_id}/scale?batches=2", headers=prod_hdr)
    assert scale_res.status_code == 200
    scaled = scale_res.json()
    assert Decimal(str(scaled["expected_output_packets"])) == Decimal("400.0000")

    flour_planned = next(it for it in scaled["items"] if it["item_id"] == flour.id)
    assert Decimal(str(flour_planned["planned_quantity"])) == Decimal("80.0000")
