"""Seed script for FACTORYFLOW demo accounts and Phase 2 master data."""
from decimal import Decimal
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal, engine
from backend.app.models.base import Base
from backend.app.models.user import User, UserRole
from backend.app.models.customer import Customer, CustomerType
from backend.app.models.supplier import Supplier
from backend.app.models.product import Product, ProductCategory
from backend.app.models.raw_material import RawMaterial, RawMaterialCategory
from backend.app.models.packaging import PackagingItem, PackagingCategory
from backend.app.models.price_list import PriceList, PriceListItem, PriceListCustomerType
from backend.app.services.auth_service import get_password_hash


DEMO_USERS = [
    {
        "username": "owner",
        "email": "owner@kanakkuflow.local",
        "full_name": "Senthil Kumar (Factory Owner)",
        "role": UserRole.OWNER,
        "password": "demo123",
    },
    {
        "username": "admin",
        "email": "admin@kanakkuflow.local",
        "full_name": "Ramesh Swaminathan (Admin Manager)",
        "role": UserRole.ADMIN,
        "password": "demo123",
    },
    {
        "username": "salesA",
        "email": "salesa@kanakkuflow.local",
        "full_name": "Karthik Raja (Sales Executive TN)",
        "role": UserRole.SALESMAN,
        "password": "demo123",
    },
    {
        "username": "salesB",
        "email": "salesb@kanakkuflow.local",
        "full_name": "Anand Prakash (Sales Executive KA)",
        "role": UserRole.SALESMAN,
        "password": "demo123",
    },
    {
        "username": "prod",
        "email": "prod@kanakkuflow.local",
        "full_name": "Muthu Vel (Production Supervisor)",
        "role": UserRole.PRODUCTION,
        "password": "demo123",
    },
    {
        "username": "auditor",
        "email": "auditor@kanakkuflow.local",
        "full_name": "Venkatesh CA (Chartered Accountant)",
        "role": UserRole.AUDITOR,
        "password": "demo123",
    },
]


def seed_users(db: Session) -> None:
    print("-> Seeding default demo users...")
    for user_data in DEMO_USERS:
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        if not existing:
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                hashed_password=get_password_hash(user_data["password"]),
                is_active=True,
            )
            db.add(user)
            print(f"   [+] Created user: {user.username} ({user.role.value})")
        else:
            print(f"   [*] User exists: {existing.username} ({existing.role.value})")
    db.commit()


def seed_master_data(db: Session) -> None:
    print("-> Seeding Phase 2 Master Data...")

    # 1. Products
    p_murukku = db.query(Product).filter(Product.sku == "MUR-200").first()
    if not p_murukku:
        p_murukku = Product(
            sku="MUR-200",
            product_name="Murukku 200 g",
            category=ProductCategory.MURUKKU,
            description="Traditional crunchy rice & urad dal savoury snack (Benchmark Item)",
            pack_size=Decimal("200.00"),
            pack_size_unit="g",
            hsn_code="1905",
            gst_rate=Decimal("0.0500"),
            selling_price_paise=5000,  # ₹50.00
            base_unit="packet",
            packets_per_carton=20,
            reorder_level=Decimal("50.0000"),
            is_active=True,
        )
        db.add(p_murukku)
        db.flush()
        print("   [+] Created product: Murukku 200 g (MUR-200)")
    else:
        print("   [*] Product exists: Murukku 200 g")

    # 2. Raw Materials
    raw_materials = [
        {
            "code": "RM-FLOUR",
            "name": "Raw Rice Flour (1st Grade)",
            "cat": RawMaterialCategory.FLOUR,
            "unit": "kg",
            "reorder": Decimal("20.0000"),
        },
        {
            "code": "RM-OIL",
            "name": "Refined Groundnut Cooking Oil",
            "cat": RawMaterialCategory.OIL,
            "unit": "litre",
            "reorder": Decimal("10.0000"),
        },
        {
            "code": "RM-SPICE",
            "name": "Special Salt & Spice Masala Mix",
            "cat": RawMaterialCategory.SPICE,
            "unit": "kg",
            "reorder": Decimal("2.0000"),
        },
    ]
    for rm in raw_materials:
        existing_rm = db.query(RawMaterial).filter(RawMaterial.material_code == rm["code"]).first()
        if not existing_rm:
            new_rm = RawMaterial(
                material_code=rm["code"],
                material_name=rm["name"],
                category=rm["cat"],
                base_unit=rm["unit"],
                reorder_level=rm["reorder"],
                is_active=True,
            )
            db.add(new_rm)
            print(f"   [+] Created raw material: {rm['code']} - {rm['name']}")
        else:
            print(f"   [*] Raw material exists: {rm['code']}")

    # 3. Packaging Items
    packaging_items = [
        {
            "code": "PK-POUCH-200",
            "name": "Printed 200g Murukku Pouch",
            "cat": PackagingCategory.POUCH,
            "unit": "piece",
            "reorder": Decimal("100.0000"),
        },
        {
            "code": "PK-CARTON",
            "name": "Corrugated Outer Carton Box (20 pkts)",
            "cat": PackagingCategory.CARTON,
            "unit": "piece",
            "reorder": Decimal("10.0000"),
        },
    ]
    for pkg in packaging_items:
        existing_pkg = db.query(PackagingItem).filter(PackagingItem.packaging_code == pkg["code"]).first()
        if not existing_pkg:
            new_pkg = PackagingItem(
                packaging_code=pkg["code"],
                packaging_name=pkg["name"],
                category=pkg["cat"],
                base_unit=pkg["unit"],
                reorder_level=pkg["reorder"],
                is_active=True,
            )
            db.add(new_pkg)
            print(f"   [+] Created packaging item: {pkg['code']} - {pkg['name']}")
        else:
            print(f"   [*] Packaging exists: {pkg['code']}")

    # 4. Suppliers
    suppliers = [
        {
            "code": "SUP-FLOUR",
            "name": "Sri Murugan Agro Flour Mills",
            "contact": "K. Murugan",
            "phone": "9842112345",
            "email": "muruganflour@example.com",
            "gstin": "33AABCS1234F1Z5",
            "address": "45 Mill Road, Pollachi",
            "city": "Coimbatore",
            "state": "Tamil Nadu",
            "state_code": "33",
            "pincode": "642001",
        },
        {
            "code": "SUP-OIL",
            "name": "VVD Pure Oils & Agro Industries",
            "contact": "S. Sundaram",
            "phone": "9443212345",
            "email": "vvdoils@example.com",
            "gstin": "33AABCV5678G1Z3",
            "address": "12 Harbour Express Road",
            "city": "Tuticorin",
            "state": "Tamil Nadu",
            "state_code": "33",
            "pincode": "628001",
        },
        {
            "code": "SUP-SPICE",
            "name": "Annapoorna Spices & Seasonings",
            "contact": "P. Annadurai",
            "phone": "9876543210",
            "email": "annapoornaspice@example.com",
            "gstin": "33AABCA9012H1Z1",
            "address": "88 Bazaar Street",
            "city": "Erode",
            "state": "Tamil Nadu",
            "state_code": "33",
            "pincode": "638001",
        },
        {
            "code": "SUP-PACK",
            "name": "Classic Pack & Carton Solutions",
            "contact": "R. Selvam",
            "phone": "9789012345",
            "email": "classicpack@example.com",
            "gstin": "33AABCC3456J1Z9",
            "address": "10 Industrial Estate, Guindy",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "state_code": "33",
            "pincode": "600032",
        },
    ]
    for s in suppliers:
        existing_s = db.query(Supplier).filter(Supplier.supplier_code == s["code"]).first()
        if not existing_s:
            new_s = Supplier(
                supplier_code=s["code"],
                supplier_name=s["name"],
                contact_person=s["contact"],
                phone=s["phone"],
                email=s["email"],
                gstin=s["gstin"],
                address=s["address"],
                city=s["city"],
                state=s["state"],
                state_code=s["state_code"],
                pincode=s["pincode"],
                payment_terms="Net 30",
                is_active=True,
            )
            db.add(new_s)
            print(f"   [+] Created supplier: {s['code']} - {s['name']}")
        else:
            print(f"   [*] Supplier exists: {s['code']}")

    # 5. Price Lists
    pl_retailer = db.query(PriceList).filter(PriceList.name == "Default Retailer Price List").first()
    if not pl_retailer:
        pl_retailer = PriceList(
            name="Default Retailer Price List",
            description="Standard MRP selling rate for local retailers (₹50/pkt)",
            customer_type=PriceListCustomerType.RETAILER,
            is_active=True,
        )
        db.add(pl_retailer)
        db.flush()
        item = PriceListItem(
            price_list_id=pl_retailer.id,
            product_id=p_murukku.id,
            selling_price_paise=5000,  # ₹50
        )
        db.add(item)
        print("   [+] Created price list: Default Retailer (₹50)")
    else:
        print("   [*] Price list exists: Default Retailer")

    pl_distributor = db.query(PriceList).filter(PriceList.name == "Default Distributor Price List").first()
    if not pl_distributor:
        pl_distributor = PriceList(
            name="Default Distributor Price List",
            description="Wholesale bulk distribution rate (₹42/pkt)",
            customer_type=PriceListCustomerType.DISTRIBUTOR,
            is_active=True,
        )
        db.add(pl_distributor)
        db.flush()
        item = PriceListItem(
            price_list_id=pl_distributor.id,
            product_id=p_murukku.id,
            selling_price_paise=4200,  # ₹42
        )
        db.add(item)
        print("   [+] Created price list: Default Distributor (₹42)")
    else:
        print("   [*] Price list exists: Default Distributor")

    # 6. Customers (Benchmark Customers)
    salesA = db.query(User).filter(User.username == "salesA").first()
    salesB = db.query(User).filter(User.username == "salesB").first()

    customers = [
        {
            "code": "CUST-RET-A",
            "name": "Retailer A (Sri Krishna Stores)",
            "type": CustomerType.RETAILER,
            "contact": "K. Krishnan",
            "phone": "9840123456",
            "email": "krishnaretail@example.com",
            "gstin": "33AAAAA0000A1Z5",  # Tamil Nadu GSTIN
            "billing": "14 North Car Street, Srirangam",
            "shipping": "14 North Car Street, Srirangam",
            "city": "Tiruchirappalli",
            "district": "Tiruchirappalli",
            "state": "Tamil Nadu",
            "state_code": "33",
            "pincode": "620006",
            "credit_limit": 5000000,  # ₹50,000
            "salesman_id": salesA.id if salesA else None,
            "price_list_id": pl_retailer.id,
        },
        {
            "code": "CUST-DIST-B",
            "name": "Distributor B (Karnataka Snack Distributors)",
            "type": CustomerType.DISTRIBUTOR,
            "contact": "B. Suresh Kumar",
            "phone": "9900123456",
            "email": "karnatakadist@example.com",
            "gstin": "29BBBBB1111B1Z2",  # Karnataka GSTIN
            "billing": "55 Chickpet Commercial Market",
            "shipping": "Warehouse 4, Yeshwanthpur Industrial Area",
            "city": "Bengaluru",
            "district": "Bengaluru Urban",
            "state": "Karnataka",
            "state_code": "29",
            "pincode": "560053",
            "credit_limit": 20000000,  # ₹2,00,000
            "salesman_id": salesB.id if salesB else None,
            "price_list_id": pl_distributor.id,
        },
    ]

    for c in customers:
        existing_c = db.query(Customer).filter(Customer.customer_code == c["code"]).first()
        if not existing_c:
            new_c = Customer(
                customer_code=c["code"],
                customer_name=c["name"],
                customer_type=c["type"],
                contact_person=c["contact"],
                phone=c["phone"],
                email=c["email"],
                gstin=c["gstin"],
                billing_address=c["billing"],
                shipping_address=c["shipping"],
                city=c["city"],
                district=c["district"],
                state=c["state"],
                state_code=c["state_code"],
                pincode=c["pincode"],
                credit_limit_paise=c["credit_limit"],
                assigned_salesman_id=c["salesman_id"],
                price_list_id=c["price_list_id"],
                is_active=True,
            )
            db.add(new_c)
            print(f"   [+] Created customer: {c['code']} - {c['name']} ({c['state']})")
        else:
            print(f"   [*] Customer exists: {c['code']}")

    db.commit()
    print("-> Phase 2 Master Data seeded successfully.")


def run_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_users(db)
        seed_master_data(db)
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
