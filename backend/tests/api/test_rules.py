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


def _create_category(client, headers: dict[str, str], *, name: str, group_name: str) -> str:
    response = client.post(
        "/api/v1/categories",
        json={"name": name, "group_name": group_name},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _rule_payload(category_id: str) -> dict[str, object]:
    return {
        "rule_name": "Swiggy to Food",
        "match_type": "description_contains",
        "match_value": "SWIGGY",
        "assigned_category_id": category_id,
        "priority": 10,
        "is_active": True,
    }


def test_rules_crud_and_disable_flow(client) -> None:
    default_category_id = _seed_default_category(name="Food & Dining", group_name="spend")
    headers = _auth_headers(client, email="owner@example.com", full_name="Owner")
    custom_category_id = _create_category(
        client,
        headers,
        name="Office Supplies",
        group_name="spend",
    )

    create_response = client.post(
        "/api/v1/rules",
        json=_rule_payload(default_category_id),
        headers=headers,
    )
    assert create_response.status_code == 201

    create_payload = create_response.json()
    assert create_payload["error"] is None
    created_rule = create_payload["data"]
    assert created_rule["rule_name"] == "Swiggy to Food"
    assert created_rule["match_type"] == "description_contains"
    assert created_rule["assigned_category_id"] == default_category_id
    assert created_rule["priority"] == 10
    assert created_rule["is_active"] is True
    rule_id = created_rule["id"]

    list_response = client.get("/api/v1/rules", headers=headers)
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["error"] is None
    assert len(list_payload["data"]) == 1
    assert list_payload["data"][0]["id"] == rule_id

    patch_response = client.patch(
        f"/api/v1/rules/{rule_id}",
        json={
            "rule_name": "Amazon to Office Supplies",
            "match_type": "merchant_equals",
            "match_value": "AMAZON",
            "assigned_category_id": custom_category_id,
            "priority": 5,
        },
        headers=headers,
    )
    assert patch_response.status_code == 200
    patch_payload = patch_response.json()
    assert patch_payload["data"]["rule_name"] == "Amazon to Office Supplies"
    assert patch_payload["data"]["match_type"] == "merchant_equals"
    assert patch_payload["data"]["assigned_category_id"] == custom_category_id
    assert patch_payload["data"]["priority"] == 5
    assert patch_payload["data"]["is_active"] is True

    delete_response = client.delete(f"/api/v1/rules/{rule_id}", headers=headers)
    assert delete_response.status_code == 200
    delete_payload = delete_response.json()
    assert delete_payload["error"] is None
    assert delete_payload["data"]["is_active"] is False

    final_list_response = client.get("/api/v1/rules", headers=headers)
    assert final_list_response.status_code == 200
    assert final_list_response.json()["data"][0]["is_active"] is False


def test_rule_routes_require_authentication(client) -> None:
    list_response = client.get("/api/v1/rules")
    assert list_response.status_code == 401
    assert list_response.json()["error"]["code"] == "UNAUTHORIZED"

    create_response = client.post(
        "/api/v1/rules",
        json=_rule_payload("9bb14591-cb35-4849-b8c9-1c6adcc2f7cf"),
    )
    assert create_response.status_code == 401
    assert create_response.json()["error"]["code"] == "UNAUTHORIZED"


def test_rule_routes_enforce_ownership_and_category_scope_validation(client) -> None:
    owner_headers = _auth_headers(client, email="owner@example.com", full_name="Owner")
    other_headers = _auth_headers(client, email="other@example.com", full_name="Other")
    owner_category_id = _create_category(
        client,
        owner_headers,
        name="Owner Category",
        group_name="spend",
    )
    other_category_id = _create_category(
        client,
        other_headers,
        name="Other Category",
        group_name="spend",
    )

    create_response = client.post(
        "/api/v1/rules",
        json=_rule_payload(owner_category_id),
        headers=owner_headers,
    )
    assert create_response.status_code == 201
    rule_id = create_response.json()["data"]["id"]

    other_patch_response = client.patch(
        f"/api/v1/rules/{rule_id}",
        json={"rule_name": "Should Not Work"},
        headers=other_headers,
    )
    assert other_patch_response.status_code == 404
    assert other_patch_response.json()["error"]["code"] == "RULE_NOT_FOUND"

    other_delete_response = client.delete(f"/api/v1/rules/{rule_id}", headers=other_headers)
    assert other_delete_response.status_code == 404
    assert other_delete_response.json()["error"]["code"] == "RULE_NOT_FOUND"

    invalid_create_response = client.post(
        "/api/v1/rules",
        json=_rule_payload(other_category_id),
        headers=owner_headers,
    )
    assert invalid_create_response.status_code == 422
    assert invalid_create_response.json()["error"]["code"] == "INVALID_ASSIGNED_CATEGORY"

    invalid_patch_response = client.patch(
        f"/api/v1/rules/{rule_id}",
        json={"assigned_category_id": other_category_id},
        headers=owner_headers,
    )
    assert invalid_patch_response.status_code == 422
    assert invalid_patch_response.json()["error"]["code"] == "INVALID_ASSIGNED_CATEGORY"
