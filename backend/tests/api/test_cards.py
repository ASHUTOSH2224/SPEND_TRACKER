from decimal import Decimal


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


def _card_payload() -> dict:
    return {
        "nickname": "HDFC Infinia",
        "issuer_name": "HDFC",
        "network": "Visa",
        "last4": "1234",
        "statement_cycle_day": 12,
        "annual_fee_expected": 12500,
        "joining_fee_expected": 12500,
        "reward_program_name": "Infinia Rewards",
        "reward_type": "points",
        "reward_conversion_rate": "0.5000",
        "reward_rule_config_json": {"base_rate": 3},
    }


def test_cards_crud_and_archive_flow(client) -> None:
    headers = _auth_headers(client, email="owner@example.com", full_name="Owner")

    create_response = client.post("/api/v1/cards", json=_card_payload(), headers=headers)
    assert create_response.status_code == 201

    created_payload = create_response.json()
    assert created_payload["error"] is None
    assert created_payload["meta"] == {}
    created_card = created_payload["data"]
    assert created_card["nickname"] == "HDFC Infinia"
    assert created_card["issuer_name"] == "HDFC"
    assert created_card["network"] == "visa"
    assert created_card["last4"] == "1234"
    assert created_card["status"] == "active"
    assert Decimal(str(created_card["annual_fee_expected"])) == Decimal("12500.00")
    card_id = created_card["id"]

    list_response = client.get("/api/v1/cards", headers=headers)
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["error"] is None
    assert list_payload["meta"] == {}
    assert len(list_payload["data"]) == 1
    assert list_payload["data"][0]["id"] == card_id

    get_response = client.get(f"/api/v1/cards/{card_id}", headers=headers)
    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["data"]["id"] == card_id

    update_response = client.patch(
        f"/api/v1/cards/{card_id}",
        json={
            "nickname": "HDFC Infinia Metal",
            "network": "MasterCard",
            "statement_cycle_day": 15,
            "joining_fee_expected": None,
        },
        headers=headers,
    )
    assert update_response.status_code == 200
    update_payload = update_response.json()
    assert update_payload["error"] is None
    assert update_payload["data"]["nickname"] == "HDFC Infinia Metal"
    assert update_payload["data"]["network"] == "mastercard"
    assert update_payload["data"]["statement_cycle_day"] == 15
    assert update_payload["data"]["joining_fee_expected"] is None

    delete_response = client.delete(f"/api/v1/cards/{card_id}", headers=headers)
    assert delete_response.status_code == 200
    delete_payload = delete_response.json()
    assert delete_payload["error"] is None
    assert delete_payload["data"]["status"] == "archived"

    archived_get_response = client.get(f"/api/v1/cards/{card_id}", headers=headers)
    assert archived_get_response.status_code == 200
    archived_get_payload = archived_get_response.json()
    assert archived_get_payload["data"]["status"] == "archived"

    archived_list_response = client.get("/api/v1/cards", headers=headers)
    assert archived_list_response.status_code == 200
    archived_list_payload = archived_list_response.json()
    assert len(archived_list_payload["data"]) == 1
    assert archived_list_payload["data"][0]["status"] == "archived"


def test_cards_require_authentication(client) -> None:
    list_response = client.get("/api/v1/cards")
    assert list_response.status_code == 401
    list_payload = list_response.json()
    assert list_payload["data"] is None
    assert list_payload["error"]["code"] == "UNAUTHORIZED"

    create_response = client.post("/api/v1/cards", json=_card_payload())
    assert create_response.status_code == 401
    create_payload = create_response.json()
    assert create_payload["data"] is None
    assert create_payload["error"]["code"] == "UNAUTHORIZED"


def test_card_routes_enforce_ownership(client) -> None:
    owner_headers = _auth_headers(client, email="owner@example.com", full_name="Owner")
    other_headers = _auth_headers(client, email="other@example.com", full_name="Other")

    create_response = client.post("/api/v1/cards", json=_card_payload(), headers=owner_headers)
    card_id = create_response.json()["data"]["id"]

    get_response = client.get(f"/api/v1/cards/{card_id}", headers=other_headers)
    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "CARD_NOT_FOUND"

    patch_response = client.patch(
        f"/api/v1/cards/{card_id}",
        json={"nickname": "Should Not Work"},
        headers=other_headers,
    )
    assert patch_response.status_code == 404
    assert patch_response.json()["error"]["code"] == "CARD_NOT_FOUND"

    delete_response = client.delete(f"/api/v1/cards/{card_id}", headers=other_headers)
    assert delete_response.status_code == 404
    assert delete_response.json()["error"]["code"] == "CARD_NOT_FOUND"

    other_list_response = client.get("/api/v1/cards", headers=other_headers)
    assert other_list_response.status_code == 200
    assert other_list_response.json()["data"] == []


def test_create_card_validates_last4(client) -> None:
    headers = _auth_headers(client, email="owner@example.com", full_name="Owner")
    payload = _card_payload()
    payload["last4"] = "123"

    response = client.post("/api/v1/cards", json=payload, headers=headers)
    assert response.status_code == 422

    body = response.json()
    assert body["data"] is None
    assert body["error"]["code"] == "VALIDATION_ERROR"
