def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "KANAKKUFLOW"
    assert "timestamp" in data


def test_api_health_check_vercel_prefix(client):
    """Test /api/health specifically required for Vercel multi-service routing."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "KANAKKUFLOW"


def test_api_docs_and_openapi_compatibility(client):
    """Test /api/docs and /api/openapi.json documentation endpoints."""
    docs_res = client.get("/api/docs")
    assert docs_res.status_code == 200
    assert "swagger" in docs_res.text.lower() or "html" in docs_res.text.lower()

    openapi_res = client.get("/api/openapi.json")
    assert openapi_res.status_code == 200
    schema = openapi_res.json()
    assert "paths" in schema
    assert "/api/health" in schema["paths"]


def test_api_root_endpoint(client):
    """Test /api service root endpoint."""
    response = client.get("/api")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "docs" in data


def test_api_v1_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "KANAKKUFLOW"


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["system"] == "KANAKKUFLOW"
    assert "tagline" in data
