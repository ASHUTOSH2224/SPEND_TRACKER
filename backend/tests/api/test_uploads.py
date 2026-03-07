from app.core.config import get_settings
from app.services.storage import build_upload_storage


def _auth_headers(client, *, email: str, full_name: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "strong-password",
            "full_name": full_name,
        },
    )
    assert response.status_code == 201
    token = response.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def test_presign_returns_local_upload_url_and_put_stores_bytes(client) -> None:
    headers = _auth_headers(client, email="owner@example.com", full_name="Owner")

    presign_response = client.post(
        "/api/v1/uploads/presign",
        json={
            "file_name": "march_2026.pdf",
            "content_type": "application/pdf",
        },
        headers=headers,
    )
    assert presign_response.status_code == 200

    presign_data = presign_response.json()["data"]
    assert presign_data["upload_url"].startswith("/api/v1/uploads/content?file_storage_key=")
    assert presign_data["file_storage_key"].endswith("-march_2026.pdf")

    upload_response = client.put(
        presign_data["upload_url"],
        content=b"%PDF-1.7 local upload",
        headers={
            **headers,
            "content-type": "application/pdf",
        },
    )
    assert upload_response.status_code == 200
    assert upload_response.json()["data"] == {
        "stored": True,
        "file_storage_key": presign_data["file_storage_key"],
    }

    storage = build_upload_storage(get_settings())
    assert (
        storage.get_object_bytes(file_storage_key=presign_data["file_storage_key"])
        == b"%PDF-1.7 local upload"
    )


def test_upload_endpoint_rejects_non_owned_storage_keys(client) -> None:
    owner_headers = _auth_headers(client, email="owner@example.com", full_name="Owner")
    other_headers = _auth_headers(client, email="other@example.com", full_name="Other")

    presign_response = client.post(
        "/api/v1/uploads/presign",
        json={
            "file_name": "march_2026.pdf",
            "content_type": "application/pdf",
        },
        headers=owner_headers,
    )
    assert presign_response.status_code == 200
    upload_url = presign_response.json()["data"]["upload_url"]

    upload_response = client.put(
        upload_url,
        content=b"%PDF-1.7 local upload",
        headers={
            **other_headers,
            "content-type": "application/pdf",
        },
    )
    assert upload_response.status_code == 422
    assert upload_response.json()["error"]["code"] == "INVALID_FILE_STORAGE_KEY"
