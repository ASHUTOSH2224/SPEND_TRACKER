from datetime import date
from decimal import Decimal
from uuid import UUID

from app.db.session import get_session
from app.models.category import Category
from app.models.reward_ledger import RewardLedger
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.services.categories import slugify_category_name


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
    user_id = me_response.json()["data"]["id"]
    return headers, user_id


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


def _card_payload(last4: str, nickname: str, *, reward_conversion_rate: str = "0.5000") -> dict:
    return {
        "nickname": nickname,
        "issuer_name": "HDFC",
        "network": "Visa",
        "last4": last4,
        "statement_cycle_day": 12,
        "annual_fee_expected": 12500,
        "joining_fee_expected": 12500,
        "reward_program_name": "Rewards",
        "reward_type": "points",
        "reward_conversion_rate": reward_conversion_rate,
        "reward_rule_config_json": {"base_rate": 3},
    }


def _create_card(
    client,
    headers: dict[str, str],
    *,
    last4: str,
    nickname: str,
    reward_conversion_rate: str = "0.5000",
) -> str:
    response = client.post(
        "/api/v1/cards",
        json=_card_payload(last4, nickname, reward_conversion_rate=reward_conversion_rate),
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


def _seed_transaction(
    *,
    user_id: str,
    card_id: str,
    statement_id: str,
    txn_date: date,
    raw_description: str,
    normalized_merchant: str,
    amount: str,
    txn_type: str,
    category_id: str | None,
    category_source: str | None,
    category_confidence: str | None,
    review_required: bool,
    duplicate_flag: bool,
    is_card_charge: bool,
    charge_type: str | None,
    source_hash: str,
) -> str:
    with get_session() as session:
        transaction = Transaction(
            user_id=UUID(user_id),
            card_id=UUID(card_id),
            statement_id=UUID(statement_id),
            txn_date=txn_date,
            posted_date=txn_date,
            raw_description=raw_description,
            normalized_merchant=normalized_merchant,
            amount=Decimal(amount),
            currency="INR",
            txn_direction="debit",
            txn_type=txn_type,
            category_id=UUID(category_id) if category_id is not None else None,
            category_source=category_source,
            category_confidence=Decimal(category_confidence) if category_confidence is not None else None,
            category_explanation=None,
            review_required=review_required,
            duplicate_flag=duplicate_flag,
            is_card_charge=is_card_charge,
            charge_type=charge_type,
            is_reward_related=False,
            reward_points_delta=None,
            cashback_amount=None,
            source_hash=source_hash,
            metadata_json={"seeded": True},
        )
        session.add(transaction)
        statement = session.get(Statement, UUID(statement_id))
        assert statement is not None
        statement.transaction_count += 1
        session.commit()
        session.refresh(transaction)
        return str(transaction.id)


def _seed_reward_ledger(
    *,
    user_id: str,
    card_id: str,
    event_date: date,
    event_type: str,
    reward_points: str | None,
    reward_value_estimate: str | None,
    notes: str,
) -> str:
    with get_session() as session:
        reward_ledger = RewardLedger(
            user_id=UUID(user_id),
            card_id=UUID(card_id),
            statement_id=None,
            event_date=event_date,
            event_type=event_type,
            reward_points=Decimal(reward_points) if reward_points is not None else None,
            reward_value_estimate=(
                Decimal(reward_value_estimate) if reward_value_estimate is not None else None
            ),
            source="manual",
            notes=notes,
        )
        session.add(reward_ledger)
        session.commit()
        session.refresh(reward_ledger)
        return str(reward_ledger.id)


def _seed_analytics_dataset(client) -> dict[str, object]:
    owner_headers, owner_user_id = _auth_context(
        client,
        email="owner@example.com",
        full_name="Owner",
    )
    other_headers, other_user_id = _auth_context(
        client,
        email="other@example.com",
        full_name="Other",
    )

    food_category_id = _seed_default_category(name="Food & Dining", group_name="spend")
    shopping_category_id = _seed_default_category(name="Shopping", group_name="spend")
    annual_fee_category_id = _seed_default_category(name="Annual Fee", group_name="charges")
    tax_category_id = _seed_default_category(name="Tax on Charge", group_name="charges")

    owner_card_one_id = _create_card(
        client,
        owner_headers,
        last4="1234",
        nickname="HDFC Infinia",
        reward_conversion_rate="0.5000",
    )
    owner_card_two_id = _create_card(
        client,
        owner_headers,
        last4="5678",
        nickname="Amex Gold",
        reward_conversion_rate="0.5000",
    )
    other_card_id = _create_card(
        client,
        other_headers,
        last4="9999",
        nickname="Other Card",
        reward_conversion_rate="0.5000",
    )

    owner_statement_one_feb_id = _create_statement(
        client,
        owner_headers,
        card_id=owner_card_one_id,
        file_name="owner_card_one_feb.pdf",
        period_start="2026-02-01",
        period_end="2026-02-28",
    )
    owner_statement_one_mar_id = _create_statement(
        client,
        owner_headers,
        card_id=owner_card_one_id,
        file_name="owner_card_one_mar.pdf",
        period_start="2026-03-01",
        period_end="2026-03-31",
    )
    owner_statement_two_feb_id = _create_statement(
        client,
        owner_headers,
        card_id=owner_card_two_id,
        file_name="owner_card_two_feb.pdf",
        period_start="2026-02-01",
        period_end="2026-02-28",
    )
    owner_statement_two_mar_id = _create_statement(
        client,
        owner_headers,
        card_id=owner_card_two_id,
        file_name="owner_card_two_mar.pdf",
        period_start="2026-03-01",
        period_end="2026-03-31",
    )
    other_statement_id = _create_statement(
        client,
        other_headers,
        card_id=other_card_id,
        file_name="other_mar.pdf",
        period_start="2026-03-01",
        period_end="2026-03-31",
    )

    transaction_ids = {
        "dmart": _seed_transaction(
            user_id=owner_user_id,
            card_id=owner_card_one_id,
            statement_id=owner_statement_one_feb_id,
            txn_date=date(2026, 2, 10),
            raw_description="DMART BANGALORE",
            normalized_merchant="DMart",
            amount="800.00",
            txn_type="spend",
            category_id=food_category_id,
            category_source="rule",
            category_confidence="0.9500",
            review_required=False,
            duplicate_flag=False,
            is_card_charge=False,
            charge_type=None,
            source_hash="hash-dmart",
        ),
        "swiggy": _seed_transaction(
            user_id=owner_user_id,
            card_id=owner_card_one_id,
            statement_id=owner_statement_one_mar_id,
            txn_date=date(2026, 3, 1),
            raw_description="SWIGGY BANGALORE",
            normalized_merchant="Swiggy",
            amount="500.00",
            txn_type="spend",
            category_id=food_category_id,
            category_source="rule",
            category_confidence="0.9600",
            review_required=False,
            duplicate_flag=False,
            is_card_charge=False,
            charge_type=None,
            source_hash="hash-swiggy",
        ),
        "duplicate": _seed_transaction(
            user_id=owner_user_id,
            card_id=owner_card_one_id,
            statement_id=owner_statement_one_mar_id,
            txn_date=date(2026, 3, 2),
            raw_description="GROCERY DUPLICATE",
            normalized_merchant="Fresh Grocery",
            amount="700.00",
            txn_type="spend",
            category_id=food_category_id,
            category_source="rule",
            category_confidence="0.9300",
            review_required=False,
            duplicate_flag=True,
            is_card_charge=False,
            charge_type=None,
            source_hash="hash-duplicate",
        ),
        "tax_charge": _seed_transaction(
            user_id=owner_user_id,
            card_id=owner_card_one_id,
            statement_id=owner_statement_one_mar_id,
            txn_date=date(2026, 3, 3),
            raw_description="BANK CHARGE GST",
            normalized_merchant="Bank Charge GST",
            amount="50.00",
            txn_type="charge",
            category_id=tax_category_id,
            category_source="rule",
            category_confidence="0.9900",
            review_required=False,
            duplicate_flag=False,
            is_card_charge=True,
            charge_type="tax",
            source_hash="hash-tax-charge",
        ),
        "zara": _seed_transaction(
            user_id=owner_user_id,
            card_id=owner_card_two_id,
            statement_id=owner_statement_two_feb_id,
            txn_date=date(2026, 2, 15),
            raw_description="ZARA STORE",
            normalized_merchant="Zara",
            amount="600.00",
            txn_type="spend",
            category_id=shopping_category_id,
            category_source="history",
            category_confidence="0.8100",
            review_required=False,
            duplicate_flag=False,
            is_card_charge=False,
            charge_type=None,
            source_hash="hash-zara",
        ),
        "amazon": _seed_transaction(
            user_id=owner_user_id,
            card_id=owner_card_two_id,
            statement_id=owner_statement_two_mar_id,
            txn_date=date(2026, 3, 4),
            raw_description="AMAZON PAY",
            normalized_merchant="Amazon",
            amount="1200.00",
            txn_type="spend",
            category_id=shopping_category_id,
            category_source="history",
            category_confidence="0.6200",
            review_required=True,
            duplicate_flag=False,
            is_card_charge=False,
            charge_type=None,
            source_hash="hash-amazon",
        ),
        "annual_fee": _seed_transaction(
            user_id=owner_user_id,
            card_id=owner_card_two_id,
            statement_id=owner_statement_two_mar_id,
            txn_date=date(2026, 3, 5),
            raw_description="ANNUAL FEE",
            normalized_merchant="Annual Fee",
            amount="999.00",
            txn_type="charge",
            category_id=annual_fee_category_id,
            category_source="rule",
            category_confidence="0.9800",
            review_required=False,
            duplicate_flag=False,
            is_card_charge=True,
            charge_type="annual_fee",
            source_hash="hash-annual-fee",
        ),
        "other_user": _seed_transaction(
            user_id=other_user_id,
            card_id=other_card_id,
            statement_id=other_statement_id,
            txn_date=date(2026, 3, 6),
            raw_description="OTHER USER TXN",
            normalized_merchant="Other Merchant",
            amount="5000.00",
            txn_type="spend",
            category_id=shopping_category_id,
            category_source="manual",
            category_confidence="1.0000",
            review_required=False,
            duplicate_flag=False,
            is_card_charge=False,
            charge_type=None,
            source_hash="hash-other-user",
        ),
    }

    _seed_reward_ledger(
        user_id=owner_user_id,
        card_id=owner_card_one_id,
        event_date=date(2026, 2, 12),
        event_type="earned",
        reward_points="120.00",
        reward_value_estimate=None,
        notes="February statement earn",
    )
    _seed_reward_ledger(
        user_id=owner_user_id,
        card_id=owner_card_one_id,
        event_date=date(2026, 3, 4),
        event_type="earned",
        reward_points="200.00",
        reward_value_estimate=None,
        notes="March statement earn",
    )
    _seed_reward_ledger(
        user_id=owner_user_id,
        card_id=owner_card_two_id,
        event_date=date(2026, 3, 6),
        event_type="cashback",
        reward_points=None,
        reward_value_estimate="120.00",
        notes="Cashback posted",
    )
    _seed_reward_ledger(
        user_id=owner_user_id,
        card_id=owner_card_two_id,
        event_date=date(2026, 3, 7),
        event_type="expired",
        reward_points="40.00",
        reward_value_estimate=None,
        notes="Points expired",
    )
    _seed_reward_ledger(
        user_id=other_user_id,
        card_id=other_card_id,
        event_date=date(2026, 3, 8),
        event_type="earned",
        reward_points="1000.00",
        reward_value_estimate="500.00",
        notes="Other user earn",
    )

    return {
        "owner_headers": owner_headers,
        "other_headers": other_headers,
        "cards": {
            "one": owner_card_one_id,
            "two": owner_card_two_id,
            "other": other_card_id,
        },
        "categories": {
            "food": food_category_id,
            "shopping": shopping_category_id,
            "annual_fee": annual_fee_category_id,
            "tax": tax_category_id,
        },
        "transactions": transaction_ids,
    }


def test_dashboard_analytics_endpoints(client) -> None:
    dataset = _seed_analytics_dataset(client)
    headers = dataset["owner_headers"]

    summary_response = client.get(
        "/api/v1/dashboard/summary",
        params={"from_date": "2026-03-01", "to_date": "2026-03-31"},
        headers=headers,
    )
    assert summary_response.status_code == 200
    summary_payload = summary_response.json()
    assert summary_payload["error"] is None
    summary = summary_payload["data"]
    assert Decimal(str(summary["total_spend"])) == Decimal("1700.00")
    assert Decimal(str(summary["previous_period_spend"])) == Decimal("1400.00")
    assert Decimal(str(summary["spend_change_pct"])) == Decimal("21.43")
    assert Decimal(str(summary["total_rewards_value"])) == Decimal("200.00")
    assert Decimal(str(summary["total_charges"])) == Decimal("1049.00")
    assert Decimal(str(summary["net_card_value"])) == Decimal("-849.00")
    assert summary["transaction_count"] == 4
    assert summary["needs_review_count"] == 1
    assert summary["top_category"] == {
        "category_id": dataset["categories"]["shopping"],
        "name": "Shopping",
        "amount": "1200.00",
    }
    assert summary["top_card"] == {
        "card_id": dataset["cards"]["two"],
        "name": "Amex Gold",
        "amount": "1200.00",
    }

    spend_by_category_response = client.get(
        "/api/v1/dashboard/spend-by-category",
        params={"from_date": "2026-03-01", "to_date": "2026-03-31"},
        headers=headers,
    )
    assert spend_by_category_response.status_code == 200
    spend_by_category = spend_by_category_response.json()["data"]
    assert spend_by_category == [
        {
            "category_id": dataset["categories"]["shopping"],
            "category_name": "Shopping",
            "amount": "1200.00",
            "transaction_count": 1,
        },
        {
            "category_id": dataset["categories"]["food"],
            "category_name": "Food & Dining",
            "amount": "500.00",
            "transaction_count": 1,
        },
    ]

    spend_by_card_response = client.get(
        "/api/v1/dashboard/spend-by-card",
        params={"from_date": "2026-03-01", "to_date": "2026-03-31"},
        headers=headers,
    )
    assert spend_by_card_response.status_code == 200
    spend_by_card = spend_by_card_response.json()["data"]
    assert spend_by_card == [
        {
            "card_id": dataset["cards"]["two"],
            "card_name": "Amex Gold",
            "amount": "1200.00",
            "transaction_count": 1,
        },
        {
            "card_id": dataset["cards"]["one"],
            "card_name": "HDFC Infinia",
            "amount": "500.00",
            "transaction_count": 1,
        },
    ]

    rewards_vs_charges_response = client.get(
        "/api/v1/dashboard/rewards-vs-charges",
        params={"from_date": "2026-03-01", "to_date": "2026-03-31"},
        headers=headers,
    )
    assert rewards_vs_charges_response.status_code == 200
    rewards_vs_charges = rewards_vs_charges_response.json()["data"]
    assert rewards_vs_charges == [
        {
            "card_id": dataset["cards"]["one"],
            "card_name": "HDFC Infinia",
            "total_spend": "500.00",
            "reward_value": "100.00",
            "charges": "50.00",
            "net_value": "50.00",
        },
        {
            "card_id": dataset["cards"]["two"],
            "card_name": "Amex Gold",
            "total_spend": "1200.00",
            "reward_value": "100.00",
            "charges": "999.00",
            "net_value": "-899.00",
        },
    ]

    monthly_trend_response = client.get(
        "/api/v1/dashboard/monthly-trend",
        params={"from_date": "2026-02-01", "to_date": "2026-03-31"},
        headers=headers,
    )
    assert monthly_trend_response.status_code == 200
    monthly_trend = monthly_trend_response.json()["data"]
    assert monthly_trend == [
        {
            "month": "2026-02-01",
            "total_spend": "1400.00",
            "reward_value": "60.00",
            "charges": "0.00",
            "net_value": "60.00",
        },
        {
            "month": "2026-03-01",
            "total_spend": "1700.00",
            "reward_value": "200.00",
            "charges": "1049.00",
            "net_value": "-849.00",
        },
    ]

    top_merchants_response = client.get(
        "/api/v1/dashboard/top-merchants",
        params={"from_date": "2026-03-01", "to_date": "2026-03-31"},
        headers=headers,
    )
    assert top_merchants_response.status_code == 200
    top_merchants = top_merchants_response.json()["data"]
    assert top_merchants[:2] == [
        {
            "merchant_name": "Amazon",
            "amount": "1200.00",
            "transaction_count": 1,
        },
        {
            "merchant_name": "Swiggy",
            "amount": "500.00",
            "transaction_count": 1,
        },
    ]


def test_card_analytics_endpoints_and_ownership(client) -> None:
    dataset = _seed_analytics_dataset(client)
    headers = dataset["owner_headers"]
    other_headers = dataset["other_headers"]

    card_summary_response = client.get(
        f"/api/v1/cards/{dataset['cards']['one']}/summary",
        params={"from_date": "2026-03-01", "to_date": "2026-03-31"},
        headers=headers,
    )
    assert card_summary_response.status_code == 200
    card_summary = card_summary_response.json()["data"]
    assert card_summary == {
        "card": {
            "id": dataset["cards"]["one"],
            "nickname": "HDFC Infinia",
            "last4": "1234",
            "issuer_name": "HDFC",
        },
        "total_spend": "500.00",
        "eligible_spend": "500.00",
        "reward_points": "200.00",
        "reward_value": "100.00",
        "charges": "50.00",
        "annual_fee": "0.00",
        "joining_fee": "0.00",
        "other_charges": "50.00",
        "net_value": "50.00",
    }

    card_trend_response = client.get(
        f"/api/v1/cards/{dataset['cards']['one']}/monthly-trend",
        params={"from_date": "2026-02-01", "to_date": "2026-03-31"},
        headers=headers,
    )
    assert card_trend_response.status_code == 200
    assert card_trend_response.json()["data"] == [
        {
            "month": "2026-02-01",
            "total_spend": "800.00",
            "reward_value": "60.00",
            "charges": "0.00",
            "net_value": "60.00",
        },
        {
            "month": "2026-03-01",
            "total_spend": "500.00",
            "reward_value": "100.00",
            "charges": "50.00",
            "net_value": "50.00",
        },
    ]

    card_transactions_response = client.get(
        f"/api/v1/cards/{dataset['cards']['one']}/transactions",
        headers=headers,
    )
    assert card_transactions_response.status_code == 200
    card_transactions_payload = card_transactions_response.json()
    assert card_transactions_payload["meta"] == {
        "page": 1,
        "page_size": 50,
        "total": 4,
        "total_pages": 1,
    }
    assert [item["id"] for item in card_transactions_payload["data"]] == [
        dataset["transactions"]["tax_charge"],
        dataset["transactions"]["duplicate"],
        dataset["transactions"]["swiggy"],
        dataset["transactions"]["dmart"],
    ]

    charge_only_response = client.get(
        f"/api/v1/cards/{dataset['cards']['one']}/transactions",
        params={"is_card_charge": "true"},
        headers=headers,
    )
    assert charge_only_response.status_code == 200
    assert [item["id"] for item in charge_only_response.json()["data"]] == [
        dataset["transactions"]["tax_charge"]
    ]

    search_response = client.get(
        f"/api/v1/cards/{dataset['cards']['one']}/transactions",
        params={"search": "swiggy"},
        headers=headers,
    )
    assert search_response.status_code == 200
    assert [item["id"] for item in search_response.json()["data"]] == [
        dataset["transactions"]["swiggy"]
    ]

    other_user_summary = client.get(
        f"/api/v1/cards/{dataset['cards']['one']}/summary",
        params={"from_date": "2026-03-01", "to_date": "2026-03-31"},
        headers=other_headers,
    )
    assert other_user_summary.status_code == 404
    assert other_user_summary.json()["error"]["code"] == "CARD_NOT_FOUND"

    other_user_transactions = client.get(
        f"/api/v1/cards/{dataset['cards']['one']}/transactions",
        headers=other_headers,
    )
    assert other_user_transactions.status_code == 404
    assert other_user_transactions.json()["error"]["code"] == "CARD_NOT_FOUND"

    invalid_dashboard_summary = client.get(
        "/api/v1/dashboard/summary",
        params={"from_date": "2026-03-01"},
        headers=headers,
    )
    assert invalid_dashboard_summary.status_code == 422
    assert invalid_dashboard_summary.json()["error"]["code"] == "VALIDATION_ERROR"

    unauthenticated_response = client.get("/api/v1/dashboard/spend-by-card")
    assert unauthenticated_response.status_code == 401
    assert unauthenticated_response.json()["error"]["code"] == "UNAUTHORIZED"
