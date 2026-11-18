import pytest


def get_auth_header(client, username, password="demo123"):
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_customer_crud_and_validation(client, seeded_users):
    admin_headers = get_auth_header(client, "admin")

    # 1. Invalid GSTIN format
    bad_gst_payload = {
        "customer_code": "CUST-BAD-GST",
        "customer_name": "Bad GST Store",
        "phone": "9876543210",
        "gstin": "INVALID123",
        "billing_address": "Street 1",
        "shipping_address": "Street 1",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "pincode": "600001",
    }
    bad_res = client.post("/customers", json=bad_gst_payload, headers=admin_headers)
    assert bad_res.status_code == 422  # validation error

    # 2. Valid customer creation
    valid_payload = {
        "customer_code": "CUST-NEW-01",
        "customer_name": "Sri Balaji Traders",
        "customer_type": "RETAILER",
        "phone": "9842198421",
        "gstin": "33AAAAA0000A1Z5",
        "billing_address": "12 Bazar Road",
        "shipping_address": "12 Bazar Road",
        "city": "Madurai",
        "state": "Tamil Nadu",
        "pincode": "625001",
    }
    create_res = client.post("/customers", json=valid_payload, headers=admin_headers)
    assert create_res.status_code == 201
    cust_data = create_res.json()
    assert cust_data["customer_code"] == "CUST-NEW-01"
    assert cust_data["state_code"] == "33"
    cust_id = cust_data["id"]

    # 3. Duplicate code rejection
    dup_res = client.post("/customers", json=valid_payload, headers=admin_headers)
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

    # 4. Search & Filtering
    search_res = client.get("/customers?search=Balaji", headers=admin_headers)
    assert search_res.status_code == 200
    assert len(search_res.json()) >= 1

    # 5. Soft-delete
    del_res = client.delete(f"/customers/{cust_id}", headers=admin_headers)
    assert del_res.status_code == 200
    assert del_res.json()["is_active"] is False


def test_supplier_crud(client, seeded_users):
    admin_headers = get_auth_header(client, "admin")

    supplier_payload = {
        "supplier_code": "SUP-TEST-01",
        "supplier_name": "Cauvery Agro Products",
        "phone": "9876543210",
        "gstin": "33AABCC1234D1Z8",
        "address": "Factory Zone 2",
        "city": "Thanjavur",
        "state": "Tamil Nadu",
        "pincode": "613001",
    }
    res = client.post("/suppliers", json=supplier_payload, headers=admin_headers)
    assert res.status_code == 201
    sup_data = res.json()
    assert sup_data["supplier_code"] == "SUP-TEST-01"

    # Duplicate code rejection
    res_dup = client.post("/suppliers", json=supplier_payload, headers=admin_headers)
    assert res_dup.status_code == 400


def test_product_crud_and_pricing_rules(client, seeded_users):
    admin_headers = get_auth_header(client, "admin")

    # Positive price requirement: 0 or negative price should be rejected
    invalid_price_payload = {
        "sku": "MUR-BAD-PRICE",
        "product_name": "Zero Price Murukku",
        "selling_price_paise": 0,
    }
    bad_res = client.post("/products", json=invalid_price_payload, headers=admin_headers)
    assert bad_res.status_code == 422

    # Valid product creation
    valid_payload = {
        "sku": "MUR-TEST-200",
        "product_name": "Test Murukku 200g",
        "category": "MURUKKU",
        "pack_size": "200.00",
        "pack_size_unit": "g",
        "hsn_code": "1905",
        "gst_rate": "0.0500",
        "selling_price_paise": 5000,  # ₹50
        "base_unit": "packet",
        "packets_per_carton": 20,
        "reorder_level": "100.0000",
    }
    create_res = client.post("/products", json=valid_payload, headers=admin_headers)
    assert create_res.status_code == 201
    prod_data = create_res.json()
    assert prod_data["sku"] == "MUR-TEST-200"
    assert prod_data["selling_price_paise"] == 5000

    # Duplicate SKU rejection
    dup_res = client.post("/products", json=valid_payload, headers=admin_headers)
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]


def test_raw_materials_and_packaging(client, seeded_users):
    prod_headers = get_auth_header(client, "prod")

    # Raw material creation
    rm_res = client.post(
        "/raw-materials",
        json={
            "material_code": "RM-TEST-FLOUR",
            "material_name": "Gram Flour (Besan)",
            "category": "FLOUR",
            "base_unit": "kg",
            "reorder_level": "25.0000",
        },
        headers=prod_headers,
    )
    assert rm_res.status_code == 201
    assert rm_res.json()["base_unit"] == "kg"

    # Packaging item creation
    pkg_res = client.post(
        "/packaging",
        json={
            "packaging_code": "PK-TEST-POUCH",
            "packaging_name": "Silver Foil Pouch 200g",
            "category": "POUCH",
            "base_unit": "piece",
            "reorder_level": "500.0000",
        },
        headers=prod_headers,
    )
    assert pkg_res.status_code == 201
    assert pkg_res.json()["base_unit"] == "piece"


def test_price_lists_and_effective_pricing(client, seeded_users):
    admin_headers = get_auth_header(client, "admin")

    # 1. Create a Product
    p_res = client.post(
        "/products",
        json={
            "sku": "MUR-EFF-PRICE",
            "product_name": "Effective Price Murukku",
            "category": "MURUKKU",
            "pack_size": "200.00",
            "pack_size_unit": "g",
            "selling_price_paise": 5000,  # Default ₹50
            "base_unit": "packet",
            "packets_per_carton": 20,
        },
        headers=admin_headers,
    )
    assert p_res.status_code == 201
    prod_id = p_res.json()["id"]

    # 2. Create a Customer Type Price List for DISTRIBUTOR (₹40 = 4000 paise)
    pl_dist_res = client.post(
        "/price-lists",
        json={
            "name": "Distributor Wholesale Rate List",
            "customer_type": "DISTRIBUTOR",
            "items": [{"product_id": prod_id, "selling_price_paise": 4000}],
        },
        headers=admin_headers,
    )
    assert pl_dist_res.status_code == 201

    # 3. Create a Customer Specific Price List (₹38 = 3800 paise)
    pl_cust_res = client.post(
        "/price-lists",
        json={
            "name": "VIP Customer Special Rate",
            "customer_type": "ALL",
            "items": [{"product_id": prod_id, "selling_price_paise": 3800}],
        },
        headers=admin_headers,
    )
    assert pl_cust_res.status_code == 201
    vip_pl_id = pl_cust_res.json()["id"]

    # 4. Create Distributor Customer without custom price list -> should get DISTRIBUTOR rate (₹40)
    c_dist = client.post(
        "/customers",
        json={
            "customer_code": "CUST-DIST-EFF",
            "customer_name": "Bangalore Bulk Dist",
            "customer_type": "DISTRIBUTOR",
            "phone": "9900990099",
            "gstin": "29BBBBB1111B1Z2",
            "billing_address": "Chickpet",
            "shipping_address": "Chickpet",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560053",
        },
        headers=admin_headers,
    )
    assert c_dist.status_code == 201
    dist_cust_id = c_dist.json()["id"]

    eff1 = client.get(
        f"/price-lists/effective-price?customer_id={dist_cust_id}&product_id={prod_id}",
        headers=admin_headers,
    )
    assert eff1.status_code == 200
    assert eff1.json()["selling_price_paise"] == 4000
    assert eff1.json()["source"] == "CUSTOMER_TYPE_PRICE_LIST"

    # 5. Create Customer with VIP price list assigned -> should get VIP rate (₹38)
    c_vip = client.post(
        "/customers",
        json={
            "customer_code": "CUST-VIP-EFF",
            "customer_name": "VIP Retailer",
            "customer_type": "RETAILER",
            "phone": "9842198422",
            "gstin": "33AAAAA0000A1Z5",
            "billing_address": "Tiruchirappalli",
            "shipping_address": "Tiruchirappalli",
            "city": "Tiruchirappalli",
            "state": "Tamil Nadu",
            "pincode": "620001",
            "price_list_id": vip_pl_id,
        },
        headers=admin_headers,
    )
    assert c_vip.status_code == 201
    vip_cust_id = c_vip.json()["id"]

    eff2 = client.get(
        f"/price-lists/effective-price?customer_id={vip_cust_id}&product_id={prod_id}",
        headers=admin_headers,
    )
    assert eff2.status_code == 200
    assert eff2.json()["selling_price_paise"] == 3800
    assert eff2.json()["source"] == "CUSTOMER_PRICE_LIST"

    # 6. Customer without any matching price list -> fallback to PRODUCT_DEFAULT (₹50)
    c_plain = client.post(
        "/customers",
        json={
            "customer_code": "CUST-PLAIN-EFF",
            "customer_name": "Plain Retailer",
            "customer_type": "RETAILER",
            "phone": "9842198423",
            "gstin": "33AAAAA0000A1Z5",
            "billing_address": "Salem",
            "shipping_address": "Salem",
            "city": "Salem",
            "state": "Tamil Nadu",
            "pincode": "636001",
        },
        headers=admin_headers,
    )
    assert c_plain.status_code == 201
    plain_cust_id = c_plain.json()["id"]

    eff3 = client.get(
        f"/price-lists/effective-price?customer_id={plain_cust_id}&product_id={prod_id}",
        headers=admin_headers,
    )
    assert eff3.status_code == 200
    assert eff3.json()["selling_price_paise"] == 5000
    assert eff3.json()["source"] == "PRODUCT_DEFAULT"


def test_role_based_permissions_on_master_data(client, seeded_users):
    sales_headers = get_auth_header(client, "salesA")
    auditor_headers = get_auth_header(client, "auditor")
    admin_headers = get_auth_header(client, "admin")

    # 1. Salesman cannot create product (Forbidden 403)
    sales_create_prod = client.post(
        "/products",
        json={"sku": "FORBIDDEN-01", "product_name": "Illegal Murukku", "selling_price_paise": 5000},
        headers=sales_headers,
    )
    assert sales_create_prod.status_code == 403

    # 2. Salesman CAN view products (200)
    sales_list_prod = client.get("/products", headers=sales_headers)
    assert sales_list_prod.status_code == 200

    # 3. Auditor cannot create or edit customer (Forbidden 403)
    auditor_create_cust = client.post(
        "/customers",
        json={"customer_code": "AUD-FORBIDDEN", "customer_name": "Audit Cust"},
        headers=auditor_headers,
    )
    assert auditor_create_cust.status_code == 403

    # 4. Auditor CAN view customers (200)
    auditor_list_cust = client.get("/customers", headers=auditor_headers)
    assert auditor_list_cust.status_code == 200

    # 5. Admin has full CRUD access (200)
    admin_list = client.get("/customers", headers=admin_headers)
    assert admin_list.status_code == 200
