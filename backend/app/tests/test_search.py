def test_global_search_empty(client):
    response = client.get("/search?q=   ")
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []


def test_global_search_query(client):
    # Search for murukku
    response = client.get("/search?q=murukku")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total" in data
    # At least our products or sample items should match
    print("Found search results:", data["total"])
