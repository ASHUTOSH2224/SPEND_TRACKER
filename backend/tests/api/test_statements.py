from datetime import date
from uuid import UUID


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


def _card_payload(last4: str, nickname: str) -> dict:
    return {
        "nickname": nickname,
        "issuer_name": "HDFC",
        "network": "Visa",
        "last4": last4,
        "statement_cycle_day": 12,
        "annual_fee_expected": 12500,
        "joining_fee_expected": 12500,
        "reward_program_name": "Infinia Rewards",
        "reward_type": "points",
        "reward_conversion_rate": "0.5000",
        "reward_rule_config_json": {"base_rate": 3},
    }


def _create_card(client, headers: dict[str, str], *, last4: str, nickname: str) -> str:
    response = client.post("/api/v1/cards", json=_card_payload(last4, nickname), headers=headers)
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _presign_upload(client, headers: dict[str, str], *, file_name: str) -> dict:
    response = client.post(
        "/api/v1/uploads/presign",
        json={
            "file_name": file_name,
            "content_type": "application/pdf",
        },
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()["data"]


def _create_statement(
    client,
    headers: dict[str, str],
    *,
    card_id: str,
    file_name: str,
    file_storage_key: str,
    period_start: str,
    period_end: str,
) -> dict:
    response = client.post(
        "/api/v1/statements",
        json={
            "card_id": card_id,
            "file_name": file_name,
            "file_storage_key": file_storage_key,
            "file_type": "pdf",
            "statement_period_start": period_start,
            "statement_period_end": period_end,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["data"]


def test_statement_create_list_detail_retry_delete_flow(client) -> None:
    headers = _auth_headers(client, email="owner@example.com", full_name="Owner")
    card_one_id = _create_card(client, headers, last4="1234", nickname="HDFC Infinia")
    card_two_id = _create_card(client, headers, last4="5678", nickname="Amex Gold")

    presigned_one = _presign_upload(client, headers, file_name="hdfc_feb_2026.pdf")
    presigned_two = _presign_upload(client, headers, file_name="amex_mar_2026.pdf")
    presigned_three = _presign_upload(client, headers, file_name="hdfc_jan_2026.pdf")

    statement_one = _create_statement(
        client,
        headers,
        card_id=card_one_id,
        file_name="hdfc_feb_2026.pdf",
        file_storage_key=presigned_one["file_storage_key"],
        period_start="2026-02-01",
        period_end="2026-02-28",
    )
    statement_two = _create_statement(
        client,
        headers,
        card_id=card_two_id,
        file_name="amex_mar_2026.pdf",
        file_storage_key=presigned_two["file_storage_key"],
        period_start="2026-03-01",
        period_end="2026-03-31",
    )
    statement_three = _create_statement(
        client,
        headers,
        card_id=card_one_id,
        file_name="hdfc_jan_2026.pdf",
        file_storage_key=presigned_three["file_storage_key"],
        period_start="2026-01-01",
        period_end="2026-01-31",
    )

    assert statement_one["upload_status"] == "uploaded"
    assert statement_one["extraction_status"] == "pending"
    assert statement_one["categorization_status"] == "pending"
    assert statement_one["transaction_count"] == 0

    detail_response = client.get(f"/api/v1/statements/{statement_one['id']}", headers=headers)
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["error"] is None
    assert detail_payload["data"]["id"] == statement_one["id"]
    assert detail_payload["data"]["card_id"] == card_one_id

    february_list_response = client.get(
        "/api/v1/statements",
        params={
            "card_id": card_one_id,
            "status": "uploaded",
            "month": "2026-02",
            "page": 1,
            "page_size": 1,
        },
        headers=headers,
    )
    assert february_list_response.status_code == 200
    february_list_payload = february_list_response.json()
    assert february_list_payload["error"] is None
    assert february_list_payload["meta"] == {
        "page": 1,
        "page_size": 1,
        "total": 1,
        "total_pages": 1,
    }
    assert [item["id"] for item in february_list_payload["data"]] == [statement_one["id"]]

    paged_list_response = client.get(
        "/api/v1/statements",
        params={"page": 2, "page_size": 1},
        headers=headers,
    )
    assert paged_list_response.status_code == 200
    paged_list_payload = paged_list_response.json()
    assert paged_list_payload["meta"] == {
        "page": 2,
        "page_size": 1,
        "total": 3,
        "total_pages": 3,
    }
    assert [item["id"] for item in paged_list_payload["data"]] == [statement_one["id"]]

    from app.db.session import get_session
    from app.models.statement import Statement

    with get_session() as session:
        statement_record = session.get(Statement, UUID(statement_two["id"]))
        assert statement_record is not None
        statement_record.upload_status = "failed"
        statement_record.extraction_status = "failed"
        statement_record.categorization_status = "failed"
        statement_record.transaction_count = 17
        statement_record.processing_error = "Parser timed out"
        session.commit()

    retry_response = client.post(
        f"/api/v1/statements/{statement_two['id']}/retry",
        headers=headers,
    )
    assert retry_response.status_code == 200
    retry_payload = retry_response.json()
    assert retry_payload["error"] is None
    assert retry_payload["data"]["id"] == statement_two["id"]
    assert retry_payload["data"]["upload_status"] == "uploaded"
    assert retry_payload["data"]["extraction_status"] == "pending"
    assert retry_payload["data"]["categorization_status"] == "pending"
    assert retry_payload["data"]["transaction_count"] == 0
    assert retry_payload["data"]["processing_error"] is None

    delete_response = client.delete(
        f"/api/v1/statements/{statement_three['id']}",
        headers=headers,
    )
    assert delete_response.status_code == 200
    delete_payload = delete_response.json()
    assert delete_payload["error"] is None
    assert delete_payload["data"] == {
        "id": statement_three["id"],
        "deleted": True,
        "transactions_deleted": 0,
        "storage_object_deleted": False,
        "delete_policy": (
            "Deletes the statement metadata row and any queued processing jobs when "
            "no imported transactions are linked. The local fake storage backend does "
            "not delete any file blob."
        ),
    }

    missing_after_delete = client.get(
        f"/api/v1/statements/{statement_three['id']}",
        headers=headers,
    )
    assert missing_after_delete.status_code == 404
    assert missing_after_delete.json()["error"]["code"] == "STATEMENT_NOT_FOUND"


def test_statement_routes_enforce_owned_cards_and_statement_ownership(client) -> None:
    owner_headers = _auth_headers(client, email="owner@example.com", full_name="Owner")
    other_headers = _auth_headers(client, email="other@example.com", full_name="Other")

    owner_card_id = _create_card(client, owner_headers, last4="1234", nickname="Owner Card")
    other_card_id = _create_card(client, other_headers, last4="5678", nickname="Other Card")
    presigned_owner = _presign_upload(client, owner_headers, file_name="owner_statement.pdf")
    presigned_other = _presign_upload(client, other_headers, file_name="other_statement.pdf")

    create_with_other_card = client.post(
        "/api/v1/statements",
        json={
            "card_id": other_card_id,
            "file_name": "bad.pdf",
            "file_storage_key": presigned_owner["file_storage_key"],
            "file_type": "pdf",
            "statement_period_start": "2026-02-01",
            "statement_period_end": "2026-02-28",
        },
        headers=owner_headers,
    )
    assert create_with_other_card.status_code == 404
    assert create_with_other_card.json()["error"]["code"] == "CARD_NOT_FOUND"

    create_with_other_key = client.post(
        "/api/v1/statements",
        json={
            "card_id": owner_card_id,
            "file_name": "bad.pdf",
            "file_storage_key": presigned_other["file_storage_key"],
            "file_type": "pdf",
            "statement_period_start": "2026-02-01",
            "statement_period_end": "2026-02-28",
        },
        headers=owner_headers,
    )
    assert create_with_other_key.status_code == 422
    assert create_with_other_key.json()["error"]["code"] == "INVALID_FILE_STORAGE_KEY"

    statement = _create_statement(
        client,
        owner_headers,
        card_id=owner_card_id,
        file_name="owner_statement.pdf",
        file_storage_key=presigned_owner["file_storage_key"],
        period_start="2026-02-01",
        period_end="2026-02-28",
    )

    other_detail = client.get(f"/api/v1/statements/{statement['id']}", headers=other_headers)
    assert other_detail.status_code == 404
    assert other_detail.json()["error"]["code"] == "STATEMENT_NOT_FOUND"

    other_retry = client.post(f"/api/v1/statements/{statement['id']}/retry", headers=other_headers)
    assert other_retry.status_code == 404
    assert other_retry.json()["error"]["code"] == "STATEMENT_NOT_FOUND"

    other_delete = client.delete(f"/api/v1/statements/{statement['id']}", headers=other_headers)
    assert other_delete.status_code == 404
    assert other_delete.json()["error"]["code"] == "STATEMENT_NOT_FOUND"

    other_list = client.get("/api/v1/statements", headers=other_headers)
    assert other_list.status_code == 200
    assert other_list.json()["data"] == []
    assert other_list.json()["meta"] == {
        "page": 1,
        "page_size": 20,
        "total": 0,
        "total_pages": 0,
    }


def test_statement_retry_requires_failed_status_and_validates_month_filter(client) -> None:
    headers = _auth_headers(client, email="owner@example.com", full_name="Owner")
    card_id = _create_card(client, headers, last4="1234", nickname="Owner Card")
    presigned = _presign_upload(client, headers, file_name="owner_statement.pdf")
    statement = _create_statement(
        client,
        headers,
        card_id=card_id,
        file_name="owner_statement.pdf",
        file_storage_key=presigned["file_storage_key"],
        period_start="2026-02-01",
        period_end="2026-02-28",
    )

    retry_response = client.post(f"/api/v1/statements/{statement['id']}/retry", headers=headers)
    assert retry_response.status_code == 409
    assert retry_response.json()["error"]["code"] == "STATEMENT_RETRY_NOT_ALLOWED"

    invalid_month_response = client.get(
        "/api/v1/statements",
        params={"month": "2026-13"},
        headers=headers,
    )
    assert invalid_month_response.status_code == 422
    assert invalid_month_response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_statement_create_rejects_archived_cards(client) -> None:
    headers = _auth_headers(client, email="owner@example.com", full_name="Owner")
    card_id = _create_card(client, headers, last4="1234", nickname="Owner Card")
    archive_response = client.delete(f"/api/v1/cards/{card_id}", headers=headers)
    assert archive_response.status_code == 200

    presigned = _presign_upload(client, headers, file_name="owner_statement.pdf")
    response = client.post(
        "/api/v1/statements",
        json={
            "card_id": card_id,
            "file_name": "owner_statement.pdf",
            "file_storage_key": presigned["file_storage_key"],
            "file_type": "pdf",
            "statement_period_start": date(2026, 2, 1).isoformat(),
            "statement_period_end": date(2026, 2, 28).isoformat(),
        },
        headers=headers,
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CARD_ARCHIVED"
