import pytest
from decimal import Decimal
from backend.app.models.supplier import Supplier
from backend.app.models.raw_material import RawMaterial, RawMaterialCategory


def get_auth_header(client, username, password="demo123"):
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def purchase_setup(db):
    supplier = Supplier(
        supplier_code="SUP-TEST-01",
        supplier_name="Trichy Agro Commodities",
        phone="9876543210",
        gstin="33AAAAA1234A1Z5",
        address="12 Main Road",
        city="Tiruchirappalli",
        state="Tamil Nadu",
        state_code="33",
        pincode="620001",
        is_active=True,
    )
    rm = RawMaterial(
        material_code="RM-FLOUR-TEST",
        material_name="Rice Flour Raw",
        category=RawMaterialCategory.FLOUR,
        base_unit="kg",
        reorder_level=Decimal("20.0000"),
        is_active=True,
    )
    db.add_all([supplier, rm])
    db.commit()
    db.refresh(supplier)
    db.refresh(rm)
    return {"supplier": supplier, "rm": rm}


def test_purchase_lifecycle(client, seeded_users, purchase_setup):
    prod_hdr = get_auth_header(client, "prod")
    sales_hdr = get_auth_header(client, "salesA")
    supplier = purchase_setup["supplier"]
    rm = purchase_setup["rm"]

    # 1. Salesman cannot create purchase (403)
    p_payload = {
        "supplier_id": supplier.id,
        "supplier_invoice_number": "INV-2026-999",
        "lines": [
            {
                "item_type": "RAW",
                "item_id": rm.id,
                "quantity": "60.0000",
                "unit": "kg",
                "unit_rate_paise": 4500,  # ₹45/kg
                "tax_rate": "0.0500",     # 5% GST
            }
        ],
    }
    unauth_res = client.post("/purchases", json=p_payload, headers=sales_hdr)
    assert unauth_res.status_code == 403

    # 2. Production user creates draft purchase
    res = client.post("/purchases", json=p_payload, headers=prod_hdr)
    assert res.status_code == 201
    p_data = res.json()
    assert p_data["status"] == "DRAFT"
    # Taxable = 60 * 4500 = 270,000 paise
    assert p_data["subtotal_paise"] == 270000
    # Tax = 5% of 270,000 = 13,500 paise
    assert p_data["tax_paise"] == 13500
    # Total = 283,500 paise
    assert p_data["total_paise"] == 283500
    p_id = p_data["id"]

    # 3. Post purchase
    post_res = client.post(f"/purchases/{p_id}/post", headers=prod_hdr)
    assert post_res.status_code == 200
    assert post_res.json()["status"] == "POSTED"

    # 4. Verify inventory ledger stock movement created
    ledger_res = client.get(f"/stock/ledger?item_id={rm.id}", headers=prod_hdr)
    assert ledger_res.status_code == 200
    items = ledger_res.json()["items"]
    assert len(items) == 1
    m = items[0]
    assert m["movement_type"] == "PURCHASE_RECEIPT"
    assert Decimal(str(m["qty_delta"])) == Decimal("60.0000")
    assert m["unit_cost_paise"] == 4500
    assert m["total_value_paise"] == 270000

    # 5. Prevent posting already posted purchase
    repost_res = client.post(f"/purchases/{p_id}/post", headers=prod_hdr)
    assert repost_res.status_code == 400
