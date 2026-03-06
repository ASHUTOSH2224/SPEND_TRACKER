from app.db.session import get_session
from app.models.category import Category
from app.services.categories import slugify_category_name


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


def _seed_default_category(*, name: str, group_name: str) -> str:
    with get_session() as session:
        category = Category(
            user_id=None,
            name=name,
            slug=slugify_category_name(name),
            group_name=group_name,
            is_default=True,
            is_archived=False,
        )
        session.add(category)
        session.commit()
        session.refresh(category)
        return str(category.id)


def test_categories_crud_and_archive_flow(client) -> None:
    default_category_id = _seed_default_category(name="Food & Dining", group_name="spend")
    headers = _auth_headers(client, email="owner@example.com", full_name="Owner")

    create_response = client.post(
        "/api/v1/categories",
        json={"name": "Office Supplies", "group_name": "spend"},
        headers=headers,
    )
    assert create_response.status_code == 201

    create_payload = create_response.json()
    assert create_payload["error"] is None
    created_category = create_payload["data"]
    assert created_category["name"] == "Office Supplies"
    assert created_category["slug"] == "office-supplies"
    assert created_category["group_name"] == "spend"
    assert created_category["is_default"] is False
    assert created_category["is_archived"] is False
    category_id = created_category["id"]

    list_response = client.get("/api/v1/categories", headers=headers)
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["error"] is None
    returned_ids = {item["id"] for item in list_payload["data"]}
    assert default_category_id in returned_ids
    assert category_id in returned_ids

    rename_response = client.patch(
        f"/api/v1/categories/{category_id}",
        json={"name": "Work Expenses"},
        headers=headers,
    )
    assert rename_response.status_code == 200
    rename_payload = rename_response.json()
    assert rename_payload["data"]["name"] == "Work Expenses"
    assert rename_payload["data"]["slug"] == "work-expenses"
    assert rename_payload["data"]["is_archived"] is False

    archive_response = client.patch(
        f"/api/v1/categories/{category_id}",
        json={"is_archived": True},
        headers=headers,
    )
    assert archive_response.status_code == 200
    assert archive_response.json()["data"]["is_archived"] is True

    restore_response = client.patch(
        f"/api/v1/categories/{category_id}",
        json={"is_archived": False},
        headers=headers,
    )
    assert restore_response.status_code == 200
    assert restore_response.json()["data"]["is_archived"] is False

    delete_response = client.delete(f"/api/v1/categories/{category_id}", headers=headers)
    assert delete_response.status_code == 200
    delete_payload = delete_response.json()
    assert delete_payload["error"] is None
    assert delete_payload["data"]["is_archived"] is True

    final_list_response = client.get("/api/v1/categories", headers=headers)
    assert final_list_response.status_code == 200
    archived_category = next(
        item for item in final_list_response.json()["data"] if item["id"] == category_id
    )
    assert archived_category["is_archived"] is True


def test_category_routes_require_authentication(client) -> None:
    list_response = client.get("/api/v1/categories")
    assert list_response.status_code == 401
    assert list_response.json()["error"]["code"] == "UNAUTHORIZED"

    create_response = client.post(
        "/api/v1/categories",
        json={"name": "Office Supplies", "group_name": "spend"},
    )
    assert create_response.status_code == 401
    assert create_response.json()["error"]["code"] == "UNAUTHORIZED"


def test_category_routes_enforce_ownership_and_default_read_only(client) -> None:
    default_category_id = _seed_default_category(name="Annual Fee", group_name="charges")
    owner_headers = _auth_headers(client, email="owner@example.com", full_name="Owner")
    other_headers = _auth_headers(client, email="other@example.com", full_name="Other")

    create_response = client.post(
        "/api/v1/categories",
        json={"name": "Owner Only", "group_name": "spend"},
        headers=owner_headers,
    )
    category_id = create_response.json()["data"]["id"]

    other_patch_response = client.patch(
        f"/api/v1/categories/{category_id}",
        json={"name": "Should Not Work"},
        headers=other_headers,
    )
    assert other_patch_response.status_code == 404
    assert other_patch_response.json()["error"]["code"] == "CATEGORY_NOT_FOUND"

    other_delete_response = client.delete(
        f"/api/v1/categories/{category_id}",
        headers=other_headers,
    )
    assert other_delete_response.status_code == 404
    assert other_delete_response.json()["error"]["code"] == "CATEGORY_NOT_FOUND"

    default_patch_response = client.patch(
        f"/api/v1/categories/{default_category_id}",
        json={"name": "Should Not Work"},
        headers=owner_headers,
    )
    assert default_patch_response.status_code == 403
    assert default_patch_response.json()["error"]["code"] == "CATEGORY_READ_ONLY"

    default_delete_response = client.delete(
        f"/api/v1/categories/{default_category_id}",
        headers=owner_headers,
    )
    assert default_delete_response.status_code == 403
    assert default_delete_response.json()["error"]["code"] == "CATEGORY_READ_ONLY"


def test_create_category_validates_group_name(client) -> None:
    headers = _auth_headers(client, email="owner@example.com", full_name="Owner")

    response = client.post(
        "/api/v1/categories",
        json={"name": "Bad Category", "group_name": "invalid"},
        headers=headers,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
