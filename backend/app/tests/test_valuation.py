import pytest
from decimal import Decimal
from backend.app.models.supplier import Supplier
from backend.app.models.raw_material import RawMaterial, RawMaterialCategory


def get_auth_header(client, username, password="demo123"):
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_benchmark_moving_weighted_average_valuation(client, db, seeded_users):
    """
    Benchmark Verification Test:
    1. Opening stock: 100 kg Flour @ ₹42.00/kg = 420,000 paise
    2. Purchase receipt: 60 kg Flour @ ₹45.00/kg = 270,000 paise
    3. Total stock: 160 kg
    4. Total valuation: 690,000 paise = ₹6,900.00
    5. Moving weighted average cost per unit:
       690,000 / 160 = 4,312.50 paise = ₹43.125/kg (rounds to 4313 paise / ₹43.13)
    """
    admin_hdr = get_auth_header(client, "admin")
    prod_hdr = get_auth_header(client, "prod")

    # Setup master items
    flour = RawMaterial(
        material_code="RM-FLOUR-BENCHMARK",
        material_name="Rice & Urad Flour Mix",
        category=RawMaterialCategory.FLOUR,
        base_unit="kg",
        reorder_level=Decimal("30.0000"),
        is_active=True,
    )
    supplier = Supplier(
        supplier_code="SUP-FLOUR-01",
        supplier_name="Sri Andal Flour Mill",
        phone="9840112233",
        gstin="33AAAAA5555A1Z1",
        address="Mills Road",
        city="Madurai",
        state="Tamil Nadu",
        state_code="33",
        pincode="625001",
        is_active=True,
    )
    db.add_all([flour, supplier])
    db.commit()
    db.refresh(flour)
    db.refresh(supplier)

    # Step 1: Initialize Opening Stock (100 kg @ ₹42/kg)
    op_res = client.post(
        "/inventory/opening-stock",
        json={
            "item_type": "RAW",
            "item_id": flour.id,
            "quantity": "100.0000",
            "unit_cost_paise": 4200,
            "notes": "Benchmark opening flour",
        },
        headers=admin_hdr,
    )
    assert op_res.status_code == 201

    # Check initial valuation
    val_res1 = client.get(f"/stock/valuation/RAW/{flour.id}", headers=admin_hdr)
    assert val_res1.status_code == 200
    val_data1 = val_res1.json()
    assert Decimal(str(val_data1["quantity"])) == Decimal("100.0000")
    assert val_data1["total_value_paise"] == 420000
    assert val_data1["weighted_avg_rate_paise"] == 4200

    # Step 2: Purchase 60 kg @ ₹45/kg
    po_res = client.post(
        "/purchases",
        json={
            "supplier_id": supplier.id,
            "supplier_invoice_number": "INV-BENCH-001",
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
    post_res = client.post(f"/purchases/{po_id}/post", headers=prod_hdr)
    assert post_res.status_code == 200

    # Step 3 & 4 & 5: Check Post-Purchase Balance and Weighted Average Valuation
    val_res2 = client.get(f"/stock/valuation/RAW/{flour.id}", headers=admin_hdr)
    assert val_res2.status_code == 200
    val_data2 = val_res2.json()

    # Total quantity must equal 160 kg
    assert Decimal(str(val_data2["quantity"])) == Decimal("160.0000")

    # Total valuation must equal 690,000 paise (420,000 + 270,000)
    assert val_data2["total_value_paise"] == 690000

    # Moving weighted average rate must be 4312.5 rounded to 4313 paise
    assert val_data2["weighted_avg_rate_paise"] in (4312, 4313)
