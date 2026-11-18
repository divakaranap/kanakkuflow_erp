from decimal import Decimal
import uuid
from fastapi.testclient import TestClient

from backend.app.models.customer import Customer, CustomerType
from backend.app.models.product import Product, ProductCategory


def get_auth_header(client: TestClient, username: str, password: str = "demo123"):
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_sync_reference_data_and_orders(client: TestClient, db, seeded_users):
    """
    Test Phase 10 Mobile PWA & Offline Sync:
    1. Download reference data (active customers & products).
    2. Submit offline order with client_order_uuid idempotency key.
    3. Verify idempotency protection: submitting the same client_order_uuid does NOT duplicate the order.
    4. Verify batch sync with both valid and invalid orders (resilient partial sync).
    """
    sales_headers = get_auth_header(client, "salesA")

    # 1. Setup Master Data
    prd = db.query(Product).filter(Product.sku == "MUR-SYNC-TEST").first()
    if not prd:
        prd = Product(
            sku="MUR-SYNC-TEST",
            product_name="Murukku 200g (Sync Test)",
            category=ProductCategory.MURUKKU,
            pack_size=Decimal("200.00"),
            pack_size_unit="g",
            hsn_code="1905",
            gst_rate=Decimal("0.0500"),
            selling_price_paise=5000,  # ₹50.00
            base_unit="packet",
            is_active=True,
        )
        db.add(prd)
        db.flush()

    cust = db.query(Customer).filter(Customer.customer_code == "CUST-SYNC-TEST").first()
    if not cust:
        cust = Customer(
            customer_code="CUST-SYNC-TEST",
            customer_name="Retailer Sync Test",
            customer_type=CustomerType.RETAILER,
            contact_person="Ramesh",
            phone="9876543210",
            email="ramesh@example.com",
            gstin="33AAAAA0000A1Z5",
            billing_address="12 Main Bazaar, Madurai",
            shipping_address="12 Main Bazaar, Madurai",
            city="Madurai",
            district="Madurai",
            state="Tamil Nadu",
            state_code="33",
            pincode="625001",
            credit_limit_paise=5000000,
            is_active=True,
        )
        db.add(cust)
        db.flush()
    db.commit()

    # 2. Test GET /sync/reference-data
    ref_res = client.get("/sync/reference-data", headers=sales_headers)
    assert ref_res.status_code == 200
    ref_data = ref_res.json()
    assert "customers" in ref_data
    assert "products" in ref_data
    assert len(ref_data["customers"]) >= 1
    assert len(ref_data["products"]) >= 1
    assert any(c["customer_code"] == "CUST-SYNC-TEST" for c in ref_data["customers"])
    assert any(p["sku"] == "MUR-SYNC-TEST" for p in ref_data["products"])

    # 3. Test POST /sync/orders - Single Order Sync
    client_uuid_1 = str(uuid.uuid4())
    sync_payload = {
        "orders": [
            {
                "client_order_uuid": client_uuid_1,
                "customer_id": str(cust.id),
                "notes": "Field sales mobile offline order",
                "items": [
                    {
                        "product_id": str(prd.id),
                        "ordered_quantity": 50,
                    }
                ],
            }
        ]
    }

    sync_res = client.post("/sync/orders", json=sync_payload, headers=sales_headers)
    assert sync_res.status_code == 200
    res_body = sync_res.json()
    assert len(res_body["synced"]) == 1
    assert len(res_body["failed"]) == 0
    synced_order = res_body["synced"][0]
    assert synced_order["client_order_uuid"] == client_uuid_1
    assert synced_order["order_number"].startswith("SO-")
    # 50 pkts * ₹50 = ₹2,500 + 5% GST (₹125) = ₹2,625 = 262,500 paise
    assert synced_order["grand_total_paise"] == 262500

    # 4. Test Idempotency: submit the exact same client_order_uuid again
    res_retry = client.post("/sync/orders", json=sync_payload, headers=sales_headers)
    assert res_retry.status_code == 200
    retry_body = res_retry.json()
    assert len(retry_body["synced"]) == 1
    assert retry_body["synced"][0]["client_order_uuid"] == client_uuid_1
    assert retry_body["synced"][0]["sales_order_id"] == synced_order["sales_order_id"]
    assert retry_body["synced"][0]["order_number"] == synced_order["order_number"]

    # 5. Test Batch Sync with partial failures
    client_uuid_2 = str(uuid.uuid4())
    client_uuid_bad = str(uuid.uuid4())
    fake_customer_id = str(uuid.uuid4())

    batch_payload = {
        "orders": [
            {
                "client_order_uuid": client_uuid_2,
                "customer_id": str(cust.id),
                "items": [
                    {
                        "product_id": str(prd.id),
                        "ordered_quantity": 10,
                    }
                ],
            },
            {
                "client_order_uuid": client_uuid_bad,
                "customer_id": fake_customer_id,
                "items": [
                    {
                        "product_id": str(prd.id),
                        "ordered_quantity": 10,
                    }
                ],
            },
        ]
    }

    batch_res = client.post("/sync/orders", json=batch_payload, headers=sales_headers)
    assert batch_res.status_code == 200
    batch_data = batch_res.json()
    assert len(batch_data["synced"]) == 1
    assert batch_data["synced"][0]["client_order_uuid"] == client_uuid_2
    assert len(batch_data["failed"]) == 1
    assert batch_data["failed"][0]["client_order_uuid"] == client_uuid_bad
    assert "Customer not found" in batch_data["failed"][0]["error"]
