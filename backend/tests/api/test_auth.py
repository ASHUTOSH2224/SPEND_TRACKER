from sqlalchemy import select

from app.core.security import verify_password
from app.models.user import User


def test_signup_creates_user_and_returns_token(client, db_session) -> None:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "User@example.com",
            "password": "strong-password",
            "full_name": "Ashutosh",
        },
    )

    assert response.status_code == 201

    payload = response.json()
    assert payload["error"] is None
    assert payload["meta"] == {}
    assert payload["data"]["user"]["email"] == "user@example.com"
    assert payload["data"]["user"]["full_name"] == "Ashutosh"
    assert isinstance(payload["data"]["token"], str)
    assert payload["data"]["token"]

    user = db_session.scalar(select(User).where(User.email == "user@example.com"))
    assert user is not None
    assert user.password_hash != "strong-password"
    assert verify_password("strong-password", user.password_hash)


def test_login_returns_user_and_token(client) -> None:
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user@example.com",
            "password": "strong-password",
            "full_name": "Ashutosh",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "strong-password"},
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["error"] is None
    assert payload["meta"] == {}
    assert payload["data"]["user"]["email"] == "user@example.com"
    assert isinstance(payload["data"]["token"], str)
    assert payload["data"]["token"]


def test_login_rejects_invalid_credentials(client) -> None:
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user@example.com",
            "password": "strong-password",
            "full_name": "Ashutosh",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401

    payload = response.json()
    assert payload["data"] is None
    assert payload["meta"] == {}
    assert payload["error"]["code"] == "INVALID_CREDENTIALS"
    assert payload["error"]["message"] == "Invalid email or password"


def test_me_requires_bearer_token_and_returns_current_user(client) -> None:
    unauthorized_response = client.get("/api/v1/auth/me")

    assert unauthorized_response.status_code == 401
    unauthorized_payload = unauthorized_response.json()
    assert unauthorized_payload["data"] is None
    assert unauthorized_payload["error"]["code"] == "UNAUTHORIZED"

    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "user@example.com",
            "password": "strong-password",
            "full_name": "Ashutosh",
        },
    )
    token = signup_response.json()["data"]["token"]

    authorized_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert authorized_response.status_code == 200
    authorized_payload = authorized_response.json()
    assert authorized_payload["error"] is None
    assert authorized_payload["meta"] == {}
    assert authorized_payload["data"]["email"] == "user@example.com"
    assert authorized_payload["data"]["full_name"] == "Ashutosh"
