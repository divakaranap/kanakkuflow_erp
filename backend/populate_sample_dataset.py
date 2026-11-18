"""
Comprehensive Sample Dataset Generator for FACTORYFLOW (kanakkuflow)
=====================================================================
Seeds a complete, production-grade demo dataset matching the NIT Trichy
Internship Problem Statement:
- 6 Role-Based Demo Users (password: demo123)
- 5 Finished Goods Products (Murukku, Mixture, Banana Chips, Potato Chips, Sweets)
- 8 Raw Materials & 6 Packaging Items
- 5 Suppliers & Tiered Price Lists (Retailer & Distributor)
- 4 Customers (Tamil Nadu Retailers, Karnataka & Kerala Distributors)
- Opening Inventory Balances & Chronological Stock Ledger Movements
- Active Recipe BOMs for all production lines
- Production Runs with realistic Yield Variances & Packet Costing
- Sales Orders, GST Tax Invoices (Intra & Inter state) & Dispatches
- Customer Payments, Invoice Allocations & Customer Ledger running balances
- Complete Double-Entry Journal Entries & Chart of Accounts
- Audit Trail Events
"""

from decimal import Decimal
from datetime import date, datetime, timedelta
import uuid

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
from backend.app.models.inventory import InventoryBalance, StockMovement, MovementType, InventoryItemType
from backend.app.models.bom import BOM, BOMItem, BOMStatus
from backend.app.models.production import (
    ProductionRun,
    ProductionRunMaterial,
    ProductionRunOverhead,
    ProductionRunStatus,
    OverheadExpenseType,
    VarianceStatus,
)
from backend.app.models.sales import (
    SalesOrder,
    SalesOrderItem,
    SalesInvoice,
    SalesInvoiceItem,
    SalesOrderStatus,
    InvoiceStatus,
)
from backend.app.models.dispatch import Dispatch, DispatchItem, DispatchStatus
from backend.app.models.payment import (
    CustomerPayment,
    PaymentAllocation,
    CustomerLedgerEntry,
    PaymentMode,
    PaymentStatus,
)
from backend.app.models.accounting import (
    Account,
    JournalEntry,
    JournalEntryLine,
    AuditLog,
)
from backend.app.services.auth_service import get_password_hash
from backend.app.services.accounting_service import seed_chart_of_accounts, post_sales_invoice_journal, post_payment_journal
from backend.app.services.gst_service import calculate_gst


def populate_all():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        print("=================================================================")
        print("  POPULATING FACTORYFLOW SAMPLE DATASET")
        print("=================================================================")

        # -------------------------------------------------------------
        # 1. USERS & ROLES
        # -------------------------------------------------------------
        print("\n[1/10] Seeding Users...")
        users_data = [
            ("owner", "owner@kanakkuflow.local", "Senthil Kumar (Managing Director)", UserRole.OWNER),
            ("admin", "admin@kanakkuflow.local", "Ramesh Swaminathan (Operations Admin)", UserRole.ADMIN),
            ("salesA", "salesa@kanakkuflow.local", "Karthik Raja (Sales Exec - Tamil Nadu)", UserRole.SALESMAN),
            ("salesB", "salesb@kanakkuflow.local", "Anand Prakash (Sales Exec - Karnataka)", UserRole.SALESMAN),
            ("prod", "prod@kanakkuflow.local", "Muthu Vel (Production Supervisor)", UserRole.PRODUCTION),
            ("auditor", "auditor@kanakkuflow.local", "Venkatesh CA (Statutory Auditor)", UserRole.AUDITOR),
        ]
        user_map = {}
        for username, email, full_name, role in users_data:
            u = db.query(User).filter(User.username == username).first()
            if not u:
                u = User(
                    username=username,
                    email=email,
                    full_name=full_name,
                    role=role,
                    hashed_password=get_password_hash("demo123"),
                    is_active=True,
                )
                db.add(u)
                db.flush()
            user_map[username] = u
        print(f"   -> {len(user_map)} users verified.")

        # Seed Standard Chart of Accounts
        seed_chart_of_accounts(db)

        # -------------------------------------------------------------
        # 2. MASTER DATA: PRODUCTS
        # -------------------------------------------------------------
        print("\n[2/10] Seeding Products (Finished Goods)...")
        products_data = [
            ("MUR-200", "Murukku 200g", ProductCategory.MURUKKU, "Crispy traditional South Indian rice flour spirals", Decimal("200.00"), "g", "1905", Decimal("0.0500"), 5000, 20),
            ("MIX-250", "Madras Mixture 250g", ProductCategory.MIXTURE, "Spicy savouries, roasted peanuts and fried curry leaves", Decimal("250.00"), "g", "1905", Decimal("0.0500"), 6000, 20),
            ("BAN-150", "Banana Chips Salted 150g", ProductCategory.CHIPS, "Authentic Nendran raw banana chips fried in pure oil", Decimal("150.00"), "g", "2008", Decimal("0.0500"), 5500, 25),
            ("POT-100", "Potato Chips Spicy 100g", ProductCategory.CHIPS, "Crispy thin potato wafers tossed in chilli rock salt", Decimal("100.00"), "g", "2005", Decimal("0.0500"), 4000, 30),
            ("SWE-500", "Traditional Mysore Pak 500g", ProductCategory.SWEETS, "Melt-in-mouth gram flour, sugar and pure ghee sweet", Decimal("500.00"), "g", "2106", Decimal("0.0500"), 22000, 10),
        ]
        product_map = {}
        for sku, name, cat, desc, psize, punit, hsn, gst, price, per_box in products_data:
            p = db.query(Product).filter(Product.sku == sku).first()
            if not p:
                p = Product(
                    sku=sku,
                    product_name=name,
                    category=cat,
                    description=desc,
                    pack_size=psize,
                    pack_size_unit=punit,
                    hsn_code=hsn,
                    gst_rate=gst,
                    selling_price_paise=price,
                    base_unit="packet",
                    packets_per_carton=per_box,
                    reorder_level=Decimal("50.0000"),
                    is_active=True,
                )
                db.add(p)
                db.flush()
            product_map[sku] = p
        print(f"   -> {len(product_map)} products verified.")

        # -------------------------------------------------------------
        # 3. MASTER DATA: RAW MATERIALS & PACKAGING
        # -------------------------------------------------------------
        print("\n[3/10] Seeding Ingredients & Packaging...")
        rm_data = [
            ("RM-RICE-01", "Raw Rice Flour (1st Grade)", RawMaterialCategory.FLOUR, "kg", Decimal("50.0000")),
            ("RM-BESAN-01", "Gram Flour / Besan", RawMaterialCategory.FLOUR, "kg", Decimal("30.0000")),
            ("RM-OIL-01", "Refined Cooking Oil", RawMaterialCategory.OIL, "litre", Decimal("25.0000")),
            ("RM-SPICE-01", "Masala & Rock Salt Mix", RawMaterialCategory.SPICE, "kg", Decimal("10.0000")),
            ("RM-BANANA-01", "Raw Nendran Green Bananas", RawMaterialCategory.OTHER, "kg", Decimal("40.0000")),
            ("RM-POTATO-01", "Processing Grade Potatoes", RawMaterialCategory.OTHER, "kg", Decimal("40.0000")),
            ("RM-GHEE-01", "Pure Cow Ghee", RawMaterialCategory.OIL, "kg", Decimal("15.0000")),
            ("RM-SUGAR-01", "Refined Cane Sugar", RawMaterialCategory.OTHER, "kg", Decimal("30.0000")),
        ]
        rm_map = {}
        for code, name, cat, unit, reorder in rm_data:
            rm = db.query(RawMaterial).filter(RawMaterial.material_code == code).first()
            if not rm:
                rm = RawMaterial(
                    material_code=code,
                    material_name=name,
                    category=cat,
                    base_unit=unit,
                    reorder_level=reorder,
                    is_active=True,
                )
                db.add(rm)
                db.flush()
            rm_map[code] = rm

        pkg_data = [
            ("PKG-POUCH-200", "Printed 200g Murukku Pouch", PackagingCategory.POUCH, "piece", Decimal("500.0000")),
            ("PKG-POUCH-250", "Printed 250g Mixture Pouch", PackagingCategory.POUCH, "piece", Decimal("500.0000")),
            ("PKG-POUCH-150", "Foil 150g Banana Chips Pouch", PackagingCategory.POUCH, "piece", Decimal("500.0000")),
            ("PKG-POUCH-100", "Nitrogen Foil 100g Potato Chips", PackagingCategory.POUCH, "piece", Decimal("500.0000")),
            ("PKG-BOX-500", "Sweet Gift Box 500g", PackagingCategory.CARTON, "piece", Decimal("200.0000")),
            ("PKG-CARTON-20", "Corrugated Master Carton Box", PackagingCategory.CARTON, "piece", Decimal("50.0000")),
        ]
        pkg_map = {}
        for code, name, cat, unit, reorder in pkg_data:
            pkg = db.query(PackagingItem).filter(PackagingItem.packaging_code == code).first()
            if not pkg:
                pkg = PackagingItem(
                    packaging_code=code,
                    packaging_name=name,
                    category=cat,
                    base_unit=unit,
                    reorder_level=reorder,
                    is_active=True,
                )
                db.add(pkg)
                db.flush()
            pkg_map[code] = pkg
        print(f"   -> {len(rm_map)} raw materials, {len(pkg_map)} packaging items verified.")

        # -------------------------------------------------------------
        # 4. SUPPLIERS & PRICE LISTS
        # -------------------------------------------------------------
        print("\n[4/10] Seeding Suppliers & Price Lists...")
        suppliers_data = [
            ("SUP-FLOUR", "Sri Murugan Agro Flour Mills", "M. Palanisamy", "9443112233", "muruganagro@example.com", "33AABCS1234F1Z1", "Madurai", "33"),
            ("SUP-OIL", "VVD Pure Oils & Agro Industries", "S. Sundaram", "9443212345", "vvdoils@example.com", "33AABCV5678G1Z3", "Tuticorin", "33"),
            ("SUP-SPICE", "Annapoorna Spices & Seasonings", "P. Annadurai", "9876543210", "annapoornaspice@example.com", "33AABCA9012H1Z1", "Erode", "33"),
            ("SUP-FARM", "Pollachi Fresh Farms", "K. Nachimuthu", "9842155667", "pollachifresh@example.com", "33AABCP8899K1Z4", "Pollachi", "33"),
            ("SUP-PACK", "Classic Pack & Carton Solutions", "R. Selvam", "9789012345", "classicpack@example.com", "33AABCC3456J1Z9", "Chennai", "33"),
        ]
        for code, name, contact, phone, email, gstin, city, scode in suppliers_data:
            s = db.query(Supplier).filter(Supplier.supplier_code == code).first()
            if not s:
                s = Supplier(
                    supplier_code=code,
                    supplier_name=name,
                    contact_person=contact,
                    phone=phone,
                    email=email,
                    gstin=gstin,
                    address=f"Industrial Zone, {city}",
                    city=city,
                    state="Tamil Nadu",
                    state_code=scode,
                    pincode="620001",
                    is_active=True,
                )
                db.add(s)

        # Price Lists
        pl_ret = db.query(PriceList).filter(PriceList.name == "Standard Retailer Price List").first()
        if not pl_ret:
            pl_ret = PriceList(
                name="Standard Retailer Price List",
                description="Retail MRP rates for supermarkets and general stores",
                customer_type=PriceListCustomerType.RETAILER,
                is_active=True,
            )
            db.add(pl_ret)
            db.flush()
            for sku, p in product_map.items():
                db.add(PriceListItem(price_list_id=pl_ret.id, product_id=p.id, selling_price_paise=p.selling_price_paise))

        pl_dist = db.query(PriceList).filter(PriceList.name == "Wholesale Distributor Price List").first()
        if not pl_dist:
            pl_dist = PriceList(
                name="Wholesale Distributor Price List",
                description="Tiered bulk wholesale rates (15-20% margin)",
                customer_type=PriceListCustomerType.DISTRIBUTOR,
                is_active=True,
            )
            db.add(pl_dist)
            db.flush()
            dist_rates = {
                "MUR-200": 4200,   # ₹42.00
                "MIX-250": 5000,   # ₹50.00
                "BAN-150": 4600,   # ₹46.00
                "POT-100": 3400,   # ₹34.00
                "SWE-500": 18500,  # ₹185.00
            }
            for sku, rate in dist_rates.items():
                p = product_map.get(sku)
                if p:
                    db.add(PriceListItem(price_list_id=pl_dist.id, product_id=p.id, selling_price_paise=rate))

        # Customers
        customers_data = [
            ("CUST-RET-A", "Sri Krishna Stores (Retailer A)", CustomerType.RETAILER, "K. Krishnan", "9840123456", "33AAAAA0000A1Z5", "Srirangam, Trichy", "Tiruchirappalli", "Tamil Nadu", "33", 5000000, user_map["salesA"].id, pl_ret.id),
            ("CUST-RET-B", "Saravana Supermarket (Retailer B)", CustomerType.RETAILER, "M. Saravanan", "9840998877", "33AABCS7890D1Z2", "Thillai Nagar, Trichy", "Tiruchirappalli", "Tamil Nadu", "33", 7500000, user_map["salesA"].id, pl_ret.id),
            ("CUST-DIST-B", "Karnataka Snack Distributors", CustomerType.DISTRIBUTOR, "B. Suresh Kumar", "9900123456", "29BBBBB1111B1Z2", "Chickpet Market", "Bengaluru", "Karnataka", "29", 20000000, user_map["salesB"].id, pl_dist.id),
            ("CUST-DIST-C", "Kerala Hot Chips Wholesale", CustomerType.DISTRIBUTOR, "P. George", "9895012345", "32CCCCC2222C1Z8", "MG Road, Ernakulam", "Kochi", "Kerala", "32", 15000000, user_map["salesA"].id, pl_dist.id),
        ]
        customer_map = {}
        for code, name, ctype, contact, phone, gstin, addr, city, state, scode, credit, salesman_id, plist_id in customers_data:
            c = db.query(Customer).filter(Customer.customer_code == code).first()
            if not c:
                c = Customer(
                    customer_code=code,
                    customer_name=name,
                    customer_type=ctype,
                    contact_person=contact,
                    phone=phone,
                    email=f"{code.lower()}@example.com",
                    gstin=gstin,
                    billing_address=addr,
                    shipping_address=addr,
                    city=city,
                    district=city,
                    state=state,
                    state_code=scode,
                    pincode="620001",
                    credit_limit_paise=credit,
                    assigned_salesman_id=salesman_id,
                    price_list_id=plist_id,
                    is_active=True,
                )
                db.add(c)
                db.flush()
            customer_map[code] = c

        # -------------------------------------------------------------
        # 5. INVENTORY OPENING STOCKS & MOVEMENTS
        # -------------------------------------------------------------
        print("\n[5/10] Initializing Stock Ledger & Opening Balances...")
        opening_items = [
            (InventoryItemType.RAW, rm_map["RM-RICE-01"].id, Decimal("300.0000"), 4000, "Raw Rice Flour 300kg @ ₹40.00"),
            (InventoryItemType.RAW, rm_map["RM-BESAN-01"].id, Decimal("200.0000"), 7000, "Gram Flour Besan 200kg @ ₹70.00"),
            (InventoryItemType.RAW, rm_map["RM-OIL-01"].id, Decimal("150.0000"), 12000, "Refined Cooking Oil 150L @ ₹120.00"),
            (InventoryItemType.RAW, rm_map["RM-SPICE-01"].id, Decimal("30.0000"), 15000, "Spices Mix 30kg @ ₹150.00"),
            (InventoryItemType.RAW, rm_map["RM-BANANA-01"].id, Decimal("120.0000"), 3500, "Raw Bananas 120kg @ ₹35.00"),
            (InventoryItemType.RAW, rm_map["RM-POTATO-01"].id, Decimal("100.0000"), 2500, "Potatoes 100kg @ ₹25.00"),
            (InventoryItemType.RAW, rm_map["RM-GHEE-01"].id, Decimal("40.0000"), 55000, "Pure Cow Ghee 40kg @ ₹550.00"),
            (InventoryItemType.RAW, rm_map["RM-SUGAR-01"].id, Decimal("80.0000"), 4200, "Cane Sugar 80kg @ ₹42.00"),

            (InventoryItemType.PACKAGING, pkg_map["PKG-POUCH-200"].id, Decimal("2500.0000"), 150, "Murukku Pouches 2500pcs @ ₹1.50"),
            (InventoryItemType.PACKAGING, pkg_map["PKG-POUCH-250"].id, Decimal("2000.0000"), 160, "Mixture Pouches 2000pcs @ ₹1.60"),
            (InventoryItemType.PACKAGING, pkg_map["PKG-POUCH-150"].id, Decimal("1500.0000"), 180, "Banana Chips Pouches 1500pcs @ ₹1.80"),
            (InventoryItemType.PACKAGING, pkg_map["PKG-CARTON-20"].id, Decimal("250.0000"), 1500, "Master Cartons 250pcs @ ₹15.00"),

            (InventoryItemType.FG, product_map["MUR-200"].id, Decimal("238.0000"), 3114, "Murukku 200g Stock 238 pkts @ ₹31.14"),
            (InventoryItemType.FG, product_map["MIX-250"].id, Decimal("100.0000"), 3800, "Madras Mixture 250g Stock 100 pkts @ ₹38.00"),
            (InventoryItemType.FG, product_map["BAN-150"].id, Decimal("80.0000"), 3500, "Banana Chips 150g Stock 80 pkts @ ₹35.00"),
        ]

        for itype, item_id, qty, cost, ref in opening_items:
            existing_sm = db.query(StockMovement).filter(
                StockMovement.item_type == itype,
                StockMovement.item_id == str(item_id),
                StockMovement.movement_type == MovementType.OPENING,
            ).first()
            if not existing_sm:
                sm = StockMovement(
                    item_type=itype,
                    item_id=str(item_id),
                    movement_type=MovementType.OPENING,
                    qty_delta=qty,
                    unit_cost_paise=cost,
                    total_value_paise=int(qty * cost),
                    source_type="OPENING_STOCK",
                    source_id="00000000-0000-0000-0000-000000000000",
                    reference_number="INIT-2026",
                    notes=ref,
                    created_by=user_map["admin"].id,
                )
                db.add(sm)

                bal = db.query(InventoryBalance).filter(
                    InventoryBalance.item_type == itype,
                    InventoryBalance.item_id == str(item_id),
                ).first()
                if not bal:
                    bal = InventoryBalance(
                        item_type=itype,
                        item_id=str(item_id),
                        cached_qty=qty,
                        weighted_avg_rate_paise=cost,
                        total_value_paise=int(qty * cost),
                    )
                    db.add(bal)
                else:
                    bal.cached_qty = qty
                    bal.weighted_avg_rate_paise = cost
                    bal.total_value_paise = int(qty * cost)

        # -------------------------------------------------------------
        # 6. RECIPE BOMS
        # -------------------------------------------------------------
        print("\n[6/10] Creating Active Recipe BOMs...")
        boms_to_create = [
            (
                "BOM-MUR-200",
                product_map["MUR-200"].id,
                Decimal("250.0000"),
                Decimal("4.00"),
                "Benchmark Standard Recipe for Murukku 200g (250 pkts target)",
                [
                    (InventoryItemType.RAW, rm_map["RM-RICE-01"].id, Decimal("35.0000"), "kg"),
                    (InventoryItemType.RAW, rm_map["RM-BESAN-01"].id, Decimal("10.0000"), "kg"),
                    (InventoryItemType.RAW, rm_map["RM-OIL-01"].id, Decimal("5.0000"), "litre"),
                    (InventoryItemType.RAW, rm_map["RM-SPICE-01"].id, Decimal("1.0000"), "kg"),
                    (InventoryItemType.PACKAGING, pkg_map["PKG-POUCH-200"].id, Decimal("250.0000"), "piece"),
                    (InventoryItemType.PACKAGING, pkg_map["PKG-CARTON-20"].id, Decimal("12.5000"), "piece"),
                ],
            ),
            (
                "BOM-MIX-250",
                product_map["MIX-250"].id,
                Decimal("200.0000"),
                Decimal("3.00"),
                "Standard Recipe for Madras Mixture 250g (200 pkts target)",
                [
                    (InventoryItemType.RAW, rm_map["RM-BESAN-01"].id, Decimal("30.0000"), "kg"),
                    (InventoryItemType.RAW, rm_map["RM-RICE-01"].id, Decimal("10.0000"), "kg"),
                    (InventoryItemType.RAW, rm_map["RM-OIL-01"].id, Decimal("8.0000"), "litre"),
                    (InventoryItemType.RAW, rm_map["RM-SPICE-01"].id, Decimal("2.0000"), "kg"),
                    (InventoryItemType.PACKAGING, pkg_map["PKG-POUCH-250"].id, Decimal("200.0000"), "piece"),
                    (InventoryItemType.PACKAGING, pkg_map["PKG-CARTON-20"].id, Decimal("10.0000"), "piece"),
                ],
            ),
        ]

        bom_map = {}
        for bcode, pid, yld, tol, desc, items in boms_to_create:
            b = db.query(BOM).filter(BOM.bom_code == bcode).first()
            if not b:
                b = BOM(
                    bom_code=bcode,
                    product_id=str(pid),
                    version=1,
                    batch_yield_packets=yld,
                    tolerance_pct=tol,
                    description=desc,
                    status=BOMStatus.ACTIVE,
                    created_by=user_map["admin"].id,
                    items=[
                        BOMItem(item_type=itype, item_id=str(iid), quantity_per_batch=iqty, unit=iunit)
                        for itype, iid, iqty, iunit in items
                    ],
                )
                db.add(b)
                db.flush()
            bom_map[bcode] = b

        # -------------------------------------------------------------
        # 7. PRODUCTION RUN WITH YIELD VARIANCE
        # -------------------------------------------------------------
        print("\n[7/10] Recording Benchmark Production Run...")
        existing_run = db.query(ProductionRun).filter(ProductionRun.run_number == "RUN-202611-0001").first()
        if not existing_run:
            p_run = ProductionRun(
                run_number="RUN-202611-0001",
                product_id=product_map["MUR-200"].id,
                bom_id=bom_map["BOM-MUR-200"].id,
                bom_version_snapshot="BOM-MUR-200 v1",
                batch_number="BATCH-MUR-001",
                number_of_batches=Decimal("1.00"),
                expected_output=Decimal("250.0000"),
                actual_good_output=Decimal("238.0000"),  # Benchmark yield
                damaged_packaging=Decimal("12.0000"),
                wastage_quantity=Decimal("12.0000"),
                status=ProductionRunStatus.POSTED,
                planned_material_cost_paise=390000,
                actual_material_cost_paise=405500,
                packaging_cost_paise=55500,
                labour_cost_paise=120000,
                utility_cost_paise=60000,
                total_production_cost_paise=585500,
                cost_per_packet_paise=2460,
                cost_per_packet_decimal=Decimal("24.6008"),
                variance_status=VarianceStatus.WARNING,
                supervisor_id=user_map["prod"].id,
                notes="Standard batch run: rice flour 35kg, besan 10kg, oil 5.2L (0.2L variance)",
                materials=[
                    ProductionRunMaterial(item_type=InventoryItemType.RAW, item_id=rm_map["RM-RICE-01"].id, planned_quantity=Decimal("35.0000"), issued_quantity=Decimal("35.0000"), consumed_quantity=Decimal("35.0000"), unit="kg", planned_unit_cost=4000, actual_unit_cost=4000, material_cost_paise=140000),
                    ProductionRunMaterial(item_type=InventoryItemType.RAW, item_id=rm_map["RM-BESAN-01"].id, planned_quantity=Decimal("10.0000"), issued_quantity=Decimal("10.0000"), consumed_quantity=Decimal("10.0000"), unit="kg", planned_unit_cost=7000, actual_unit_cost=7000, material_cost_paise=70000),
                    ProductionRunMaterial(item_type=InventoryItemType.RAW, item_id=rm_map["RM-OIL-01"].id, planned_quantity=Decimal("5.0000"), issued_quantity=Decimal("5.2000"), consumed_quantity=Decimal("5.2000"), unit="litre", planned_unit_cost=12000, actual_unit_cost=12000, material_cost_paise=62400),
                    ProductionRunMaterial(item_type=InventoryItemType.RAW, item_id=rm_map["RM-SPICE-01"].id, planned_quantity=Decimal("1.0000"), issued_quantity=Decimal("1.0000"), consumed_quantity=Decimal("1.0000"), unit="kg", planned_unit_cost=15000, actual_unit_cost=15000, material_cost_paise=15000),
                    ProductionRunMaterial(item_type=InventoryItemType.PACKAGING, item_id=pkg_map["PKG-POUCH-200"].id, planned_quantity=Decimal("250.0000"), issued_quantity=Decimal("250.0000"), consumed_quantity=Decimal("250.0000"), unit="piece", planned_unit_cost=150, actual_unit_cost=150, material_cost_paise=37500),
                    ProductionRunMaterial(item_type=InventoryItemType.PACKAGING, item_id=pkg_map["PKG-CARTON-20"].id, planned_quantity=Decimal("12.5000"), issued_quantity=Decimal("12.0000"), consumed_quantity=Decimal("12.0000"), unit="piece", planned_unit_cost=1500, actual_unit_cost=1500, material_cost_paise=18000),
                ],
                overheads=[
                    ProductionRunOverhead(expense_type=OverheadExpenseType.LABOUR, amount_paise=120000, description="Fryer and packaging labour wages"),
                    ProductionRunOverhead(expense_type=OverheadExpenseType.GAS, amount_paise=60000, description="Commercial LPG fuel charge"),
                ],
            )
            db.add(p_run)
            db.flush()

        # -------------------------------------------------------------
        # 8. SALES ORDERS, GST INVOICES & DISPATCHES
        # -------------------------------------------------------------
        print("\n[8/10] Booking Benchmark Sales Order & GST Invoice...")
        existing_so1 = db.query(SalesOrder).filter(SalesOrder.order_number == "SO-202611-0001").first()
        if not existing_so1:
            # Retailer A order: 150 pkts @ ₹50 = ₹7,500 + 5% GST (CGST ₹187.50, SGST ₹187.50) = ₹7,875.00
            so1 = SalesOrder(
                order_number="SO-202611-0001",
                customer_id=customer_map["CUST-RET-A"].id,
                order_date=date.today(),
                delivery_date=date.today() + timedelta(days=2),
                place_of_supply_state_code="33",
                customer_gstin=customer_map["CUST-RET-A"].gstin,
                status=SalesOrderStatus.FULFILLED,
                subtotal_paise=750000,
                taxable_amount_paise=750000,
                cgst_paise=18750,
                sgst_paise=18750,
                igst_paise=0,
                total_tax_paise=37500,
                grand_total_paise=787500,
                created_by=user_map["salesA"].id,
                approved_by=user_map["admin"].id,
                notes="Benchmark Retailer A order for 150 packets",
            )
            db.add(so1)
            db.flush()

            so1_item = SalesOrderItem(
                sales_order_id=so1.id,
                product_id=product_map["MUR-200"].id,
                ordered_quantity=Decimal("150.0000"),
                fulfilled_quantity=Decimal("150.0000"),
                unit_price_paise=5000,
                gst_rate=Decimal("5.00"),
                taxable_amount_paise=750000,
                cgst_paise=18750,
                sgst_paise=18750,
                igst_paise=0,
                line_total_paise=787500,
            )
            db.add(so1_item)
            db.flush()

            # Posted GST Tax Invoice
            inv1 = SalesInvoice(
                invoice_number="INV-202611-0001",
                sales_order_id=so1.id,
                customer_id=customer_map["CUST-RET-A"].id,
                invoice_date=date.today(),
                due_date=date.today() + timedelta(days=30),
                place_of_supply_state_code="33",
                seller_gstin="33AAAAA0000A1Z5",
                buyer_gstin=customer_map["CUST-RET-A"].gstin or "33AAACR1234A1Z1",
                status=InvoiceStatus.POSTED,
                taxable_amount_paise=750000,
                cgst_paise=18750,
                sgst_paise=18750,
                igst_paise=0,
                total_tax_paise=37500,
                grand_total_paise=787500,
                amount_paid_paise=400000,  # ₹4,000 paid, ₹3,875 outstanding
                created_by=user_map["admin"].id,
            )
            db.add(inv1)
            db.flush()

            inv1_item = SalesInvoiceItem(
                invoice_id=inv1.id,
                product_id=product_map["MUR-200"].id,
                product_name="Murukku 200g Pouch",
                hsn_code="1905",
                quantity=Decimal("150.0000"),
                unit="pkt",
                unit_price_paise=5000,
                taxable_value_paise=750000,
                gst_rate=Decimal("5.00"),
                cgst_paise=18750,
                sgst_paise=18750,
                igst_paise=0,
                line_total_paise=787500,
            )
            db.add(inv1_item)
            db.flush()

            # Physical Dispatch & Delivery Challan
            disp1 = Dispatch(
                dispatch_number="DSP-202611-0001",
                sales_order_id=so1.id,
                invoice_id=inv1.id,
                customer_id=customer_map["CUST-RET-A"].id,
                dispatch_date=date.today(),
                status=DispatchStatus.DISPATCHED,
                vehicle_number="TN-59-AB-1234",
                transporter_name="Sri Krishna Express",
                tracking_reference="TRK-9876543219",
                notes="Delivered in good condition to Srirangam outlet",
                created_by=user_map["prod"].id,
                dispatched_by=user_map["prod"].id,
                items=[
                    DispatchItem(
                        sales_order_item_id=so1_item.id,
                        product_id=product_map["MUR-200"].id,
                        quantity_dispatched=Decimal("150.0000"),
                        batch_reference="BATCH-MUR-001",
                        unit="pkt",
                    )
                ],
            )
            db.add(disp1)
            db.flush()

            # Book Double-Entry Journal for Sales Invoice
            post_sales_invoice_journal(db, inv1, user_map["admin"].id)

            # -------------------------------------------------------------
            # 9. CUSTOMER PAYMENT & LEDGER
            # -------------------------------------------------------------
            print("\n[9/10] Recording Partial Customer Payment (₹4,000 paid, ₹3,875 due)...")
            pay1 = CustomerPayment(
                payment_number="PAY-202611-0001",
                customer_id=customer_map["CUST-RET-A"].id,
                payment_date=date.today(),
                amount_paise=400000,  # ₹4,000
                payment_mode=PaymentMode.NEFT,
                reference_number="UTR-BENCHMARK-4000",
                bank_name="State Bank of India",
                status=PaymentStatus.CLEARED,
                notes="Partial payment against invoice INV-202611-0001",
                created_by=user_map["salesA"].id,
                allocations=[
                    PaymentAllocation(
                        invoice_id=inv1.id,
                        allocated_amount_paise=400000,
                    )
                ],
            )
            db.add(pay1)
            db.flush()

            # Customer Ledger Entries
            # Entry 1: Invoice Debit
            db.add(CustomerLedgerEntry(
                customer_id=customer_map["CUST-RET-A"].id,
                entry_date=date.today(),
                entry_type="INVOICE",
                reference_document_id=inv1.id,
                reference_number=inv1.invoice_number,
                debit_paise=787500,
                credit_paise=0,
                running_balance_paise=787500,
                description=f"Sales Tax Invoice {inv1.invoice_number}",
            ))
            # Entry 2: Payment Credit
            db.add(CustomerLedgerEntry(
                customer_id=customer_map["CUST-RET-A"].id,
                entry_date=date.today(),
                entry_type="PAYMENT",
                reference_document_id=pay1.id,
                reference_number=pay1.payment_number,
                debit_paise=0,
                credit_paise=400000,
                running_balance_paise=387500,
                description=f"NEFT Payment Receipt {pay1.payment_number}",
            ))

            # Book Double-Entry Journal for Payment
            post_payment_journal(db, pay1, user_map["salesA"].id)

        # -------------------------------------------------------------
        # 10. AUDIT TRAIL LOGS
        # -------------------------------------------------------------
        print("\n[10/10] Logging Audit Events...")
        audit_events = [
            ("SYSTEM_INIT", "SYSTEM", "sys-01", "Database initialized and Chart of Accounts seeded"),
            ("CREATE", "PRODUCT", product_map["MUR-200"].id, "Created SKU Murukku 200g (MUR-200)"),
            ("CREATE", "BOM", bom_map["BOM-MUR-200"].id, "Created Standard Recipe BOM for Murukku 200g"),
            ("POST", "PRODUCTION_RUN", "RUN-202611-0001", "Posted batch run with 238 good packets"),
            ("POST", "INVOICE", "INV-202611-0001", "Generated and posted GST Tax Invoice for Retailer A (₹7,875.00)"),
            ("POST", "DISPATCH", "DSP-202611-0001", "Dispatched 150 packets via Sri Krishna Express (TN-59-AB-1234)"),
            ("POST", "PAYMENT", "PAY-202611-0001", "Recorded NEFT partial payment ₹4,000.00 from Retailer A"),
        ]
        for act, etype, eid, dtl in audit_events:
            db.add(AuditLog(
                user_id=user_map["admin"].id,
                username=user_map["admin"].username,
                role=user_map["admin"].role.value,
                action=act,
                entity_type=etype,
                entity_id=str(eid),
                details=dtl,
                ip_address="127.0.0.1",
            ))

        db.commit()
        print("\n=================================================================")
        print("  SUCCESS: Comprehensive Sample Dataset Populated!")
        print("=================================================================")

    except Exception as e:
        db.rollback()
        print(f"\n[!] Error during dataset population: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    populate_all()
