# Credit Card Spend Tracker — Wireframes, Backend Schema, and API Contracts

## 1. Scope

This document extends the PRD and defines:

1. low-fidelity wireframes for each core page
2. backend schema for MVP
3. API contracts for frontend-backend integration

The focus is an MVP for:
- multi-card management
- statement uploads
- transaction extraction
- AI-assisted categorization
- rewards and charges tracking
- dashboard and card-level insights

---

# 2. Information Architecture

## Main Pages

1. Login / Signup
2. Onboarding
3. Dashboard
4. Cards List
5. Card Detail
6. Statement Upload
7. Statement History
8. Transactions Explorer
9. Categories & Rules
10. Rewards & Charges Summary
11. Settings

## Global Navigation

- Dashboard
- Cards
- Upload Statements
- Transactions
- Categories
- Statements
- Settings

---

# 3. Low-Fidelity Wireframes

## 3.1 Login / Signup

### Purpose
Allow user authentication and account creation.

### Wireframe

```text
+--------------------------------------------------------------+
| SpendSense                                                   |
|--------------------------------------------------------------|
|                 Track your cards in one place                |
|                                                              |
|   [ Email ________________________________ ]                 |
|   [ Password _____________________________ ]                 |
|                                                              |
|   [ Sign In ]                        [ Continue with Google ]|
|                                                              |
|   Don't have an account? [ Sign Up ]                         |
+--------------------------------------------------------------+
```

### Key Actions
- Sign in
- Sign up
- OAuth login

---

## 3.2 Onboarding

### Purpose
Collect first card and optional preferences.

### Wireframe

```text
+--------------------------------------------------------------+
| Welcome to SpendSense                                        |
|--------------------------------------------------------------|
| Step 1: Add your first card                                  |
|                                                              |
| Card Nickname      [ HDFC Infinia____________ ]              |
| Issuer             [ HDFC____________________ ]              |
| Last 4 digits      [ 1234____________________ ]              |
| Network            [ Visa v ]                                |
| Annual Fee         [ 12500___________________ ]              |
| Joining Fee        [ 12500___________________ ]              |
| Reward Type        [ Points v ]                              |
|                                                              |
|                [ Skip ]    [ Save and Continue ]             |
+--------------------------------------------------------------+
```

### Key Actions
- Add first card
- Skip onboarding

---

## 3.3 Dashboard

### Purpose
Show overall monthly performance across spending, rewards, and charges.

### Wireframe

```text
+----------------------------------------------------------------------------------+
| Logo | Dashboard | Cards | Upload | Transactions | Categories | Settings | User |
|----------------------------------------------------------------------------------|
| Filters: [This Month v] [All Cards v] [All Categories v] [Export]                |
|----------------------------------------------------------------------------------|
| [Total Spend]   [Rewards Value]   [Charges Paid]   [Net Card Value]              |
| ₹1,24,000       ₹8,400            ₹3,200           ₹5,200                        |
|----------------------------------------------------------------------------------|
| Spend by Category              | Spend by Card                                   |
| [Donut Chart]                  | [Bar Chart]                                     |
|----------------------------------------------------------------------------------|
| Rewards vs Charges by Card     | Monthly Spend Trend                             |
| [Grouped Bar Chart]            | [Line Chart]                                    |
|----------------------------------------------------------------------------------|
| Top Merchants                  | Needs Review                                    |
| Swiggy ₹12,400                 | 14 low-confidence transactions                  |
| Amazon ₹18,000                 | [Review Now]                                    |
| DMart ₹7,500                   |                                                 |
+----------------------------------------------------------------------------------+
```

### Widgets
- total spend
- rewards earned/value
- charges paid
- net value
- category chart
- card chart
- rewards vs charges chart
- trends
- needs review queue

---

## 3.4 Cards List

### Purpose
Show all cards with quick summary.

### Wireframe

```text
+----------------------------------------------------------------------------------+
| Cards                                                               [ Add Card ] |
|----------------------------------------------------------------------------------|
| Search [____________________]                                                    |
|----------------------------------------------------------------------------------|
| [Card Tile] HDFC Infinia                                                         |
| Last4: 1234 | Spend: ₹54,000 | Rewards: 8,200 pts | Charges: ₹1,500             |
| Net Value: ₹3,900                                     [View] [Edit] [Archive]    |
|----------------------------------------------------------------------------------|
| [Card Tile] Amex Gold                                                            |
| Last4: 6789 | Spend: ₹22,000 | Rewards: 2,100 pts | Charges: ₹0                 |
| Net Value: ₹1,200                                     [View] [Edit] [Archive]    |
+----------------------------------------------------------------------------------+
```

### Key Actions
- Add card
- Edit card
- Open card detail
- Archive card

---

## 3.5 Card Detail

### Purpose
Drill into one card’s performance.

### Wireframe

```text
+----------------------------------------------------------------------------------+
| HDFC Infinia                                                      [Edit Card]    |
|----------------------------------------------------------------------------------|
| Last 4: 1234 | Issuer: HDFC | Reward Type: Points | Annual Fee: ₹12,500         |
|----------------------------------------------------------------------------------|
| [Total Spend] [Eligible Spend] [Reward Points] [Reward Value] [Charges]         |
| ₹54,000       ₹48,000         8,200           ₹4,100          ₹1,500             |
|----------------------------------------------------------------------------------|
| Monthly Spend Trend              | Rewards Trend                                 |
| [Line Chart]                     | [Line Chart]                                  |
|----------------------------------------------------------------------------------|
| Charges Breakdown                | Recent Transactions                           |
| Annual Fee ₹0                    | 01 Mar  Swiggy        ₹540    Food           |
| Joining Fee ₹0                   | 03 Mar  Annual Fee    ₹1,500  Annual Fee     |
| Finance Charge ₹0                | 04 Mar  Amazon        ₹2,300  Shopping       |
| Other Charges ₹1,500             |                          [View All]          |
|----------------------------------------------------------------------------------|
| Reward Events                                                                   |
| 05 Mar  Earned    1,200 pts   Statement Imported                                |
| 10 Mar  Adjusted    300 pts   Manual                                             |
+----------------------------------------------------------------------------------+
```

### Key Actions
- View spend, reward, and fee performance
- See transactions for the card
- Add reward adjustment

---

## 3.6 Statement Upload

### Purpose
Upload statements and attach them to cards.

### Wireframe

```text
+----------------------------------------------------------------------------+
| Upload Statement                                                           |
|----------------------------------------------------------------------------|
| Card                [ Select Card v ]                                      |
| Statement Period    [ 01-Feb-2026 ] to [ 28-Feb-2026 ]                    |
| File                [ Choose File ]                                        |
|                                                                            |
| Drag & drop PDF / CSV here                                                 |
|                                                                            |
|                              [ Upload ]                                    |
|----------------------------------------------------------------------------|
| Recent Uploads                                                              |
| HDFC Infinia | Feb 2026 | Processing | 124 txns                             |
| Amex Gold    | Feb 2026 | Done       |  58 txns                             |
+----------------------------------------------------------------------------+
```

### Key Actions
- Upload file
- Select card and period
- View status

---

## 3.7 Statement History

### Purpose
Audit uploaded files and processing history.

### Wireframe

```text
+----------------------------------------------------------------------------------+
| Statements                                                                      |
|----------------------------------------------------------------------------------|
| Filters: [All Cards v] [All Status v] [Month v]                                 |
|----------------------------------------------------------------------------------|
| Card         | Period      | File Name         | Status      | Txns | Actions    |
| HDFC Infinia | Feb 2026    | hdfc_feb.pdf      | Completed   | 124  | View Retry |
| Amex Gold    | Feb 2026    | amex_feb.pdf      | Failed      |  0   | View Retry |
| SBI Cashback | Jan 2026    | sbi_jan.csv       | Completed   |  92  | View Delete|
+----------------------------------------------------------------------------------+
```

### Key Actions
- View details
- Retry processing
- Delete import

---

## 3.8 Transactions Explorer

### Purpose
Browse and edit all transactions.

### Wireframe

```text
+------------------------------------------------------------------------------------------------+
| Transactions                                                                                   |
|------------------------------------------------------------------------------------------------|
| Search [merchant / description____________________]                                            |
| Filters: [Card v] [Category v] [Month v] [Charges only] [Needs Review] [Export]               |
|------------------------------------------------------------------------------------------------|
| Date     | Card         | Merchant        | Amount  | Category      | Confidence | Action     |
| 01-Mar   | HDFC Infinia | Swiggy          | ₹540    | Food          | 0.96       | Edit       |
| 02-Mar   | HDFC Infinia | BANK CHARGE GST | ₹270    | Tax on Charge | 0.99       | Edit       |
| 04-Mar   | Amex Gold    | AMAZON PAY      | ₹1,200  | Shopping      | 0.62       | Review     |
| 05-Mar   | SBI Cashback | Annual Fee      | ₹999    | Annual Fee    | 0.98       | Edit       |
|------------------------------------------------------------------------------------------------|
| Bulk Actions: [Assign Category v] [Mark Reviewed] [Create Rule]                                |
+------------------------------------------------------------------------------------------------+
```

### Key Actions
- Search and filter
- Edit category
- Bulk update
- Create rule

---

## 3.9 Categories & Rules

### Purpose
Manage category taxonomy and reusable rules.

### Wireframe

```text
+----------------------------------------------------------------------------------+
| Categories & Rules                                              [ Add Category ] |
|----------------------------------------------------------------------------------|
| Categories                                                                        |
| Food & Dining            [Edit] [Archive]                                         |
| Shopping                 [Edit] [Archive]                                         |
| Annual Fee               [Edit] [Archive]                                         |
| Joining Fee              [Edit] [Archive]                                         |
|----------------------------------------------------------------------------------|
| Rules                                                                             |
| If description contains 'SWIGGY'      => Food & Dining        [Edit] [Disable]   |
| If description contains 'ANNUAL FEE'  => Annual Fee           [Edit] [Disable]   |
| If merchant contains 'AMAZON'         => Shopping             [Edit] [Disable]   |
+----------------------------------------------------------------------------------+
```

### Key Actions
- Add category
- Edit/disable rule
- Archive category

---

## 3.10 Rewards & Charges Summary

### Purpose
Compare cards by value creation and fee leakage.

### Wireframe

```text
+----------------------------------------------------------------------------------+
| Rewards & Charges                                                                |
|----------------------------------------------------------------------------------|
| Filters: [This Year v] [All Cards v]                                             |
|----------------------------------------------------------------------------------|
| Card         | Spend     | Reward Points | Reward Value | Charges | Net Value   |
| HDFC Infinia | ₹5,20,000 | 72,000        | ₹36,000      | ₹12,500 | ₹23,500     |
| Amex Gold    | ₹2,40,000 | 18,000        | ₹ 9,000      | ₹ 4,500 | ₹ 4,500     |
| SBI Cashback | ₹1,80,000 | Cashback only | ₹ 8,700      | ₹   999 | ₹ 7,701     |
|----------------------------------------------------------------------------------|
| [Rewards by Card Chart]               | [Charges by Type Chart]                  |
+----------------------------------------------------------------------------------+
```

### Key Actions
- Compare card economics
- Drill into a card

---

## 3.11 Settings

### Purpose
Manage profile, privacy, import, and preferences.

### Wireframe

```text
+----------------------------------------------------------------------------------+
| Settings                                                                         |
|----------------------------------------------------------------------------------|
| Profile                                                                          |
| Name      [____________________]                                                 |
| Email     [____________________]                                                 |
|----------------------------------------------------------------------------------|
| Preferences                                                                      |
| Default Currency [INR v]                                                         |
| Statement Date Format [DD-MM-YYYY v]                                             |
|----------------------------------------------------------------------------------|
| Data                                                                             |
| [ Export Transactions ]                                                          |
| [ Delete Account ]                                                               |
+----------------------------------------------------------------------------------+
```

---

# 4. Backend Schema

## 4.1 Design Notes

- PostgreSQL recommended for MVP
- Use UUID primary keys
- Store money in minor units or numeric(18,2)
- Maintain auditability for imports and recategorizations
- Keep reward events separate from transaction table where possible

---

## 4.2 Entities

## users

| column | type | notes |
|---|---|---|
| id | uuid pk | primary key |
| email | varchar unique | login email |
| password_hash | varchar | nullable if OAuth |
| full_name | varchar | |
| auth_provider | varchar | local/google |
| created_at | timestamptz | |
| updated_at | timestamptz | |

## cards

| column | type | notes |
|---|---|---|
| id | uuid pk | |
| user_id | uuid fk users.id | owner |
| nickname | varchar | display name |
| issuer_name | varchar | bank name |
| network | varchar | visa/mastercard/amex/etc |
| last4 | varchar(4) | |
| statement_cycle_day | int | nullable |
| annual_fee_expected | numeric(12,2) | nullable |
| joining_fee_expected | numeric(12,2) | nullable |
| reward_program_name | varchar | nullable |
| reward_type | varchar | points/cashback/miles |
| reward_conversion_rate | numeric(12,4) | optional |
| reward_rule_config_json | jsonb | optional |
| status | varchar | active/archived |
| created_at | timestamptz | |
| updated_at | timestamptz | |

## statements

| column | type | notes |
|---|---|---|
| id | uuid pk | |
| user_id | uuid fk users.id | |
| card_id | uuid fk cards.id | |
| file_name | varchar | |
| file_storage_key | varchar | blob location |
| file_type | varchar | pdf/csv/xlsx |
| statement_period_start | date | |
| statement_period_end | date | |
| upload_status | varchar | uploaded/processing/completed/failed |
| extraction_status | varchar | pending/running/completed/failed |
| categorization_status | varchar | pending/running/completed/failed |
| transaction_count | int | |
| processing_error | text | nullable |
| uploaded_at | timestamptz | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

## categories

| column | type | notes |
|---|---|---|
| id | uuid pk | |
| user_id | uuid fk users.id | null for system default optional |
| name | varchar | |
| slug | varchar | |
| group_name | varchar | spend/charges/rewards |
| is_default | boolean | |
| is_archived | boolean | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

## transactions

| column | type | notes |
|---|---|---|
| id | uuid pk | |
| user_id | uuid fk users.id | |
| card_id | uuid fk cards.id | |
| statement_id | uuid fk statements.id | |
| txn_date | date | |
| posted_date | date | nullable |
| raw_description | text | original line |
| normalized_merchant | varchar | normalized merchant |
| amount | numeric(12,2) | positive stored with type |
| currency | varchar(3) | default INR |
| txn_direction | varchar | debit/credit |
| txn_type | varchar | spend/refund/charge/reward/manual_adjustment |
| category_id | uuid fk categories.id | nullable pre-classification |
| category_source | varchar | rule/history/llm/manual |
| category_confidence | numeric(5,4) | 0-1 |
| category_explanation | text | optional |
| review_required | boolean | |
| duplicate_flag | boolean | |
| is_card_charge | boolean | |
| charge_type | varchar | annual_fee/joining_fee/late_fee/etc |
| is_reward_related | boolean | |
| reward_points_delta | numeric(12,2) | nullable |
| cashback_amount | numeric(12,2) | nullable |
| source_hash | varchar | for dedupe |
| metadata_json | jsonb | parser output |
| created_at | timestamptz | |
| updated_at | timestamptz | |

## categorization_rules

| column | type | notes |
|---|---|---|
| id | uuid pk | |
| user_id | uuid fk users.id | |
| rule_name | varchar | |
| match_type | varchar | description_contains / merchant_equals / regex |
| match_value | varchar | |
| assigned_category_id | uuid fk categories.id | |
| priority | int | lower number = higher priority |
| is_active | boolean | |
| created_from_transaction_id | uuid fk transactions.id | nullable |
| created_at | timestamptz | |
| updated_at | timestamptz | |

## transaction_category_audit

| column | type | notes |
|---|---|---|
| id | uuid pk | |
| transaction_id | uuid fk transactions.id | |
| old_category_id | uuid fk categories.id | nullable |
| new_category_id | uuid fk categories.id | |
| changed_by | varchar | user/system |
| source | varchar | manual_patch/bulk_update/etc |
| created_at | timestamptz | |

## reward_ledgers

| column | type | notes |
|---|---|---|
| id | uuid pk | |
| user_id | uuid fk users.id | |
| card_id | uuid fk cards.id | |
| statement_id | uuid fk statements.id | nullable |
| event_date | date | |
| event_type | varchar | earned/redeemed/expired/adjusted/cashback |
| reward_points | numeric(12,2) | nullable |
| reward_value_estimate | numeric(12,2) | nullable |
| source | varchar | manual/extracted/estimated |
| notes | text | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

## card_charge_summaries

| column | type | notes |
|---|---|---|
| id | uuid pk | |
| user_id | uuid fk users.id | |
| card_id | uuid fk cards.id | |
| period_month | date | use first day of month |
| annual_fee_amount | numeric(12,2) | default 0 |
| joining_fee_amount | numeric(12,2) | default 0 |
| late_fee_amount | numeric(12,2) | default 0 |
| finance_charge_amount | numeric(12,2) | default 0 |
| emi_processing_fee_amount | numeric(12,2) | default 0 |
| cash_advance_fee_amount | numeric(12,2) | default 0 |
| forex_markup_amount | numeric(12,2) | default 0 |
| tax_amount | numeric(12,2) | default 0 |
| other_charge_amount | numeric(12,2) | default 0 |
| total_charge_amount | numeric(12,2) | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

---

## 4.3 Suggested Indexes

### cards
- index on (user_id, status)

### statements
- index on (user_id, card_id)
- index on (statement_period_start, statement_period_end)
- index on (upload_status, extraction_status)

### transactions
- index on (user_id, txn_date desc)
- index on (user_id, card_id, txn_date desc)
- index on (user_id, category_id, txn_date desc)
- index on (statement_id)
- unique or semi-unique index on (user_id, source_hash)
- index on (review_required)
- index on (is_card_charge, charge_type)

### rules
- index on (user_id, is_active, priority)

### reward_ledgers
- index on (user_id, card_id, event_date desc)

---

# 5. API Contracts

## 5.1 API Conventions

- Base URL: `/api/v1`
- Auth: Bearer token / session token
- Response format: JSON
- All list APIs support pagination where relevant
- Dates: ISO 8601
- Currency values in decimal strings or numeric JSON values consistently

### Standard Response Envelope

```json
{
  "data": {},
  "meta": {},
  "error": null
}
```

### Error Format

```json
{
  "data": null,
  "meta": {},
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "card_id is required",
    "details": {
      "field": "card_id"
    }
  }
}
```

---

## 5.2 Auth APIs

### POST /auth/signup

#### Request
```json
{
  "email": "user@example.com",
  "password": "strong-password",
  "full_name": "Ashutosh"
}
```

#### Response
```json
{
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "Ashutosh"
    },
    "token": "jwt-token"
  },
  "meta": {},
  "error": null
}
```

### POST /auth/login

#### Request
```json
{
  "email": "user@example.com",
  "password": "strong-password"
}
```

### GET /auth/me
Returns current user profile.

---

## 5.3 Cards APIs

### GET /cards
List all cards for user.

#### Response
```json
{
  "data": [
    {
      "id": "uuid",
      "nickname": "HDFC Infinia",
      "issuer_name": "HDFC",
      "network": "visa",
      "last4": "1234",
      "reward_type": "points",
      "annual_fee_expected": 12500,
      "joining_fee_expected": 12500,
      "status": "active"
    }
  ],
  "meta": {},
  "error": null
}
```

### POST /cards
Create card.

#### Request
```json
{
  "nickname": "HDFC Infinia",
  "issuer_name": "HDFC",
  "network": "visa",
  "last4": "1234",
  "statement_cycle_day": 12,
  "annual_fee_expected": 12500,
  "joining_fee_expected": 12500,
  "reward_program_name": "Infinia Rewards",
  "reward_type": "points",
  "reward_conversion_rate": 0.5
}
```

### GET /cards/{card_id}
Get one card.

### PATCH /cards/{card_id}
Update card metadata.

### DELETE /cards/{card_id}
Soft archive card.

---

## 5.4 Statements APIs

### POST /statements
Upload statement metadata and file reference.

Recommended implementation:
1. `POST /uploads/presign`
2. frontend uploads to storage
3. `POST /statements` with storage key

#### Request
```json
{
  "card_id": "uuid",
  "file_name": "hdfc_feb_2026.pdf",
  "file_storage_key": "statements/user-1/hdfc_feb_2026.pdf",
  "file_type": "pdf",
  "statement_period_start": "2026-02-01",
  "statement_period_end": "2026-02-28"
}
```

#### Response
```json
{
  "data": {
    "id": "uuid",
    "upload_status": "uploaded",
    "extraction_status": "pending",
    "categorization_status": "pending"
  },
  "meta": {},
  "error": null
}
```

### GET /statements
List statements.

#### Query Params
- card_id
- status
- month (`YYYY-MM`, matched against overlapping statement periods)
- page
- page_size

### GET /statements/{statement_id}
Get statement details.

### POST /statements/{statement_id}/retry
Retry failed processing.

### DELETE /statements/{statement_id}
Delete statement and optionally imported transactions based on policy.

Current MVP delete policy for the metadata-only slice:
- block deletion when imported transactions are linked to the statement
- otherwise delete the statement metadata row only
- do not delete a file blob when using the local fake storage backend

---

## 5.5 Transactions APIs

### GET /transactions
List transactions with filters.

#### Query Params
- card_id
- category_id
- statement_id
- from_date
- to_date
- search
- review_required
- is_card_charge
- charge_type
- page
- page_size
- sort_by
- sort_order

#### Response
```json
{
  "data": [
    {
      "id": "uuid",
      "txn_date": "2026-03-01",
      "card_id": "uuid",
      "card_name": "HDFC Infinia",
      "raw_description": "SWIGGY BANGALORE",
      "normalized_merchant": "Swiggy",
      "amount": 540,
      "currency": "INR",
      "txn_type": "spend",
      "category": {
        "id": "uuid",
        "name": "Food & Dining"
      },
      "category_source": "rule",
      "category_confidence": 0.96,
      "review_required": false,
      "is_card_charge": false,
      "charge_type": null
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 50,
    "total": 642
  },
  "error": null
}
```

### GET /transactions/{transaction_id}
Get one transaction.

### PATCH /transactions/{transaction_id}
Update category or review state.

#### Request
```json
{
  "category_id": "uuid",
  "review_required": false,
  "create_rule": true,
  "rule_match_type": "description_contains",
  "rule_match_value": "SWIGGY"
}
```

### POST /transactions/bulk-update
Bulk update multiple transactions.

#### Request
```json
{
  "transaction_ids": ["uuid1", "uuid2"],
  "category_id": "uuid",
  "review_required": false
}
```

#### Response
```json
{
  "data": {
    "updated_count": 2,
    "audit_count": 2
  },
  "meta": {},
  "error": null
}
```

---

## 5.6 Categories APIs

### GET /categories
List default and custom categories.

### POST /categories
Create category.

#### Request
```json
{
  "name": "Office Supplies",
  "group_name": "spend"
}
```

### PATCH /categories/{category_id}
Rename or archive category.

### DELETE /categories/{category_id}
Soft delete/archive category.

---

## 5.7 Rules APIs

### GET /rules
List categorization rules.

### POST /rules
Create rule.

#### Request
```json
{
  "rule_name": "Swiggy to Food",
  "match_type": "description_contains",
  "match_value": "SWIGGY",
  "assigned_category_id": "uuid",
  "priority": 10,
  "is_active": true
}
```

### PATCH /rules/{rule_id}
Update rule.

### DELETE /rules/{rule_id}
Disable rule.

---

## 5.8 Rewards APIs

### GET /cards/{card_id}/rewards
Get reward summary for one card.

#### Response
```json
{
  "data": {
    "card_id": "uuid",
    "reward_type": "points",
    "total_points_earned": 8200,
    "total_points_redeemed": 1000,
    "total_points_expired": 0,
    "estimated_reward_value": 4100,
    "current_balance": 7200
  },
  "meta": {},
  "error": null
}
```

### GET /reward-ledgers
List reward events.

#### Query Params
- card_id
- event_type
- from_date
- to_date

### POST /reward-ledgers
Create manual reward event.

#### Request
```json
{
  "card_id": "uuid",
  "event_date": "2026-03-05",
  "event_type": "earned",
  "reward_points": 1200,
  "reward_value_estimate": 600,
  "source": "manual",
  "notes": "Entered from statement summary"
}
```

### PATCH /reward-ledgers/{reward_ledger_id}
Update reward event.

### DELETE /reward-ledgers/{reward_ledger_id}
Delete reward event.

---

## 5.9 Dashboard APIs

### GET /dashboard/summary
Get overall dashboard summary.

#### Query Params
- from_date
- to_date
- card_id
- category_id

#### Response
```json
{
  "data": {
    "total_spend": 124000,
    "previous_period_spend": 110000,
    "spend_change_pct": 12.73,
    "total_rewards_value": 8400,
    "total_charges": 3200,
    "net_card_value": 5200,
    "transaction_count": 182,
    "needs_review_count": 14,
    "top_category": {
      "name": "Shopping",
      "amount": 42000
    },
    "top_card": {
      "card_id": "uuid",
      "name": "HDFC Infinia",
      "amount": 54000
    }
  },
  "meta": {},
  "error": null
}
```

### GET /dashboard/spend-by-category
Returns category aggregation.

### GET /dashboard/spend-by-card
Returns card aggregation.

### GET /dashboard/rewards-vs-charges
Returns reward vs charges per card.

#### Response
```json
{
  "data": [
    {
      "card_id": "uuid",
      "card_name": "HDFC Infinia",
      "total_spend": 54000,
      "reward_value": 4100,
      "charges": 1500,
      "net_value": 2600
    }
  ],
  "meta": {},
  "error": null
}
```

### GET /dashboard/monthly-trend
Returns monthly spend/reward/charge trend.

### GET /dashboard/top-merchants
Returns merchant aggregation.

---

## 5.10 Card Detail APIs

### GET /cards/{card_id}/summary
Get detailed card KPIs.

#### Response
```json
{
  "data": {
    "card": {
      "id": "uuid",
      "nickname": "HDFC Infinia",
      "last4": "1234",
      "issuer_name": "HDFC"
    },
    "total_spend": 54000,
    "eligible_spend": 48000,
    "reward_points": 8200,
    "reward_value": 4100,
    "charges": 1500,
    "annual_fee": 0,
    "joining_fee": 0,
    "other_charges": 1500,
    "net_value": 2600
  },
  "meta": {},
  "error": null
}
```

### GET /cards/{card_id}/transactions
Card-scoped transactions.

### GET /cards/{card_id}/charges
Charge breakdown.

### GET /cards/{card_id}/monthly-trend
Monthly trend for spend, rewards, charges.

---

## 5.11 Upload APIs

### POST /uploads/presign
Get pre-signed upload URL.

#### Request
```json
{
  "file_name": "hdfc_feb_2026.pdf",
  "content_type": "application/pdf"
}
```

#### Response
```json
{
  "data": {
    "upload_url": "local-fake://statements/<user-id>/<generated-file-name>",
    "file_storage_key": "statements/user-1/hdfc_feb_2026.pdf"
  },
  "meta": {},
  "error": null
}
```

---

# 6. Suggested Backend Workflows

## 6.1 Statement Processing Workflow

1. User uploads statement
2. Statement record created
3. Async job picks statement
4. Parser extracts raw transaction rows
5. Normalization layer standardizes merchant, date, amount
6. Deduplication runs via source_hash and similarity rules
7. Rule engine assigns obvious categories and charges
8. LLM handles ambiguous rows
9. Dashboard aggregations refreshed
10. Statement marked completed

## 6.2 Manual Category Correction Workflow

1. User updates transaction category
2. Audit record created
3. Optional new rule created
4. Dashboard aggregates recalculated

## 6.3 Reward Entry Workflow

1. User manually adds reward ledger entry
2. Card summary recomputed
3. Dashboard reward vs charge metrics refreshed

---

# 7. Recommended MVP Endpoint Priority

## Phase 1 Must Build
- auth
- cards CRUD
- uploads/presign
- statements create/list/detail
- transactions list/detail/update/bulk update
- categories CRUD
- rules CRUD
- dashboard summary + aggregations
- card detail summary
- reward ledger create/list

## Phase 2
- statement retry/delete policies
- advanced reward extraction APIs
- card comparison endpoint
- export endpoints

---

# 8. Recommended Frontend Components

## Shared Components
- sidebar navigation
- top filter bar
- KPI card
- chart card
- transaction table
- upload dropzone
- status pill
- category select dropdown
- rule builder modal
- card summary tile

## Page-Specific Components
- dashboard charts
- card performance panel
- reward ledger table
- statement processing timeline

---

# 9. Implementation Notes

## Suggested Stack
- Frontend: Next.js + TypeScript + Tailwind
- Backend: FastAPI or NestJS
- DB: PostgreSQL
- Async jobs: Celery / RQ / Temporal
- Storage: S3-compatible object storage
- Auth: JWT or session-based auth

## LLM Layer Suggestion
- deterministic rules first
- LLM only for ambiguous descriptions
- maintain user-specific mapping memory

## Security Notes
- encrypt statement storage
- store minimal sensitive card metadata
- never store full card number
- maintain audit logs for edits

---

# 10. Next Deliverables

This document can now be converted into:

1. detailed database DDL / DBML
2. OpenAPI / Swagger specification
3. Jira epics and tickets
4. high-fidelity UI mockups
5. backend service decomposition
