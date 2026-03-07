from datetime import date
from decimal import Decimal
from uuid import UUID

from app.db.session import get_session
from app.models.category import Category
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.models.transaction_category_audit import TransactionCategoryAudit
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


def _create_category(client, headers: dict[str, str], *, name: str, group_name: str) -> str:
    response = client.post(
        "/api/v1/categories",
        json={"name": name, "group_name": group_name},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _card_payload(last4: str, nickname: str) -> dict:
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
        "reward_conversion_rate": "0.5000",
        "reward_rule_config_json": {"base_rate": 3},
    }


def _create_card(client, headers: dict[str, str], *, last4: str, nickname: str) -> str:
    response = client.post("/api/v1/cards", json=_card_payload(last4, nickname), headers=headers)
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _create_statement(
    client,
    headers: dict[str, str],
    *,
    card_id: str,
    file_name: str,
    statement_period_start: str,
    statement_period_end: str,
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

    response = client.post(
        "/api/v1/statements",
        json={
            "card_id": card_id,
            "file_name": file_name,
            "file_storage_key": file_storage_key,
            "file_type": "pdf",
            "statement_period_start": statement_period_start,
            "statement_period_end": statement_period_end,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


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
            duplicate_flag=False,
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


def _seed_transactions_dataset(client) -> dict[str, object]:
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

    owner_card_one_id = _create_card(client, owner_headers, last4="1234", nickname="HDFC Infinia")
    owner_card_two_id = _create_card(client, owner_headers, last4="5678", nickname="Amex Gold")
    other_card_id = _create_card(client, other_headers, last4="9999", nickname="Other Card")

    owner_statement_one_id = _create_statement(
        client,
        owner_headers,
        card_id=owner_card_one_id,
        file_name="owner_1.pdf",
        statement_period_start="2026-03-01",
        statement_period_end="2026-03-31",
    )
    owner_statement_two_id = _create_statement(
        client,
        owner_headers,
        card_id=owner_card_two_id,
        file_name="owner_2.pdf",
        statement_period_start="2026-03-01",
        statement_period_end="2026-03-31",
    )
    other_statement_id = _create_statement(
        client,
        other_headers,
        card_id=other_card_id,
        file_name="other.pdf",
        statement_period_start="2026-03-01",
        statement_period_end="2026-03-31",
    )

    transaction_ids = {
        "swiggy": _seed_transaction(
            user_id=owner_user_id,
            card_id=owner_card_one_id,
            statement_id=owner_statement_one_id,
            txn_date=date(2026, 3, 1),
            raw_description="SWIGGY BANGALORE",
            normalized_merchant="Swiggy",
            amount="540.00",
            txn_type="spend",
            category_id=food_category_id,
            category_source="rule",
            category_confidence="0.9600",
            review_required=False,
            is_card_charge=False,
            charge_type=None,
            source_hash="hash-swiggy",
        ),
        "tax": _seed_transaction(
            user_id=owner_user_id,
            card_id=owner_card_one_id,
            statement_id=owner_statement_one_id,
            txn_date=date(2026, 3, 2),
            raw_description="BANK CHARGE GST",
            normalized_merchant="Bank Charge GST",
            amount="270.00",
            txn_type="charge",
            category_id=tax_category_id,
            category_source="rule",
            category_confidence="0.9900",
            review_required=False,
            is_card_charge=True,
            charge_type="tax",
            source_hash="hash-tax",
        ),
        "amazon": _seed_transaction(
            user_id=owner_user_id,
            card_id=owner_card_two_id,
            statement_id=owner_statement_two_id,
            txn_date=date(2026, 3, 4),
            raw_description="AMAZON PAY",
            normalized_merchant="Amazon",
            amount="1200.00",
            txn_type="spend",
            category_id=shopping_category_id,
            category_source="history",
            category_confidence="0.6200",
            review_required=True,
            is_card_charge=False,
            charge_type=None,
            source_hash="hash-amazon",
        ),
        "annual_fee": _seed_transaction(
            user_id=owner_user_id,
            card_id=owner_card_two_id,
            statement_id=owner_statement_two_id,
            txn_date=date(2026, 3, 5),
            raw_description="ANNUAL FEE",
            normalized_merchant="Annual Fee",
            amount="999.00",
            txn_type="charge",
            category_id=annual_fee_category_id,
            category_source="rule",
            category_confidence="0.9800",
            review_required=False,
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
            amount="100.00",
            txn_type="spend",
            category_id=shopping_category_id,
            category_source="manual",
            category_confidence="1.0000",
            review_required=False,
            is_card_charge=False,
            charge_type=None,
            source_hash="hash-other-user",
        ),
    }

    return {
        "owner_headers": owner_headers,
        "owner_user_id": owner_user_id,
        "other_headers": other_headers,
        "cards": {
            "one": owner_card_one_id,
            "two": owner_card_two_id,
            "other": other_card_id,
        },
        "statements": {
            "one": owner_statement_one_id,
            "two": owner_statement_two_id,
            "other": other_statement_id,
        },
        "categories": {
            "food": food_category_id,
            "shopping": shopping_category_id,
            "annual_fee": annual_fee_category_id,
            "tax": tax_category_id,
        },
        "transactions": transaction_ids,
    }


def test_transactions_list_filters_pagination_sorting_and_detail(client) -> None:
    dataset = _seed_transactions_dataset(client)
    headers = dataset["owner_headers"]

    list_response = client.get("/api/v1/transactions", headers=headers)
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["error"] is None
    assert list_payload["meta"] == {
        "page": 1,
        "page_size": 50,
        "total": 4,
        "total_pages": 1,
    }
    assert [item["id"] for item in list_payload["data"]] == [
        dataset["transactions"]["annual_fee"],
        dataset["transactions"]["amazon"],
        dataset["transactions"]["tax"],
        dataset["transactions"]["swiggy"],
    ]

    card_filter = client.get(
        "/api/v1/transactions",
        params={"card_id": dataset["cards"]["one"]},
        headers=headers,
    )
    assert [item["id"] for item in card_filter.json()["data"]] == [
        dataset["transactions"]["tax"],
        dataset["transactions"]["swiggy"],
    ]

    category_filter = client.get(
        "/api/v1/transactions",
        params={"category_id": dataset["categories"]["shopping"]},
        headers=headers,
    )
    assert [item["id"] for item in category_filter.json()["data"]] == [dataset["transactions"]["amazon"]]

    statement_filter = client.get(
        "/api/v1/transactions",
        params={"statement_id": dataset["statements"]["two"]},
        headers=headers,
    )
    assert [item["id"] for item in statement_filter.json()["data"]] == [
        dataset["transactions"]["annual_fee"],
        dataset["transactions"]["amazon"],
    ]

    date_filter = client.get(
        "/api/v1/transactions",
        params={
            "from_date": "2026-03-02",
            "to_date": "2026-03-04",
        },
        headers=headers,
    )
    assert [item["id"] for item in date_filter.json()["data"]] == [
        dataset["transactions"]["amazon"],
        dataset["transactions"]["tax"],
    ]

    search_filter = client.get(
        "/api/v1/transactions",
        params={"search": "amazon"},
        headers=headers,
    )
    assert [item["id"] for item in search_filter.json()["data"]] == [dataset["transactions"]["amazon"]]

    review_filter = client.get(
        "/api/v1/transactions",
        params={"review_required": "true"},
        headers=headers,
    )
    assert [item["id"] for item in review_filter.json()["data"]] == [dataset["transactions"]["amazon"]]

    charge_filter = client.get(
        "/api/v1/transactions",
        params={
            "is_card_charge": "true",
            "charge_type": "annual_fee",
        },
        headers=headers,
    )
    assert [item["id"] for item in charge_filter.json()["data"]] == [
        dataset["transactions"]["annual_fee"]
    ]

    pagination_filter = client.get(
        "/api/v1/transactions",
        params={
            "page": 2,
            "page_size": 2,
            "sort_by": "amount",
            "sort_order": "desc",
        },
        headers=headers,
    )
    pagination_payload = pagination_filter.json()
    assert pagination_payload["meta"] == {
        "page": 2,
        "page_size": 2,
        "total": 4,
        "total_pages": 2,
    }
    assert [item["id"] for item in pagination_payload["data"]] == [
        dataset["transactions"]["swiggy"],
        dataset["transactions"]["tax"],
    ]

    detail_response = client.get(
        f"/api/v1/transactions/{dataset['transactions']['swiggy']}",
        headers=headers,
    )
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["data"]["card_name"] == "HDFC Infinia"
    assert detail_payload["data"]["category"] == {
        "id": dataset["categories"]["food"],
        "name": "Food & Dining",
    }


def test_transaction_patch_updates_category_creates_audit_and_rule(client) -> None:
    dataset = _seed_transactions_dataset(client)
    headers = dataset["owner_headers"]
    custom_category_id = _create_category(
        client,
        headers,
        name="Dining Out",
        group_name="spend",
    )

    patch_response = client.patch(
        f"/api/v1/transactions/{dataset['transactions']['swiggy']}",
        json={
            "category_id": custom_category_id,
            "review_required": False,
            "create_rule": True,
            "rule_match_type": "description_contains",
            "rule_match_value": "SWIGGY",
        },
        headers=headers,
    )
    assert patch_response.status_code == 200
    patch_payload = patch_response.json()
    assert patch_payload["error"] is None
    assert patch_payload["data"]["category"] == {
        "id": custom_category_id,
        "name": "Dining Out",
    }
    assert patch_payload["data"]["category_source"] == "manual"
    assert Decimal(str(patch_payload["data"]["category_confidence"])) == Decimal("1.0000")
    assert patch_payload["data"]["review_required"] is False

    rules_response = client.get("/api/v1/rules", headers=headers)
    assert rules_response.status_code == 200
    rules_payload = rules_response.json()
    assert len(rules_payload["data"]) == 1
    assert rules_payload["data"][0]["match_type"] == "description_contains"
    assert rules_payload["data"][0]["match_value"] == "SWIGGY"
    assert rules_payload["data"][0]["assigned_category_id"] == custom_category_id

    with get_session() as session:
        audits = session.query(TransactionCategoryAudit).all()
        assert len(audits) == 1
        assert str(audits[0].transaction_id) == dataset["transactions"]["swiggy"]
        assert str(audits[0].old_category_id) == dataset["categories"]["food"]
        assert str(audits[0].new_category_id) == custom_category_id
        assert audits[0].changed_by == "user"
        assert audits[0].source == "manual_patch"


def test_transactions_bulk_update_creates_audits_and_enforces_ownership(client) -> None:
    dataset = _seed_transactions_dataset(client)
    headers = dataset["owner_headers"]
    custom_category_id = _create_category(
        client,
        headers,
        name="Reviewed Spend",
        group_name="spend",
    )

    bulk_response = client.post(
        "/api/v1/transactions/bulk-update",
        json={
            "transaction_ids": [
                dataset["transactions"]["swiggy"],
                dataset["transactions"]["amazon"],
            ],
            "category_id": custom_category_id,
            "review_required": False,
        },
        headers=headers,
    )
    assert bulk_response.status_code == 200
    bulk_payload = bulk_response.json()
    assert bulk_payload["error"] is None
    assert bulk_payload["data"] == {
        "updated_count": 2,
        "audit_count": 2,
    }

    with get_session() as session:
        transactions = (
            session.query(Transaction)
            .filter(
                Transaction.id.in_(
                    [
                        UUID(dataset["transactions"]["swiggy"]),
                        UUID(dataset["transactions"]["amazon"]),
                    ]
                )
            )
            .order_by(Transaction.txn_date.asc())
            .all()
        )
        assert len(transactions) == 2
        assert all(str(transaction.category_id) == custom_category_id for transaction in transactions)
        assert all(transaction.review_required is False for transaction in transactions)

        audits = (
            session.query(TransactionCategoryAudit)
            .filter(
                TransactionCategoryAudit.transaction_id.in_(
                    [
                        UUID(dataset["transactions"]["swiggy"]),
                        UUID(dataset["transactions"]["amazon"]),
                    ]
                )
            )
            .all()
        )
        assert len(audits) == 2
        assert {audit.source for audit in audits} == {"bulk_update"}

    missing_response = client.post(
        "/api/v1/transactions/bulk-update",
        json={
            "transaction_ids": [
                dataset["transactions"]["swiggy"],
                dataset["transactions"]["other_user"],
            ],
            "review_required": False,
        },
        headers=headers,
    )
    assert missing_response.status_code == 404
    assert missing_response.json()["error"]["code"] == "TRANSACTION_NOT_FOUND"


def test_transaction_routes_require_authentication_and_enforce_ownership(client) -> None:
    dataset = _seed_transactions_dataset(client)

    list_response = client.get("/api/v1/transactions")
    assert list_response.status_code == 401
    assert list_response.json()["error"]["code"] == "UNAUTHORIZED"

    other_headers = dataset["other_headers"]
    owner_headers = dataset["owner_headers"]

    other_detail = client.get(
        f"/api/v1/transactions/{dataset['transactions']['swiggy']}",
        headers=other_headers,
    )
    assert other_detail.status_code == 404
    assert other_detail.json()["error"]["code"] == "TRANSACTION_NOT_FOUND"

    other_patch = client.patch(
        f"/api/v1/transactions/{dataset['transactions']['swiggy']}",
        json={"review_required": False},
        headers=other_headers,
    )
    assert other_patch.status_code == 404
    assert other_patch.json()["error"]["code"] == "TRANSACTION_NOT_FOUND"

    invalid_filter = client.get(
        "/api/v1/transactions",
        params={"from_date": "2026-03-10", "to_date": "2026-03-01"},
        headers=owner_headers,
    )
    assert invalid_filter.status_code == 422
    assert invalid_filter.json()["error"]["code"] == "VALIDATION_ERROR"

    statement_delete = client.delete(
        f"/api/v1/statements/{dataset['statements']['one']}",
        headers=owner_headers,
    )
    assert statement_delete.status_code == 409
    assert statement_delete.json()["error"]["code"] == "STATEMENT_DELETE_NOT_ALLOWED"
