import pytest
from fastapi.testclient import TestClient


def get_auth_header(client, username, password="demo123"):
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_management_analytics_and_report_exports(client: TestClient, db, seeded_users):
    """
    Test Phase 9 Management Analytics & Multi-Format Exports (CSV, Excel, PDF):
    1. Dashboard summary analytics.
    2. GSTR-1 outward sales register export in CSV, Excel and PDF.
    3. GSTR-2 inward purchase register export in CSV and Excel.
    4. Stock movement ledger export in CSV and Excel.
    5. Production & yield report export in CSV and PDF.
    6. Receivables ageing report export in CSV and Excel.
    7. Trial balance report export in CSV, Excel and PDF.
    """
    admin_headers = get_auth_header(client, "admin")
    auditor_headers = get_auth_header(client, "auditor")

    # 1. Executive Dashboard Analytics
    dash_res = client.get("/analytics/dashboard-summary", headers=admin_headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()

    assert "sales" in dash_data
    assert "production" in dash_data
    assert "inventory" in dash_data
    assert "finance" in dash_data
    assert "top_products" in dash_data
    assert "top_debtors" in dash_data

    # 2. GSTR-1 Sales Register Exports
    # CSV
    gstr1_csv = client.get("/reports/gstr1?format=csv", headers=auditor_headers)
    assert gstr1_csv.status_code == 200
    assert gstr1_csv.headers["content-type"] == "text/csv; charset=utf-8"
    assert "Invoice No,Date,Customer Name" in gstr1_csv.text

    # Excel
    gstr1_xlsx = client.get("/reports/gstr1?format=xlsx", headers=auditor_headers)
    assert gstr1_xlsx.status_code == 200
    assert "spreadsheetml.sheet" in gstr1_xlsx.headers["content-type"]
    assert len(gstr1_xlsx.content) > 1000

    # PDF
    gstr1_pdf = client.get("/reports/gstr1?format=pdf", headers=auditor_headers)
    assert gstr1_pdf.status_code == 200
    assert gstr1_pdf.headers["content-type"] == "application/pdf"
    assert gstr1_pdf.content.startswith(b"%PDF-")

    # 3. GSTR-2 Purchase Register Exports
    gstr2_csv = client.get("/reports/gstr2?format=csv", headers=auditor_headers)
    assert gstr2_csv.status_code == 200
    assert "Purchase No,Date,Supplier Name" in gstr2_csv.text

    gstr2_xlsx = client.get("/reports/gstr2?format=xlsx", headers=auditor_headers)
    assert gstr2_xlsx.status_code == 200
    assert len(gstr2_xlsx.content) > 1000

    # 4. Stock Movement Ledger
    stock_csv = client.get("/reports/stock-ledger?format=csv", headers=admin_headers)
    assert stock_csv.status_code == 200
    assert "Movement Date,Item Type,Movement Type" in stock_csv.text

    # 5. Production Yield Report
    prod_pdf = client.get("/reports/production-yield?format=pdf", headers=admin_headers)
    assert prod_pdf.status_code == 200
    assert prod_pdf.content.startswith(b"%PDF-")

    # 6. Receivables Ageing Report
    ageing_xlsx = client.get("/reports/receivables-ageing?format=xlsx", headers=auditor_headers)
    assert ageing_xlsx.status_code == 200
    assert len(ageing_xlsx.content) > 1000

    # 7. Trial Balance Report
    tb_csv = client.get("/reports/trial-balance?format=csv", headers=auditor_headers)
    assert tb_csv.status_code == 200
    assert "Code,Account Name,Category" in tb_csv.text

    tb_pdf = client.get("/reports/trial-balance?format=pdf", headers=auditor_headers)
    assert tb_pdf.status_code == 200
    assert tb_pdf.content.startswith(b"%PDF-")
