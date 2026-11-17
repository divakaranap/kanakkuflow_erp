import pytest
from backend.app.models.user import UserRole


def test_login_success_all_roles(client, seeded_users):
    role_map = {
        "owner": "OWNER",
        "admin": "ADMIN",
        "salesA": "SALESMAN",
        "prod": "PRODUCTION",
        "auditor": "AUDITOR",
    }
    for username, expected_role in role_map.items():
        res = client.post(
            "/auth/login",
            json={"username": username, "password": "demo123"},
        )
        assert res.status_code == 200, f"Login failed for {username}: {res.text}"
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == username
        assert data["user"]["role"] == expected_role


def test_login_invalid_credentials(client, seeded_users):
    res = client.post(
        "/auth/login",
        json={"username": "admin", "password": "wrongpassword"},
    )
    assert res.status_code == 401
    assert "Incorrect username or password" in res.json()["detail"]


def test_get_current_user_me(client, seeded_users):
    login_res = client.post(
        "/auth/login",
        json={"username": "salesA", "password": "demo123"},
    )
    token = login_res.json()["access_token"]

    res = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    user_data = res.json()
    assert user_data["username"] == "salesA"
    assert user_data["role"] == "SALESMAN"


def test_rbac_admin_route_forbidden_for_salesman(client, seeded_users):
    # Log in as salesman
    login_res = client.post(
        "/auth/login",
        json={"username": "salesA", "password": "demo123"},
    )
    token = login_res.json()["access_token"]

    # Try listing users (requires Admin or Owner)
    res = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert "Operation not permitted" in res.json()["detail"]


def test_rbac_admin_route_allowed_for_admin(client, seeded_users):
    # Log in as admin
    login_res = client.post(
        "/auth/login",
        json={"username": "admin", "password": "demo123"},
    )
    token = login_res.json()["access_token"]

    res = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    users = res.json()
    assert len(users) >= 5


def test_change_password(client, seeded_users):
    # Log in as auditor
    login_res = client.post(
        "/auth/login",
        json={"username": "auditor", "password": "demo123"},
    )
    token = login_res.json()["access_token"]

    # Change password
    change_res = client.post(
        "/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"old_password": "demo123", "new_password": "newSecurePassword2026"},
    )
    assert change_res.status_code == 200

    # Old password should now fail
    fail_res = client.post(
        "/auth/login",
        json={"username": "auditor", "password": "demo123"},
    )
    assert fail_res.status_code == 401

    # New password should succeed
    succ_res = client.post(
        "/auth/login",
        json={"username": "auditor", "password": "newSecurePassword2026"},
    )
    assert succ_res.status_code == 200
