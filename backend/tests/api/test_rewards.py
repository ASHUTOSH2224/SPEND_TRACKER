from datetime import date
from decimal import Decimal
from uuid import UUID

from app.db.session import get_session
from app.models.card_charge_summary import CardChargeSummary


def _auth_context(client, *, email: str, full_name: str) -> tuple[dict[str, str], str]:
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "strong-password",
            "full_name": full_name,
        },
    )
    assert signup_response.status_code == 201
    token = signup_response.json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    return headers, me_response.json()["data"]["id"]


def _card_payload(last4: str, nickname: str, reward_type: str = "points") -> dict:
    return {
        "nickname": nickname,
        "issuer_name": "HDFC",
        "network": "Visa",
        "last4": last4,
        "statement_cycle_day": 12,
        "annual_fee_expected": 12500,
        "joining_fee_expected": 12500,
        "reward_program_name": "Rewards",
        "reward_type": reward_type,
        "reward_conversion_rate": "0.5000",
        "reward_rule_config_json": {"base_rate": 3},
    }


def _create_card(client, headers: dict[str, str], *, last4: str, nickname: str, reward_type: str = "points") -> str:
    response = client.post(
        "/api/v1/cards",
        json=_card_payload(last4, nickname, reward_type),
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _create_statement(
    client,
    headers: dict[str, str],
    *,
    card_id: str,
    file_name: str,
    period_start: str,
    period_end: str,
) -> str:
    presign_response = client.post(
        "/api/v1/uploads/presign",
        json={
            "file_name": file_name,
            "content_type": "application/pdf",
        },
        headers=headers,
    )
    assert presign_response.status_code == 200
    file_storage_key = presign_response.json()["data"]["file_storage_key"]

    create_response = client.post(
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
    assert create_response.status_code == 201
    return create_response.json()["data"]["id"]


def _seed_charge_summary(
    *,
    user_id: str,
    card_id: str,
    period_month: date,
    annual_fee_amount: str,
    joining_fee_amount: str,
    late_fee_amount: str,
    finance_charge_amount: str,
    emi_processing_fee_amount: str,
    cash_advance_fee_amount: str,
    forex_markup_amount: str,
    tax_amount: str,
    other_charge_amount: str,
    total_charge_amount: str,
) -> None:
    with get_session() as session:
        session.add(
            CardChargeSummary(
                user_id=UUID(user_id),
                card_id=UUID(card_id),
                period_month=period_month,
                annual_fee_amount=Decimal(annual_fee_amount),
                joining_fee_amount=Decimal(joining_fee_amount),
                late_fee_amount=Decimal(late_fee_amount),
                finance_charge_amount=Decimal(finance_charge_amount),
                emi_processing_fee_amount=Decimal(emi_processing_fee_amount),
                cash_advance_fee_amount=Decimal(cash_advance_fee_amount),
                forex_markup_amount=Decimal(forex_markup_amount),
                tax_amount=Decimal(tax_amount),
                other_charge_amount=Decimal(other_charge_amount),
                total_charge_amount=Decimal(total_charge_amount),
            )
        )
        session.commit()


def test_reward_ledger_crud_and_list_filters(client) -> None:
    headers, _ = _auth_context(client, email="owner@example.com", full_name="Owner")
    card_id = _create_card(client, headers, last4="1234", nickname="HDFC Infinia")
    statement_id = _create_statement(
        client,
        headers,
        card_id=card_id,
        file_name="owner_statement.pdf",
        period_start="2026-03-01",
        period_end="2026-03-31",
    )

    create_response = client.post(
        "/api/v1/reward-ledgers",
        json={
            "card_id": card_id,
            "statement_id": statement_id,
            "event_date": "2026-03-05",
            "event_type": "earned",
            "reward_points": 1200,
            "reward_value_estimate": 600,
            "source": "manual",
            "notes": "Entered from statement summary",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    created_reward = create_response.json()["data"]
    reward_ledger_id = created_reward["id"]
    assert created_reward["card_id"] == card_id
    assert created_reward["statement_id"] == statement_id
    assert created_reward["event_type"] == "earned"
    assert Decimal(str(created_reward["reward_points"])) == Decimal("1200.00")

    second_create = client.post(
        "/api/v1/reward-ledgers",
        json={
            "card_id": card_id,
            "event_date": "2026-03-07",
            "event_type": "cashback",
            "reward_value_estimate": 250,
            "source": "manual",
            "notes": "Cashback posted",
        },
        headers=headers,
    )
    assert second_create.status_code == 201

    list_response = client.get(
        "/api/v1/reward-ledgers",
        params={
            "card_id": card_id,
            "event_type": "earned",
            "from_date": "2026-03-01",
            "to_date": "2026-03-31",
        },
        headers=headers,
    )
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert len(list_payload["data"]) == 1
    assert list_payload["data"][0]["id"] == reward_ledger_id

    patch_response = client.patch(
        f"/api/v1/reward-ledgers/{reward_ledger_id}",
        json={
            "event_type": "adjusted",
            "reward_points": 1100,
            "reward_value_estimate": 550,
            "notes": "Adjusted after reconciliation",
        },
        headers=headers,
    )
    assert patch_response.status_code == 200
    patch_payload = patch_response.json()["data"]
    assert patch_payload["event_type"] == "adjusted"
    assert Decimal(str(patch_payload["reward_points"])) == Decimal("1100.00")
    assert patch_payload["notes"] == "Adjusted after reconciliation"

    delete_response = client.delete(f"/api/v1/reward-ledgers/{reward_ledger_id}", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["id"] == reward_ledger_id

    final_list_response = client.get("/api/v1/reward-ledgers", headers=headers)
    assert final_list_response.status_code == 200
    final_items = final_list_response.json()["data"]
    assert len(final_items) == 1
    assert final_items[0]["event_type"] == "cashback"


def test_reward_summary_and_charge_summary_endpoints(client) -> None:
    headers, user_id = _auth_context(client, email="owner@example.com", full_name="Owner")
    card_id = _create_card(client, headers, last4="1234", nickname="HDFC Infinia")

    for payload in (
        {
            "card_id": card_id,
            "event_date": "2026-03-05",
            "event_type": "earned",
            "reward_points": 1200,
            "reward_value_estimate": 600,
            "source": "manual",
            "notes": "Statement earn",
        },
        {
            "card_id": card_id,
            "event_date": "2026-03-06",
            "event_type": "redeemed",
            "reward_points": 200,
            "reward_value_estimate": 0,
            "source": "manual",
            "notes": "Redemption",
        },
        {
            "card_id": card_id,
            "event_date": "2026-03-07",
            "event_type": "expired",
            "reward_points": 100,
            "reward_value_estimate": 0,
            "source": "manual",
            "notes": "Expired points",
        },
        {
            "card_id": card_id,
            "event_date": "2026-03-08",
            "event_type": "adjusted",
            "reward_points": 50,
            "reward_value_estimate": 25,
            "source": "manual",
            "notes": "Adjustment",
        },
    ):
        response = client.post("/api/v1/reward-ledgers", json=payload, headers=headers)
        assert response.status_code == 201

    _seed_charge_summary(
        user_id=user_id,
        card_id=card_id,
        period_month=date(2026, 1, 1),
        annual_fee_amount="1000",
        joining_fee_amount="0",
        late_fee_amount="50",
        finance_charge_amount="25",
        emi_processing_fee_amount="0",
        cash_advance_fee_amount="0",
        forex_markup_amount="10",
        tax_amount="200",
        other_charge_amount="15",
        total_charge_amount="1300",
    )
    _seed_charge_summary(
        user_id=user_id,
        card_id=card_id,
        period_month=date(2026, 2, 1),
        annual_fee_amount="0",
        joining_fee_amount="500",
        late_fee_amount="0",
        finance_charge_amount="0",
        emi_processing_fee_amount="20",
        cash_advance_fee_amount="5",
        forex_markup_amount="0",
        tax_amount="80",
        other_charge_amount="10",
        total_charge_amount="615",
    )

    reward_summary_response = client.get(f"/api/v1/cards/{card_id}/rewards", headers=headers)
    assert reward_summary_response.status_code == 200
    reward_summary = reward_summary_response.json()["data"]
    assert reward_summary["card_id"] == card_id
    assert reward_summary["reward_type"] == "points"
    assert Decimal(str(reward_summary["total_points_earned"])) == Decimal("1200.00")
    assert Decimal(str(reward_summary["total_points_redeemed"])) == Decimal("200.00")
    assert Decimal(str(reward_summary["total_points_expired"])) == Decimal("100.00")
    assert Decimal(str(reward_summary["estimated_reward_value"])) == Decimal("625.00")
    assert Decimal(str(reward_summary["current_balance"])) == Decimal("950.00")

    charge_summary_response = client.get(f"/api/v1/cards/{card_id}/charges", headers=headers)
    assert charge_summary_response.status_code == 200
    charge_summary = charge_summary_response.json()["data"]
    assert charge_summary["card_id"] == card_id
    assert charge_summary["source"] == "card_charge_summaries"
    assert charge_summary["summary_period_count"] == 2
    assert Decimal(str(charge_summary["annual_fee_amount"])) == Decimal("1000.00")
    assert Decimal(str(charge_summary["joining_fee_amount"])) == Decimal("500.00")
    assert Decimal(str(charge_summary["late_fee_amount"])) == Decimal("50.00")
    assert Decimal(str(charge_summary["finance_charge_amount"])) == Decimal("25.00")
    assert Decimal(str(charge_summary["emi_processing_fee_amount"])) == Decimal("20.00")
    assert Decimal(str(charge_summary["cash_advance_fee_amount"])) == Decimal("5.00")
    assert Decimal(str(charge_summary["forex_markup_amount"])) == Decimal("10.00")
    assert Decimal(str(charge_summary["tax_amount"])) == Decimal("280.00")
    assert Decimal(str(charge_summary["other_charge_amount"])) == Decimal("25.00")
    assert Decimal(str(charge_summary["total_charge_amount"])) == Decimal("1915.00")


def test_reward_and_charge_endpoints_enforce_ownership_and_validation(client) -> None:
    owner_headers, _ = _auth_context(client, email="owner@example.com", full_name="Owner")
    other_headers, _ = _auth_context(client, email="other@example.com", full_name="Other")
    owner_card_id = _create_card(client, owner_headers, last4="1234", nickname="Owner Card")
    other_card_id = _create_card(client, other_headers, last4="5678", nickname="Other Card")
    other_statement_id = _create_statement(
        client,
        other_headers,
        card_id=other_card_id,
        file_name="other_statement.pdf",
        period_start="2026-03-01",
        period_end="2026-03-31",
    )

    invalid_create = client.post(
        "/api/v1/reward-ledgers",
        json={
            "card_id": owner_card_id,
            "statement_id": other_statement_id,
            "event_date": "2026-03-05",
            "event_type": "earned",
            "reward_points": 1200,
            "source": "manual",
        },
        headers=owner_headers,
    )
    assert invalid_create.status_code == 404
    assert invalid_create.json()["error"]["code"] == "STATEMENT_NOT_FOUND"

    create_response = client.post(
        "/api/v1/reward-ledgers",
        json={
            "card_id": owner_card_id,
            "event_date": "2026-03-05",
            "event_type": "earned",
            "reward_points": 1200,
            "source": "manual",
        },
        headers=owner_headers,
    )
    assert create_response.status_code == 201
    reward_ledger_id = create_response.json()["data"]["id"]

    unauthorized_list = client.get("/api/v1/reward-ledgers")
    assert unauthorized_list.status_code == 401
    assert unauthorized_list.json()["error"]["code"] == "UNAUTHORIZED"

    other_patch = client.patch(
        f"/api/v1/reward-ledgers/{reward_ledger_id}",
        json={"notes": "Should fail"},
        headers=other_headers,
    )
    assert other_patch.status_code == 404
    assert other_patch.json()["error"]["code"] == "REWARD_LEDGER_NOT_FOUND"

    other_delete = client.delete(
        f"/api/v1/reward-ledgers/{reward_ledger_id}",
        headers=other_headers,
    )
    assert other_delete.status_code == 404
    assert other_delete.json()["error"]["code"] == "REWARD_LEDGER_NOT_FOUND"

    other_reward_summary = client.get(f"/api/v1/cards/{owner_card_id}/rewards", headers=other_headers)
    assert other_reward_summary.status_code == 404
    assert other_reward_summary.json()["error"]["code"] == "CARD_NOT_FOUND"

    invalid_filter = client.get(
        "/api/v1/reward-ledgers",
        params={"from_date": "2026-03-31", "to_date": "2026-03-01"},
        headers=owner_headers,
    )
    assert invalid_filter.status_code == 422
    assert invalid_filter.json()["error"]["code"] == "VALIDATION_ERROR"
