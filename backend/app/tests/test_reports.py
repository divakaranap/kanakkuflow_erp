import pytest
from datetime import date, timedelta
from io import BytesIO
import openpyxl
from fastapi.testclient import TestClient


def get_auth_header(client, username, password="demo123"):
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_analytics_summary_and_role_kpis(client: TestClient, db, seeded_users):
    """Test dashboard summary with role-based KPI customisation."""
    admin_headers = get_auth_header(client, "admin")
    owner_headers = get_auth_header(client, "owner")
    sales_headers = get_auth_header(client, "salesA")
    prod_headers = get_auth_header(client, "prod")
    auditor_headers = get_auth_header(client, "auditor")

    for h, role in [
        (admin_headers, "ADMIN"),
        (owner_headers, "OWNER"),
        (sales_headers, "SALESMAN"),
        (prod_headers, "PRODUCTION"),
        (auditor_headers, "AUDITOR"),
    ]:
        res = client.get("/analytics/dashboard-summary", headers=h)
        assert res.status_code == 200
        data = res.json()
        assert "sales" in data
        assert "production" in data
        assert "inventory" in data
        assert "finance" in data
        assert "role_kpis" in data
        assert "card1" in data["role_kpis"]
        assert "card2" in data["role_kpis"]
        assert "card3" in data["role_kpis"]
        assert "card4" in data["role_kpis"]


def test_all_six_reports_across_csv_excel_pdf(client: TestClient, db, seeded_users):
    """
    Test every one of the 6 primary reports in all 3 formats (CSV, XLSX, PDF)
    along with JSON preview and date filtering.
    """
    admin_headers = get_auth_header(client, "admin")
    auditor_headers = get_auth_header(client, "auditor")

    today = date.today()
    from_date = (today - timedelta(days=30)).isoformat()
    to_date = today.isoformat()
    as_of_date = today.isoformat()

    report_endpoints = [
        ("/reports/gstr1", "GSTR1", {"from_date": from_date, "to_date": to_date}),
        ("/reports/purchase-register", "Purchase", {"from_date": from_date, "to_date": to_date}),
        ("/reports/stock-movements", "Stock", {"as_of_date": as_of_date}),
        ("/reports/production-variance", "Production", {"from_date": from_date, "to_date": to_date}),
        ("/reports/receivables-ageing", "Receivables", {"as_of_date": as_of_date}),
        ("/reports/trial-balance", "Trial_Balance", {"as_of_date": as_of_date}),
    ]

    for endpoint, prefix, params in report_endpoints:
        # 1. JSON Preview
        json_res = client.get(endpoint, params={**params, "format": "json"}, headers=auditor_headers)
        assert json_res.status_code == 200
        json_data = json_res.json()
        assert "headers" in json_data
        assert "rows" in json_data
        assert isinstance(json_data["headers"], list)

        # 2. CSV Export
        csv_res = client.get(endpoint, params={**params, "format": "csv"}, headers=auditor_headers)
        assert csv_res.status_code == 200
        assert "text/csv" in csv_res.headers["content-type"]
        assert "Content-Disposition" in csv_res.headers
        assert ".csv" in csv_res.headers["Content-Disposition"]
        assert len(csv_res.text) > 0

        # 3. Excel Export
        xlsx_res = client.get(endpoint, params={**params, "format": "xlsx"}, headers=auditor_headers)
        assert xlsx_res.status_code == 200
        assert "openxmlformats" in xlsx_res.headers["content-type"]
        assert "Content-Disposition" in xlsx_res.headers
        assert ".xlsx" in xlsx_res.headers["Content-Disposition"]
        # Verify valid Excel workbook
        wb = openpyxl.load_workbook(BytesIO(xlsx_res.content))
        assert len(wb.sheetnames) > 0

        # 4. PDF Export
        pdf_res = client.get(endpoint, params={**params, "format": "pdf"}, headers=auditor_headers)
        assert pdf_res.status_code == 200
        assert pdf_res.headers["content-type"] == "application/pdf"
        assert "Content-Disposition" in pdf_res.headers
        assert ".pdf" in pdf_res.headers["Content-Disposition"]
        assert pdf_res.content.startswith(b"%PDF-")


def test_report_date_validation_and_rbac(client: TestClient, db, seeded_users):
    """Test date validation (from > to) and role authorization rules."""
    auditor_headers = get_auth_header(client, "auditor")
    sales_headers = get_auth_header(client, "salesA")

    # Invalid date range: from_date > to_date
    invalid_res = client.get(
        "/reports/gstr1?from_date=2026-11-20&to_date=2026-11-10",
        headers=auditor_headers,
    )
    assert invalid_res.status_code == 400
    assert "cannot be later" in invalid_res.json()["detail"]

    # Role permission: salesman cannot access purchase register or trial balance
    p_res = client.get("/reports/purchase-register", headers=sales_headers)
    assert p_res.status_code == 403

    tb_res = client.get("/reports/trial-balance", headers=sales_headers)
    assert tb_res.status_code == 403

    # But salesman CAN access receivables ageing
    ageing_res = client.get("/reports/receivables-ageing?format=json", headers=sales_headers)
    assert ageing_res.status_code == 200
