from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.database import get_db
from backend.app.models.product import Product
from backend.app.models.customer import Customer
from backend.app.models.raw_material import RawMaterial
from backend.app.models.sales import SalesOrder, SalesInvoice
from backend.app.models.production import ProductionRun
from backend.app.models.dispatch import Dispatch

router = APIRouter(tags=["Search"])


@router.get("/search")
def global_search(
    q: str = Query(..., min_length=1, description="Search term for products, customers, orders, invoices, batches"),
    db: Session = Depends(get_db),
):
    query_str = q.strip()
    if not query_str:
        return {"query": q, "total": 0, "results": []}

    pattern = f"%{query_str}%"
    results = []

    # 1. Search Products
    products = (
        db.query(Product)
        .filter(
            or_(
                Product.product_name.ilike(pattern),
                Product.sku.ilike(pattern),
                Product.category.ilike(pattern),
            )
        )
        .limit(6)
        .all()
    )
    for p in products:
        category_str = p.category.value if hasattr(p.category, "value") else str(p.category)
        results.append({
            "id": p.id,
            "type": "product",
            "title": p.product_name,
            "subtitle": f"SKU: {p.sku} • ₹{p.selling_price_paise / 100:.2f} • {category_str}",
            "view": "masters",
            "tab": "products",
            "badge": "Product",
        })

    # 2. Search Customers
    customers = (
        db.query(Customer)
        .filter(
            or_(
                Customer.customer_name.ilike(pattern),
                Customer.customer_code.ilike(pattern),
                Customer.phone.ilike(pattern),
                Customer.city.ilike(pattern),
            )
        )
        .limit(5)
        .all()
    )
    for c in customers:
        type_str = c.customer_type.value if hasattr(c.customer_type, "value") else str(c.customer_type)
        results.append({
            "id": c.id,
            "type": "customer",
            "title": c.customer_name,
            "subtitle": f"Code: {c.customer_code} • {type_str} • {c.city}, {c.state}",
            "view": "masters",
            "tab": "customers",
            "badge": "Customer",
        })

    # 3. Search Sales Orders
    orders = (
        db.query(SalesOrder)
        .filter(
            or_(
                SalesOrder.order_number.ilike(pattern),
                SalesOrder.customer_gstin.ilike(pattern),
            )
        )
        .limit(5)
        .all()
    )
    for so in orders:
        status_str = so.status.value if hasattr(so.status, "value") else str(so.status)
        results.append({
            "id": so.id,
            "type": "order",
            "title": so.order_number,
            "subtitle": f"Date: {so.order_date} • Total: ₹{so.grand_total_paise / 100:.2f} • {status_str}",
            "view": "sales",
            "tab": "orders",
            "badge": "Sales Order",
        })

    # 4. Search Sales Invoices
    invoices = (
        db.query(SalesInvoice)
        .filter(SalesInvoice.invoice_number.ilike(pattern))
        .limit(5)
        .all()
    )
    for inv in invoices:
        inv_status_str = inv.status.value if hasattr(inv.status, "value") else str(inv.status)
        results.append({
            "id": inv.id,
            "type": "invoice",
            "title": inv.invoice_number,
            "subtitle": f"Total: ₹{inv.grand_total_paise / 100:.2f} • {inv_status_str}",
            "view": "sales",
            "tab": "invoices",
            "badge": "Invoice",
        })

    # 5. Search Production Runs
    runs = (
        db.query(ProductionRun)
        .filter(
            or_(
                ProductionRun.run_number.ilike(pattern),
                ProductionRun.batch_number.ilike(pattern),
            )
        )
        .limit(5)
        .all()
    )
    for pr in runs:
        pr_status_str = pr.status.value if hasattr(pr.status, "value") else str(pr.status)
        results.append({
            "id": pr.id,
            "type": "production",
            "title": pr.batch_number,
            "subtitle": f"Run: {pr.run_number} • {pr_status_str}",
            "view": "production",
            "tab": "history",
            "badge": "Batch",
        })

    # 6. Search Dispatches
    dispatches = (
        db.query(Dispatch)
        .filter(
            or_(
                Dispatch.dispatch_number.ilike(pattern),
                Dispatch.vehicle_number.ilike(pattern),
                Dispatch.transporter_name.ilike(pattern),
            )
        )
        .limit(5)
        .all()
    )
    for d in dispatches:
        d_status_str = d.status.value if hasattr(d.status, "value") else str(d.status)
        results.append({
            "id": d.id,
            "type": "dispatch",
            "title": d.dispatch_number,
            "subtitle": f"Vehicle: {d.vehicle_number or 'N/A'} • {d_status_str}",
            "view": "dispatch",
            "tab": "active",
            "badge": "Dispatch",
        })

    # 7. Search Raw Materials
    raw_materials = (
        db.query(RawMaterial)
        .filter(
            or_(
                RawMaterial.material_name.ilike(pattern),
                RawMaterial.material_code.ilike(pattern),
            )
        )
        .limit(5)
        .all()
    )
    for rm in raw_materials:
        results.append({
            "id": rm.id,
            "type": "raw_material",
            "title": rm.material_name,
            "subtitle": f"Code: {rm.material_code} • Category: {rm.category}",
            "view": "masters",
            "tab": "raw_materials",
            "badge": "Raw Material",
        })

    return {
        "query": q,
        "total": len(results),
        "results": results,
    }
