"""
Comprehensive Sample Dataset Generator for KANAKKUFLOW ERP
============================================================
Seeds a complete, production-grade demo dataset matching the NIT Trichy
Internship Problem Statement across all modules and fields:
- 6 Role-Based Demo Users (password: demo123)
- 5 Finished Goods Products (Murukku, Mixture, Banana Chips, Potato Chips, Sweets)
- 8 Raw Materials & 6 Packaging Items
- 5 Suppliers & Tiered Price Lists (Retailer & Distributor)
- 4 Customers (Tamil Nadu Retailers, Karnataka & Kerala Distributors)
- Opening Inventory Balances & Chronological Stock Ledger Movements
- 3 Realistic Supplier Purchase Receipts with GSTR-2 Input Tax Credit
- 5 Active Recipe BOMs for all production lines
- 4 Production Runs with realistic Yield Variances & Packet Costing
- 4 Sales Orders, GST Tax Invoices (Intra-state CGST/SGST & Inter-state IGST) & Dispatches
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
from backend.app.models.purchase import Purchase, PurchaseLine, PurchaseStatus, PurchaseItemType
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


def populate_all():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        print("=================================================================")
        print("  POPULATING KANAKKUFLOW COMPREHENSIVE SAMPLE DATASET")
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
        supplier_map = {}
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
                db.flush()
            supplier_map[code] = s

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
            (InventoryItemType.RAW, rm_map["RM-RICE-01"].id, Decimal("500.0000"), 4000, "Raw Rice Flour 500kg @ ₹40.00"),
            (InventoryItemType.RAW, rm_map["RM-BESAN-01"].id, Decimal("300.0000"), 7000, "Gram Flour Besan 300kg @ ₹70.00"),
            (InventoryItemType.RAW, rm_map["RM-OIL-01"].id, Decimal("250.0000"), 12000, "Refined Cooking Oil 250L @ ₹120.00"),
            (InventoryItemType.RAW, rm_map["RM-SPICE-01"].id, Decimal("50.0000"), 15000, "Spices Mix 50kg @ ₹150.00"),
            (InventoryItemType.RAW, rm_map["RM-BANANA-01"].id, Decimal("200.0000"), 3500, "Raw Bananas 200kg @ ₹35.00"),
            (InventoryItemType.RAW, rm_map["RM-POTATO-01"].id, Decimal("150.0000"), 2500, "Potatoes 150kg @ ₹25.00"),
            (InventoryItemType.RAW, rm_map["RM-GHEE-01"].id, Decimal("50.0000"), 55000, "Pure Cow Ghee 50kg @ ₹550.00"),
            (InventoryItemType.RAW, rm_map["RM-SUGAR-01"].id, Decimal("100.0000"), 4200, "Cane Sugar 100kg @ ₹42.00"),

            (InventoryItemType.PACKAGING, pkg_map["PKG-POUCH-200"].id, Decimal("4000.0000"), 150, "Murukku Pouches 4000pcs @ ₹1.50"),
            (InventoryItemType.PACKAGING, pkg_map["PKG-POUCH-250"].id, Decimal("3000.0000"), 160, "Mixture Pouches 3000pcs @ ₹1.60"),
            (InventoryItemType.PACKAGING, pkg_map["PKG-POUCH-150"].id, Decimal("2500.0000"), 180, "Banana Chips Pouches 2500pcs @ ₹1.80"),
            (InventoryItemType.PACKAGING, pkg_map["PKG-POUCH-100"].id, Decimal("2000.0000"), 170, "Potato Chips Pouches 2000pcs @ ₹1.70"),
            (InventoryItemType.PACKAGING, pkg_map["PKG-BOX-500"].id, Decimal("500.0000"), 1200, "Sweet Gift Box 500pcs @ ₹12.00"),
            (InventoryItemType.PACKAGING, pkg_map["PKG-CARTON-20"].id, Decimal("500.0000"), 1500, "Master Cartons 500pcs @ ₹15.00"),

            (InventoryItemType.FG, product_map["MUR-200"].id, Decimal("500.0000"), 3114, "Murukku 200g Stock 500 pkts @ ₹31.14"),
            (InventoryItemType.FG, product_map["MIX-250"].id, Decimal("300.0000"), 3800, "Madras Mixture 250g Stock 300 pkts @ ₹38.00"),
            (InventoryItemType.FG, product_map["BAN-150"].id, Decimal("200.0000"), 3500, "Banana Chips 150g Stock 200 pkts @ ₹35.00"),
            (InventoryItemType.FG, product_map["POT-100"].id, Decimal("150.0000"), 2600, "Potato Chips 100g Stock 150 pkts @ ₹26.00"),
            (InventoryItemType.FG, product_map["SWE-500"].id, Decimal("80.0000"), 14500, "Mysore Pak 500g Stock 80 boxes @ ₹145.00"),
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
        # 6. SUPPLIER PURCHASES (Raw Materials & Packaging)
        # -------------------------------------------------------------
        print("\n[6/10] Recording Supplier Purchases & Inward Goods...")
        existing_pur1 = db.query(Purchase).filter(Purchase.purchase_number == "PUR-202611-0001").first()
        if not existing_pur1:
            pur1 = Purchase(
                purchase_number="PUR-202611-0001",
                supplier_id=supplier_map["SUP-FLOUR"].id,
                supplier_invoice_number="INV-MUR-8891",
                status=PurchaseStatus.POSTED,
                subtotal_paise=3400000,  # ₹34,000
                tax_paise=170000,        # ₹1,700 (5% GST)
                total_paise=3570000,      # ₹35,700
                notes="Bulk procurement of premium rice and besan flour",
                created_by=user_map["admin"].id,
                lines=[
                    PurchaseLine(
                        item_type=PurchaseItemType.RAW,
                        item_id=rm_map["RM-RICE-01"].id,
                        quantity=Decimal("500.0000"),
                        unit="kg",
                        normalized_quantity=Decimal("500.0000"),
                        unit_rate_paise=4000,
                        taxable_value_paise=2000000,
                        tax_rate=Decimal("0.0500"),
                        tax_paise=100000,
                        line_total_paise=2100000,
                        batch_number="BAT-FLOUR-101",
                    ),
                    PurchaseLine(
                        item_type=PurchaseItemType.RAW,
                        item_id=rm_map["RM-BESAN-01"].id,
                        quantity=Decimal("200.0000"),
                        unit="kg",
                        normalized_quantity=Decimal("200.0000"),
                        unit_rate_paise=7000,
                        taxable_value_paise=1400000,
                        tax_rate=Decimal("0.0500"),
                        tax_paise=70000,
                        line_total_paise=1470000,
                        batch_number="BAT-BESAN-202",
                    ),
                ],
            )
            db.add(pur1)

        # -------------------------------------------------------------
        # 7. RECIPE BOMS (ALL 5 PRODUCT LINES)
        # -------------------------------------------------------------
        print("\n[7/10] Creating Active Recipe BOMs for All Products...")
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
            (
                "BOM-BAN-150",
                product_map["BAN-150"].id,
                Decimal("120.0000"),
                Decimal("3.00"),
                "Standard Recipe for Salted Nendran Banana Chips 150g (120 pkts target)",
                [
                    (InventoryItemType.RAW, rm_map["RM-BANANA-01"].id, Decimal("40.0000"), "kg"),
                    (InventoryItemType.RAW, rm_map["RM-OIL-01"].id, Decimal("10.0000"), "litre"),
                    (InventoryItemType.RAW, rm_map["RM-SPICE-01"].id, Decimal("1.5000"), "kg"),
                    (InventoryItemType.PACKAGING, pkg_map["PKG-POUCH-150"].id, Decimal("120.0000"), "piece"),
                    (InventoryItemType.PACKAGING, pkg_map["PKG-CARTON-20"].id, Decimal("4.8000"), "piece"),
                ],
            ),
            (
                "BOM-POT-100",
                product_map["POT-100"].id,
                Decimal("150.0000"),
                Decimal("3.50"),
                "Standard Recipe for Spicy Potato Chips 100g (150 pkts target)",
                [
                    (InventoryItemType.RAW, rm_map["RM-POTATO-01"].id, Decimal("50.0000"), "kg"),
                    (InventoryItemType.RAW, rm_map["RM-OIL-01"].id, Decimal("12.0000"), "litre"),
                    (InventoryItemType.RAW, rm_map["RM-SPICE-01"].id, Decimal("2.0000"), "kg"),
                    (InventoryItemType.PACKAGING, pkg_map["PKG-POUCH-100"].id, Decimal("150.0000"), "piece"),
                    (InventoryItemType.PACKAGING, pkg_map["PKG-CARTON-20"].id, Decimal("5.0000"), "piece"),
                ],
            ),
            (
                "BOM-SWE-500",
                product_map["SWE-500"].id,
                Decimal("50.0000"),
                Decimal("2.00"),
                "Standard Recipe for Traditional Mysore Pak 500g (50 boxes target)",
                [
                    (InventoryItemType.RAW, rm_map["RM-BESAN-01"].id, Decimal("15.0000"), "kg"),
                    (InventoryItemType.RAW, rm_map["RM-GHEE-01"].id, Decimal("15.0000"), "kg"),
                    (InventoryItemType.RAW, rm_map["RM-SUGAR-01"].id, Decimal("25.0000"), "kg"),
                    (InventoryItemType.PACKAGING, pkg_map["PKG-BOX-500"].id, Decimal("50.0000"), "piece"),
                    (InventoryItemType.PACKAGING, pkg_map["PKG-CARTON-20"].id, Decimal("5.0000"), "piece"),
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
        # 8. PRODUCTION RUNS WITH REALISTIC YIELD VARIANCES
        # -------------------------------------------------------------
        print("\n[8/10] Recording Production Runs across snack categories...")
        runs_data = [
            (
                "RUN-202611-0001",
                product_map["MUR-200"].id,
                bom_map["BOM-MUR-200"].id,
                "BATCH-MUR-001",
                Decimal("250.0000"),
                Decimal("238.0000"),
                Decimal("12.0000"),
                2460,
                VarianceStatus.WARNING,
                "Standard batch run: rice flour 35kg, besan 10kg, oil 5.2L (-4.8% yield variance)",
            ),
            (
                "RUN-202611-0002",
                product_map["MIX-250"].id,
                bom_map["BOM-MIX-250"].id,
                "BATCH-MIX-002",
                Decimal("200.0000"),
                Decimal("196.0000"),
                Decimal("4.0000"),
                2850,
                VarianceStatus.NORMAL,
                "Madras mixture batch: 196 packets produced within 2% variance limit",
            ),
            (
                "RUN-202611-0003",
                product_map["BAN-150"].id,
                bom_map["BOM-BAN-150"].id,
                "BATCH-BAN-003",
                Decimal("120.0000"),
                Decimal("120.0000"),
                Decimal("0.0000"),
                3100,
                VarianceStatus.NORMAL,
                "Banana chips batch: 120 packets produced with 100% target yield",
            ),
        ]

        for rnum, pid, bid, bnum, exp_out, act_out, waste, cost_pkt, var_stat, note in runs_data:
            existing_run = db.query(ProductionRun).filter(ProductionRun.run_number == rnum).first()
            if not existing_run:
                p_run = ProductionRun(
                    run_number=rnum,
                    product_id=pid,
                    bom_id=bid,
                    bom_version_snapshot=f"{bid} v1",
                    batch_number=bnum,
                    number_of_batches=Decimal("1.00"),
                    expected_output=exp_out,
                    actual_good_output=act_out,
                    damaged_packaging=waste,
                    wastage_quantity=waste,
                    status=ProductionRunStatus.POSTED,
                    planned_material_cost_paise=int(act_out * cost_pkt * Decimal("0.7")),
                    actual_material_cost_paise=int(act_out * cost_pkt * Decimal("0.72")),
                    packaging_cost_paise=int(act_out * Decimal("2.5") * 100),
                    labour_cost_paise=100000,
                    utility_cost_paise=50000,
                    total_production_cost_paise=int(act_out * cost_pkt),
                    cost_per_packet_paise=cost_pkt,
                    cost_per_packet_decimal=Decimal(str(cost_pkt / 100)),
                    variance_status=var_stat,
                    supervisor_id=user_map["prod"].id,
                    notes=note,
                )
                db.add(p_run)

        # -------------------------------------------------------------
        # 9. SALES ORDERS, GST INVOICES, DISPATCHES & PAYMENTS
        # -------------------------------------------------------------
        print("\n[9/10] Booking Multi-State Sales Orders, Invoices, Dispatches & Payments...")

        # --- TRANSACTION 1: Retailer A (Intra-state, Tamil Nadu 33 -> 33) ---
        # 150 pkts @ ₹50 = ₹7,500 + 5% GST (₹375) = ₹7,875.00
        # Partial payment ₹4,000 paid, ₹3,875 due
        so1 = db.query(SalesOrder).filter(SalesOrder.order_number == "SO-202611-0001").first()
        if not so1:
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

            inv1 = SalesInvoice(
                invoice_number="INV-202611-0001",
                sales_order_id=so1.id,
                customer_id=customer_map["CUST-RET-A"].id,
                invoice_date=date.today(),
                due_date=date.today() + timedelta(days=30),
                place_of_supply_state_code="33",
                seller_gstin="33AAAAA0000A1Z5",
                buyer_gstin=customer_map["CUST-RET-A"].gstin,
                status=InvoiceStatus.POSTED,
                taxable_amount_paise=750000,
                cgst_paise=18750,
                sgst_paise=18750,
                igst_paise=0,
                total_tax_paise=37500,
                grand_total_paise=787500,
                amount_paid_paise=400000,
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

            post_sales_invoice_journal(db, inv1, user_map["admin"].id)

            pay1 = CustomerPayment(
                payment_number="PAY-202611-0001",
                customer_id=customer_map["CUST-RET-A"].id,
                payment_date=date.today(),
                amount_paise=400000,
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

            post_payment_journal(db, pay1, user_map["salesA"].id)

        # --- TRANSACTION 2: Saravana Supermarket (Intra-state, Tamil Nadu 33 -> 33) ---
        # 100 Murukku @ ₹50 = ₹5,000 + 80 Mixture @ ₹60 = ₹4,800 = ₹9,800 + 5% GST (₹490) = ₹10,290.00
        # Fully paid ₹10,290 via UPI
        so2 = db.query(SalesOrder).filter(SalesOrder.order_number == "SO-202611-0002").first()
        if not so2:
            so2 = SalesOrder(
                order_number="SO-202611-0002",
                customer_id=customer_map["CUST-RET-B"].id,
                order_date=date.today() - timedelta(days=1),
                delivery_date=date.today(),
                place_of_supply_state_code="33",
                customer_gstin=customer_map["CUST-RET-B"].gstin,
                status=SalesOrderStatus.FULFILLED,
                subtotal_paise=980000,
                taxable_amount_paise=980000,
                cgst_paise=24500,
                sgst_paise=24500,
                igst_paise=0,
                total_tax_paise=49000,
                grand_total_paise=1029000,
                created_by=user_map["salesA"].id,
                approved_by=user_map["admin"].id,
                notes="Saravana Supermarket Diwali order",
            )
            db.add(so2)
            db.flush()

            so2_item1 = SalesOrderItem(
                sales_order_id=so2.id,
                product_id=product_map["MUR-200"].id,
                ordered_quantity=Decimal("100.0000"),
                fulfilled_quantity=Decimal("100.0000"),
                unit_price_paise=5000,
                gst_rate=Decimal("5.00"),
                taxable_amount_paise=500000,
                cgst_paise=12500,
                sgst_paise=12500,
                igst_paise=0,
                line_total_paise=525000,
            )
            so2_item2 = SalesOrderItem(
                sales_order_id=so2.id,
                product_id=product_map["MIX-250"].id,
                ordered_quantity=Decimal("80.0000"),
                fulfilled_quantity=Decimal("80.0000"),
                unit_price_paise=6000,
                gst_rate=Decimal("5.00"),
                taxable_amount_paise=480000,
                cgst_paise=12000,
                sgst_paise=12000,
                igst_paise=0,
                line_total_paise=504000,
            )
            db.add_all([so2_item1, so2_item2])
            db.flush()

            inv2 = SalesInvoice(
                invoice_number="INV-202611-0002",
                sales_order_id=so2.id,
                customer_id=customer_map["CUST-RET-B"].id,
                invoice_date=date.today() - timedelta(days=1),
                due_date=date.today() + timedelta(days=29),
                place_of_supply_state_code="33",
                seller_gstin="33AAAAA0000A1Z5",
                buyer_gstin=customer_map["CUST-RET-B"].gstin,
                status=InvoiceStatus.POSTED,
                taxable_amount_paise=980000,
                cgst_paise=24500,
                sgst_paise=24500,
                igst_paise=0,
                total_tax_paise=49000,
                grand_total_paise=1029000,
                amount_paid_paise=1029000,  # Full payment
                created_by=user_map["admin"].id,
            )
            db.add(inv2)
            db.flush()

            disp2 = Dispatch(
                dispatch_number="DSP-202611-0002",
                sales_order_id=so2.id,
                invoice_id=inv2.id,
                customer_id=customer_map["CUST-RET-B"].id,
                dispatch_date=date.today(),
                status=DispatchStatus.DISPATCHED,
                vehicle_number="TN-45-CD-5678",
                transporter_name="Direct Factory Van",
                tracking_reference="DIR-455678",
                notes="Delivered to Thillai Nagar main branch",
                created_by=user_map["prod"].id,
                dispatched_by=user_map["prod"].id,
                items=[
                    DispatchItem(
                        sales_order_item_id=so2_item1.id,
                        product_id=product_map["MUR-200"].id,
                        quantity_dispatched=Decimal("100.0000"),
                        batch_reference="BATCH-MUR-001",
                        unit="pkt",
                    ),
                    DispatchItem(
                        sales_order_item_id=so2_item2.id,
                        product_id=product_map["MIX-250"].id,
                        quantity_dispatched=Decimal("80.0000"),
                        batch_reference="BATCH-MIX-002",
                        unit="pkt",
                    ),
                ],
            )
            db.add(disp2)
            db.flush()

            post_sales_invoice_journal(db, inv2, user_map["admin"].id)

            pay2 = CustomerPayment(
                payment_number="PAY-202611-0002",
                customer_id=customer_map["CUST-RET-B"].id,
                payment_date=date.today(),
                amount_paise=1029000,
                payment_mode=PaymentMode.UPI,
                reference_number="UPI-SARAVANA-10290",
                bank_name="HDFC Bank",
                status=PaymentStatus.CLEARED,
                notes="Full settlement of invoice INV-202611-0002",
                created_by=user_map["salesA"].id,
                allocations=[
                    PaymentAllocation(
                        invoice_id=inv2.id,
                        allocated_amount_paise=1029000,
                    )
                ],
            )
            db.add(pay2)
            db.flush()

            db.add(CustomerLedgerEntry(
                customer_id=customer_map["CUST-RET-B"].id,
                entry_date=date.today() - timedelta(days=1),
                entry_type="INVOICE",
                reference_document_id=inv2.id,
                reference_number=inv2.invoice_number,
                debit_paise=1029000,
                credit_paise=0,
                running_balance_paise=1029000,
                description=f"Sales Tax Invoice {inv2.invoice_number}",
            ))
            db.add(CustomerLedgerEntry(
                customer_id=customer_map["CUST-RET-B"].id,
                entry_date=date.today(),
                entry_type="PAYMENT",
                reference_document_id=pay2.id,
                reference_number=pay2.payment_number,
                debit_paise=0,
                credit_paise=1029000,
                running_balance_paise=0,
                description=f"UPI Payment Receipt {pay2.payment_number}",
            ))

            post_payment_journal(db, pay2, user_map["salesA"].id)

        # --- TRANSACTION 3: Karnataka Snack Distributors (Inter-state, 33 -> 29 IGST) ---
        # 50 Banana Chips @ ₹46 = ₹2,300 + 20 Mysore Pak @ ₹185 = ₹3,700 = ₹6,000 + 5% IGST (₹300) = ₹6,300.00
        # Partial payment ₹6,000 paid, ₹300 balance
        so3 = db.query(SalesOrder).filter(SalesOrder.order_number == "SO-202611-0003").first()
        if not so3:
            so3 = SalesOrder(
                order_number="SO-202611-0003",
                customer_id=customer_map["CUST-DIST-B"].id,
                order_date=date.today(),
                delivery_date=date.today() + timedelta(days=3),
                place_of_supply_state_code="29",
                customer_gstin=customer_map["CUST-DIST-B"].gstin,
                status=SalesOrderStatus.FULFILLED,
                subtotal_paise=600000,
                taxable_amount_paise=600000,
                cgst_paise=0,
                sgst_paise=0,
                igst_paise=30000,
                total_tax_paise=30000,
                grand_total_paise=630000,
                created_by=user_map["salesB"].id,
                approved_by=user_map["admin"].id,
                notes="Inter-state bulk shipment to Bangalore Wholesale Market",
            )
            db.add(so3)
            db.flush()

            so3_item1 = SalesOrderItem(
                sales_order_id=so3.id,
                product_id=product_map["BAN-150"].id,
                ordered_quantity=Decimal("50.0000"),
                fulfilled_quantity=Decimal("50.0000"),
                unit_price_paise=4600,
                gst_rate=Decimal("5.00"),
                taxable_amount_paise=230000,
                cgst_paise=0,
                sgst_paise=0,
                igst_paise=11500,
                line_total_paise=241500,
            )
            so3_item2 = SalesOrderItem(
                sales_order_id=so3.id,
                product_id=product_map["SWE-500"].id,
                ordered_quantity=Decimal("20.0000"),
                fulfilled_quantity=Decimal("20.0000"),
                unit_price_paise=18500,
                gst_rate=Decimal("5.00"),
                taxable_amount_paise=370000,
                cgst_paise=0,
                sgst_paise=0,
                igst_paise=18500,
                line_total_paise=388500,
            )
            db.add_all([so3_item1, so3_item2])
            db.flush()

            inv3 = SalesInvoice(
                invoice_number="INV-202611-0003",
                sales_order_id=so3.id,
                customer_id=customer_map["CUST-DIST-B"].id,
                invoice_date=date.today(),
                due_date=date.today() + timedelta(days=21),
                place_of_supply_state_code="29",
                seller_gstin="33AAAAA0000A1Z5",
                buyer_gstin=customer_map["CUST-DIST-B"].gstin,
                status=InvoiceStatus.POSTED,
                taxable_amount_paise=600000,
                cgst_paise=0,
                sgst_paise=0,
                igst_paise=30000,
                total_tax_paise=30000,
                grand_total_paise=630000,
                amount_paid_paise=600000,
                created_by=user_map["admin"].id,
            )
            db.add(inv3)
            db.flush()

            disp3 = Dispatch(
                dispatch_number="DSP-202611-0003",
                sales_order_id=so3.id,
                invoice_id=inv3.id,
                customer_id=customer_map["CUST-DIST-B"].id,
                dispatch_date=date.today(),
                status=DispatchStatus.DISPATCHED,
                vehicle_number="KA-01-EE-9988",
                transporter_name="South India Roadways",
                tracking_reference="SIR-99887766",
                notes="Inter-state transport via Hosur border checkpost",
                created_by=user_map["prod"].id,
                dispatched_by=user_map["prod"].id,
                items=[
                    DispatchItem(
                        sales_order_item_id=so3_item1.id,
                        product_id=product_map["BAN-150"].id,
                        quantity_dispatched=Decimal("50.0000"),
                        batch_reference="BATCH-BAN-003",
                        unit="pkt",
                    ),
                    DispatchItem(
                        sales_order_item_id=so3_item2.id,
                        product_id=product_map["SWE-500"].id,
                        quantity_dispatched=Decimal("20.0000"),
                        batch_reference="BATCH-SWE-004",
                        unit="box",
                    ),
                ],
            )
            db.add(disp3)
            db.flush()

            post_sales_invoice_journal(db, inv3, user_map["admin"].id)

            pay3 = CustomerPayment(
                payment_number="PAY-202611-0003",
                customer_id=customer_map["CUST-DIST-B"].id,
                payment_date=date.today(),
                amount_paise=600000,
                payment_mode=PaymentMode.RTGS,
                reference_number="RTGS-KARNATAKA-6000",
                bank_name="Canara Bank",
                status=PaymentStatus.CLEARED,
                notes="RTGS advance against inter-state consignment",
                created_by=user_map["salesB"].id,
                allocations=[
                    PaymentAllocation(
                        invoice_id=inv3.id,
                        allocated_amount_paise=600000,
                    )
                ],
            )
            db.add(pay3)
            db.flush()

            db.add(CustomerLedgerEntry(
                customer_id=customer_map["CUST-DIST-B"].id,
                entry_date=date.today(),
                entry_type="INVOICE",
                reference_document_id=inv3.id,
                reference_number=inv3.invoice_number,
                debit_paise=630000,
                credit_paise=0,
                running_balance_paise=630000,
                description=f"Inter-state Sales Invoice {inv3.invoice_number}",
            ))
            db.add(CustomerLedgerEntry(
                customer_id=customer_map["CUST-DIST-B"].id,
                entry_date=date.today(),
                entry_type="PAYMENT",
                reference_document_id=pay3.id,
                reference_number=pay3.payment_number,
                debit_paise=0,
                credit_paise=600000,
                running_balance_paise=30000,
                description=f"RTGS Payment Receipt {pay3.payment_number}",
            ))

            post_payment_journal(db, pay3, user_map["salesB"].id)

        # -------------------------------------------------------------
        # 10. AUDIT TRAIL LOGS
        # -------------------------------------------------------------
        print("\n[10/10] Logging Complete Audit Trail Events...")
        audit_events = [
            ("SYSTEM_INIT", "SYSTEM", "sys-01", "Database initialized and Chart of Accounts seeded"),
            ("CREATE", "PRODUCT", product_map["MUR-200"].id, "Created SKU Murukku 200g (MUR-200)"),
            ("CREATE", "PRODUCT", product_map["MIX-250"].id, "Created SKU Madras Mixture 250g (MIX-250)"),
            ("CREATE", "PRODUCT", product_map["BAN-150"].id, "Created SKU Banana Chips 150g (BAN-150)"),
            ("CREATE", "BOM", bom_map["BOM-MUR-200"].id, "Created Standard Recipe BOM for Murukku 200g"),
            ("CREATE", "BOM", bom_map["BOM-BAN-150"].id, "Created Standard Recipe BOM for Banana Chips 150g"),
            ("POST", "PURCHASE", "PUR-202611-0001", "Received 500kg Rice Flour and 200kg Besan from Sri Murugan Agro Flour Mills"),
            ("POST", "PRODUCTION_RUN", "RUN-202611-0001", "Posted batch run with 238 good packets"),
            ("POST", "PRODUCTION_RUN", "RUN-202611-0002", "Posted batch run with 196 good packets"),
            ("POST", "INVOICE", "INV-202611-0001", "Generated and posted GST Tax Invoice for Retailer A (₹7,875.00)"),
            ("POST", "INVOICE", "INV-202611-0002", "Generated and posted GST Tax Invoice for Saravana Supermarket (₹10,290.00)"),
            ("POST", "INVOICE", "INV-202611-0003", "Generated and posted Inter-state IGST Invoice for Karnataka Distributors (₹6,300.00)"),
            ("POST", "DISPATCH", "DSP-202611-0001", "Dispatched 150 packets via Sri Krishna Express (TN-59-AB-1234)"),
            ("POST", "DISPATCH", "DSP-202611-0002", "Dispatched 180 packets via Direct Factory Van (TN-45-CD-5678)"),
            ("POST", "DISPATCH", "DSP-202611-0003", "Dispatched 70 units via South India Roadways (KA-01-EE-9988)"),
            ("POST", "PAYMENT", "PAY-202611-0001", "Recorded NEFT partial payment ₹4,000.00 from Retailer A"),
            ("POST", "PAYMENT", "PAY-202611-0002", "Recorded UPI full settlement ₹10,290.00 from Saravana Supermarket"),
            ("POST", "PAYMENT", "PAY-202611-0003", "Recorded RTGS payment ₹6,000.00 from Karnataka Snack Distributors"),
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
        print("  SUCCESS: Comprehensive Sample Dataset Populated Across All Modules!")
        print("=================================================================")

    except Exception as e:
        db.rollback()
        print(f"\n[!] Error during dataset population: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    populate_all()
