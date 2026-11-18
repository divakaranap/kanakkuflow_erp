import pytest
from decimal import Decimal
from backend.app.models.raw_material import RawMaterial, RawMaterialCategory
from backend.app.models.inventory import InventoryBalance, InventoryItemType


def get_auth_header(client, username, password="demo123"):
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_stock_reconciliation_flow(client, db, seeded_users):
    admin_hdr = get_auth_header(client, "admin")

    # Create raw material
    rm = RawMaterial(
        material_code="RM-RECON-OIL",
        material_name="Cooking Oil Recon",
        category=RawMaterialCategory.OIL,
        base_unit="litre",
        reorder_level=Decimal("10.0000"),
        is_active=True,
    )
    db.add(rm)
    db.commit()
    db.refresh(rm)

    # Initialize opening stock: 30 L
    op_res = client.post(
        "/inventory/opening-stock",
        json={
            "item_type": "RAW",
            "item_id": rm.id,
            "quantity": "30.0000",
            "unit_cost_paise": 14000,
        },
        headers=admin_hdr,
    )
    assert op_res.status_code == 201

    # 1. Reconciliation should report MATCHED
    recon_res = client.get("/stock/reconciliation", headers=admin_hdr)
    assert recon_res.status_code == 200
    report = recon_res.json()
    oil_item = next(it for it in report["items"] if it["item_id"] == rm.id)
    assert oil_item["status"] == "MATCHED"
    assert Decimal(str(oil_item["ledger_qty"])) == Decimal("30.0000")
    assert Decimal(str(oil_item["cached_qty"])) == Decimal("30.0000")
    assert Decimal(str(oil_item["difference"])) == Decimal("0.0000")

    # 2. Artificially tamper cached balance to test mismatch detection
    bal_row = db.query(InventoryBalance).filter(
        InventoryBalance.item_type == InventoryItemType.RAW,
        InventoryBalance.item_id == rm.id,
    ).first()
    bal_row.cached_qty = Decimal("25.0000")  # Drifts from ledger 30.0000
    db.commit()

    # 3. Running reconciliation should detect MISMATCH and fix the cache
    run_res = client.post("/stock/reconciliation/run", headers=admin_hdr)
    assert run_res.status_code == 200
    new_report = run_res.json()
    tampered_item = next(it for it in new_report["items"] if it["item_id"] == rm.id)
    assert tampered_item["status"] == "MISMATCH"
    assert Decimal(str(tampered_item["difference"])) == Decimal("5.0000")

    # 4. Verify cache was restored to ledger truth
    db.refresh(bal_row)
    assert Decimal(str(bal_row.cached_qty)) == Decimal("30.0000")
