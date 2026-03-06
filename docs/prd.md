# Spend Tracking Platform PRD

## AI-Powered Credit Card Spend, Rewards, and Charges Tracking Platform

**Prepared for:** product definition and MVP planning  
**Document version:** 1.0  
**Date:** March 7, 2026

**Purpose:** consolidate multi-card statements, auto-categorize spending, track rewards and charges, and surface monthly card-performance insights.

---

## 1. Executive Summary

This product is a web platform for people who use multiple credit cards and want a single place to understand:
- how much they spend every month
- where they spend it
- which card they are using the most
- how many rewards each card generates
- how much they lose in annual fees and other charges
- whether a particular card is worth keeping

The core workflow is:
1. users add their cards
2. upload statements
3. the system extracts and categorizes transactions
4. dashboards show spending, rewards, and charges card-wise and category-wise

A key differentiator is that the platform does not stop at spend categorization. It also helps users evaluate card performance by tracking reward points, fee leakage, and net value created per card.

---

## 2. Product Vision

Build a personal finance intelligence platform that turns scattered credit card statements into a structured, searchable, and insightful dashboard.

The platform should help users answer:
- What did I spend this month?
- Which categories consumed most of my money?
- Which card gave me the best reward return?
- How much did I pay in annual fees, joining fees, GST on charges, interest, and other penalties?
- Are my cards generating enough value to justify the fees?

---

## 3. Problem Statement

Users with many credit cards face three major problems.

### 3.1 Fragmented transaction visibility

Transactions are spread across multiple cards and statement files. It is hard to get one monthly view.

### 3.2 Manual categorization is painful

Users often want transaction-level categorization into buckets like groceries, dining, travel, subscriptions, utilities, shopping, fuel, and fees. Doing this manually every month is repetitive and slow.

### 3.3 Card value is unclear

Users often do not know:
- how many reward points they earned
- whether a card’s annual fee was recovered
- how much they paid in card charges
- which card is efficient versus draining value

This leads to poor card usage decisions and weak financial visibility.

---

## 4. Goals

### Primary Goals

- Consolidate transactions from multiple credit cards
- Automatically categorize spends using a hybrid AI workflow
- Allow custom categories and manual corrections
- Provide a monthly dashboard of category-wise and card-wise spend
- Track rewards earned for each card
- Track charges such as annual fee, joining fee, late fee, finance charges, and taxes
- Show net card value: rewards earned versus charges paid

### Secondary Goals

- Learn from user corrections over time
- Let users compare card performance
- Help users identify expensive or low-value cards
- Reduce monthly effort of statement analysis

---

## 5. Non-Goals

The following are explicitly out of scope for MVP:
- Direct bank integrations
- Real-time transaction sync
- Debit card and bank account aggregation
- UPI tracking
- Investment tracking
- Tax filing workflows
- Mobile apps
- Shared/family budgeting
- Reward redemption automation
- Financial advice or lending recommendations

---

## 6. Target Users

### Primary User

Individuals holding multiple credit cards who want a better way to track spending and card performance.

### Secondary User

Power users who:
- actively optimize for rewards
- use many cards for different purposes
- want custom categories and advanced filters
- want to compare cards on spend, rewards, and charges

---

## 7. Core Value Proposition

The platform provides four major values in one product.

### Unified spend visibility

All card transactions across statements are brought into one system.

### AI-assisted categorization

Transactions are automatically categorized, with manual correction when needed.

### Rewards and charges intelligence

Users see how much each card earns versus how much it costs.

### Trust and control

Users can review low-confidence categorization, create custom categories, and build reusable rules.

---

## 8. Product Principles

- AI assists, user controls
- Trust comes before automation
- Repeatable monthly workflow
- Personalization improves accuracy
- Financial clarity over raw data

---

## 9. User Stories

### Spend Tracking

- As a user, I want to add multiple cards so I can track all card spending in one place.
- As a user, I want to upload statements for each card so transactions get imported automatically.
- As a user, I want transactions categorized automatically so I do not need to tag each line manually.
- As a user, I want to filter transactions by category, card, merchant, and date.
- As a user, I want to create my own categories.

### Review and Control

- As a user, I want to manually correct wrong categories.
- As a user, I want the system to learn from my corrections.
- As a user, I want low-confidence items to be shown separately for review.

### Rewards and Charges

- As a user, I want to see reward points earned for each card.
- As a user, I want to see how much I spent to earn those rewards.
- As a user, I want to see charges for each card, including annual fee and joining fee.
- As a user, I want to compare rewards earned versus charges paid.
- As a user, I want to know whether a card is worth keeping.

### Analytics

- As a user, I want a monthly dashboard that shows overall spend, category-wise spend, and card-wise spend.
- As a user, I want a card detail page to evaluate card performance.
- As a user, I want to compare cards side by side.

---

## 10. Product Scope

### In Scope for MVP

- User authentication
- Card management
- Statement upload
- Transaction extraction from statements
- Multi-card transaction consolidation
- AI-assisted spend categorization
- Manual category creation and correction
- Transaction explorer
- Dashboard with monthly spend statistics
- Per-card spend statistics
- Card charges tracking
- Annual fee and joining fee tracking
- Reward points/manual rewards entry
- Per-card rewards versus charges summary
- Needs-review queue
- Statement history and auditability

### In Scope for Phase 2

- Direct reward extraction from statement summaries
- Rule-based reward estimation engine
- Cashback and milestone reward support
- Recurring merchant recognition
- Advanced reward efficiency analysis
- Budget alerts
- Category trends and anomaly detection

### Out of Scope for MVP

- Bank integrations
- Email auto-fetching statements
- OCR-heavy edge cases across all banks
- Family/shared accounts
- Rewards redemption workflows
- Personalized financial recommendations

---

## 11. Functional Requirements

### 11.1 Authentication and User Accounts

Users can sign up and log in securely.  
User data is isolated.  
Users can manage basic profile settings.

**Acceptance criteria:** users can register with email/password or OAuth, and each logged-in user can access only their own data.

### 11.2 Credit Card Management

Users must be able to add and manage multiple cards.

Each card should support:
- nickname
- issuer/bank
- last four digits
- network
- optional statement cycle day
- optional annual fee expected
- optional joining fee expected
- reward program metadata

**Acceptance criteria:** the user can add, edit, archive, and delete a card, and statements can be linked to a specific card.

### 11.3 Statement Upload

Support upload of statement files linked to a specific card.

Supported formats:
- PDF
- CSV
- optionally XLS/XLSX later

For each upload, store:
- card reference
- file name
- statement period
- upload status
- extraction status
- categorization status

**Acceptance criteria:** the system shows processing state and transaction count extracted from each uploaded statement.

### 11.4 Transaction Extraction

Extract normalized transaction data including:
- transaction date
- posted date if available
- description
- merchant
- amount
- currency
- debit/credit indicator
- statement reference
- card reference

The system should:
- detect duplicates
- detect refunds and reversals
- store raw extraction source for audit

**Acceptance criteria:** normalized rows are created, duplicate re-imports do not cause double counting, and failed extraction is visible.

### 11.5 Spend Categorization

Transactions should be categorized into user-friendly spend categories such as:
- food and dining
- groceries
- fuel
- travel
- shopping
- entertainment
- utilities
- bills
- subscriptions
- health
- education
- insurance
- cash withdrawal
- fees and charges
- refunds
- miscellaneous

The system should use a hybrid classification flow:
1. deterministic rule matching
2. known merchant mapping
3. user history
4. LLM fallback for ambiguous transactions

Each transaction should store:
- category
- confidence score
- classification source
- review flag
- short rationale

### 11.6 Manual Review and Recategorization

Users should be able to:
- change a transaction category
- bulk edit categories
- create rules from corrections
- mark certain merchant patterns to always map to a category

**Acceptance criteria:** manual changes update the dashboard instantly and future similar transactions can inherit learned mappings.

### 11.7 Category Management

Users should be able to create, rename, archive, and later merge categories.  
Default and custom categories should both be supported.

**Acceptance criteria:** archived categories remain in history but are hidden for new selection unless restored.

### 11.8 Rewards Tracking

MVP should allow:
- manual entry of reward points earned
- manual adjustment of reward balance or statement-level reward totals
- marking whether reward data is manual or extracted

Later phases should support:
- extracting rewards from statement summaries
- estimating rewards from card reward rules
- calculating reward value in currency

Fields should support:
- total reward points earned
- points redeemed
- points expired
- cashback earned
- estimated reward value
- reward balance if available

### 11.9 Charges Tracking

The system should identify and track credit-card-related charges separately from normal spend.

Charge types include:
- joining fee
- annual fee
- late fee
- finance charge or interest
- GST or tax on charges
- cash advance fee
- EMI processing fee
- forex markup
- replacement fee
- miscellaneous bank fee

Deterministic pattern-based detection should be used first, with manual override available.

### 11.10 Card Performance View

Every card should have a performance view that shows:
- total spend
- eligible spend for rewards
- total reward points
- estimated reward value
- total charges
- annual fee
- joining fee
- other charges
- net card value

**Formula:** `Net Card Value = Estimated Reward Value - Total Charges Paid`

Negative-value cards should be easy to identify.

### 11.11 Dashboard and Analytics

The dashboard should show summary KPIs such as:
- total spend this month
- total spend last month
- month-over-month change
- total number of transactions
- highest spend category
- highest spend card
- total rewards this month
- total charges this month
- net reward value this month

Charts should include:
- spend by category
- spend by card
- spend trend by month
- top merchants
- charges by card
- rewards by card
- reward vs charges by card

Filters should include:
- date range
- month
- card
- category
- merchant
- amount range
- charges-only
- low-confidence-only

### 11.12 Transaction Explorer

Provide a searchable and filterable transaction table.

Supported capabilities:
- search by merchant or description
- sort by date, amount, category, card
- filter by card, category, date, statement
- inline edit category
- mark as reviewed

### 11.13 Statement History

Users should be able to see all uploaded statements with:
- card
- period
- upload date
- processing status
- extraction status
- categorization status
- extracted transaction count
- errors if any

**Acceptance criteria:** users can trace transactions back to source statement and reprocess or remove an import.

---

## 12. UX / Screen Requirements

- **Authentication:** login, signup, password reset, and onboarding
- **Dashboard:** main monthly summary and spend intelligence page
- **Cards Page:** manage all credit cards and access card-level summaries
- **Card Detail Page:** detailed spend, rewards, and charges analytics for one card
- **Statement Upload Page:** upload statements and track processing
- **Transactions Page:** searchable transaction explorer with edit and review capabilities
- **Categories Page:** create, rename, archive, and manage categories and rules
- **Statement History:** review all uploaded statements and processing outcomes
- **Settings:** user profile, privacy, export, and preferences

---

## 13. Core User Flows

### Flow A: New User Setup

1. Sign up
2. Add one or more cards
3. Optionally create custom categories
4. Upload first statement
5. System extracts and categorizes transactions
6. User reviews low-confidence items
7. Dashboard becomes active

### Flow B: Monthly Usage

1. Upload latest statement for each card
2. System extracts transactions and categorizes them
3. Charges and rewards are updated
4. User reviews exceptions
5. Dashboard updates automatically

### Flow C: Correcting a Transaction

1. User sees incorrect category
2. User changes category
3. System offers rule creation for future reuse
4. Future similar transactions become more accurate

### Flow D: Card Performance Review

1. User opens a specific card
2. Sees spend, rewards, and charges
3. Compares estimated reward value to fees and other charges
4. Decides whether to keep or prioritize the card

---

## 14. AI / Categorization Design

AI should assist classification, not replace deterministic logic where rules are obvious.

Recommended flow:
1. exact rule match
2. merchant normalization lookup
3. user-specific correction memory
4. LLM classification for unknown or ambiguous transactions
5. review queue for low-confidence assignments

Inputs include:
- raw transaction description
- normalized merchant
- amount
- card
- existing categories
- prior user mappings
- charge-related keywords
- statement context if needed

When a user changes a category, the system should:
- store the correction
- optionally create a merchant/category rule
- improve confidence for similar future descriptions

Fee and charge lines such as:
- annual fee
- joining fee
- finance charge
- late payment fee
- GST on charges
- cash advance fee

should be mostly rule-based.

In MVP, rewards handling should support manual reward entry and optionally simple statement-level parsing. Later versions can extract reward summaries and calculate estimated rewards based on card reward rules.

---

## 15. Data Model

- **User:** id, name, email, password_hash, created_at, updated_at
- **Card:** id, user_id, nickname, issuer_name, network, last4, statement_cycle_day, reward_program_name, reward_type, reward_conversion_rate, annual_fee_expected, joining_fee_expected, reward_rule_config_json, status, created_at, updated_at
- **Statement:** id, user_id, card_id, file_name, file_type, statement_period_start, statement_period_end, upload_status, extraction_status, categorization_status, uploaded_at, processing_error
- **Transaction:** id, user_id, card_id, statement_id, txn_date, posted_date, raw_description, normalized_merchant, amount, currency, txn_type, category_id, category_source, category_confidence, review_required, duplicate_flag, is_card_charge, charge_type, is_reward_related, reward_points_delta, cashback_amount, source_hash, created_at, updated_at
- **Category:** id, user_id, name, is_default, is_archived, created_at, updated_at
- **Categorization Rule:** id, user_id, match_type, match_value, assigned_category_id, priority, is_active, created_at, updated_at
- **Categorization Audit Log:** id, transaction_id, old_category_id, new_category_id, changed_by, source, changed_at
- **Card Reward Ledger:** id, user_id, card_id, statement_id, event_date, event_type, reward_points, reward_value_estimate, source, notes
- **Card Charge Summary:** id, user_id, card_id, period_month, annual_fee_amount, joining_fee_amount, late_fee_amount, finance_charge_amount, other_charge_amount, tax_amount, total_charge_amount

---

## 16. Dashboard Metrics

### Spend Metrics

- Total spend this month
- Total spend last month
- Month-over-month growth
- Spend by category
- Spend by card
- Top merchants
- Average transaction value

### Rewards Metrics

- Total reward points earned
- Points by card
- Estimated reward value by card
- Reward rate percentage
- Eligible spend for rewards

### Charges Metrics

- Total charges this month
- Annual fees paid
- Joining fees paid
- Finance charges paid
- Taxes on charges
- Total charges by card

### Net Value Metrics

- Reward value minus charges
- Best performing card
- Most expensive card
- Cards with negative net value

---

## 17. KPI Formulas

- **Reward Rate %** = `Estimated Reward Value / Eligible Spend × 100`
- **Net Card Value** = `Estimated Reward Value - Total Charges Paid`
- **Charges as % of Spend** = `Total Charges Paid / Total Spend × 100`
- **Category Share %** = `Category Spend / Total Spend × 100`

---

## 18. Non-Functional Requirements

### Performance

- Upload acknowledgment under 3 seconds
- Dashboard load under 2 seconds for standard user scale
- Transaction filter/search under 1 second for normal user volume

### Reliability

- No data loss of uploaded statements
- Retry/reprocess support
- Consistent auditability of source files and classification changes

### Security

- Encrypted storage of uploaded files
- Secure database access and authentication
- User-level data isolation
- Audit trail for sensitive edits
- Secure account deletion and data purge

### Privacy

- User owns their financial data
- Uploaded data must not be used for model training without explicit consent
- User can export and delete their data

### Scalability

The architecture should support asynchronous extraction and categorization and moderate-scale growth in users and transactions.

---

## 19. MVP Definition

### Must Have

- Authentication
- Add/manage cards
- Upload statements
- Extract transactions
- Transaction explorer
- AI-assisted categorization
- Manual correction
- Custom categories
- Monthly dashboard
- Card-wise spend summary
- Charge detection and display
- Annual fee and joining fee tracking
- Manual reward entry
- Rewards vs charges summary per card
- Statement history
- Low-confidence review queue

### Nice to Have in MVP

- Simple statement-level reward extraction
- Bulk recategorization
- Card comparison table

### Not in MVP

- Real-time bank sync
- Email inbox scraping
- Advanced reward rules engine
- Cashback redemption workflows
- Predictive spending insights

---

## 20. Release Plan

The release plan should prioritize a usable end-to-end monthly workflow before adding deep automation and optimization features.

| Phase | Focus | Representative Deliverables |
|---|---|---|
| Phase 1 — MVP | Core ingestion, categorization, and card intelligence | Authentication, cards, statement ingestion, transaction normalization, categorization pipeline, dashboard, card detail, manual rewards entry, fee detection |
| Phase 2 | Higher accuracy and richer card optimization | Reward extraction from statements, configurable reward rules, cashback support, recurring merchant detection, advanced card comparison, monthly trend insights |
| Phase 3 | More automation and breadth | Email-based statement ingestion, broader issuer support, spend forecasting, waiver tracking, card optimization recommendations |

---

## Core KPIs to Surface on the Dashboard

| Metric Group | Example KPI | Why It Matters |
|---|---|---|
| Spend | Total spend, spend by category, spend by card | Gives users a quick monthly overview and highlights concentration of spending. |
| Rewards | Reward points earned, reward value, reward rate % | Shows whether card usage is generating meaningful value. |
| Charges | Annual fee, joining fee, late fee, finance charge | Makes fee leakage visible instead of hidden in statement lines. |
| Net Value | Reward value minus charges | Helps users decide which cards to keep, prioritize, or discontinue. |

---

## 21. Risks and Mitigations

- **Statement format inconsistency** — build parser abstraction and support top issuers first.
- **Misclassification harms trust** — show review queue, confidence scores, and easy corrections.
- **Duplicate imports** — use transaction hashing and deduplication checks.
- **LLM cost scaling** — use hybrid pipeline and reserve LLMs for ambiguous cases.
- **Reward extraction complexity** — start with manual entry and phased automation.
- **Sensitive financial data concerns** — use strong encryption, privacy controls, and strict data isolation.

---

## 22. Success Metrics

### Product Usage

- Monthly active users
- Statements uploaded per user
- Transactions processed per user
- Repeat monthly usage rate

### Quality

- Extraction success rate
- Categorization accuracy
- Low-confidence transaction rate
- Fee-detection accuracy
- Reward tracking completeness

### User Value

- Time saved in monthly review
- Percentage of transactions auto-categorized
- Cards analyzed through reward-vs-charge view
- Number of user-created categories and rules
- Number of users identifying low-value cards

---

## 23. Open Questions

- Which banks/cards should be supported first?
- Should MVP focus on India-first statement formats?
- Should rewards be manual-only in first release or partially extracted?
- Should category structure be flat or hierarchical?
- Should refunds reduce category totals automatically or be displayed separately?
- Should reward redemption be tracked in MVP or only earnings?
- Should annual fee waiver tracking come in phase 2?

---

## 24. Positioning

**One-line pitch:** A web app that consolidates all your credit card statements, automatically categorizes spending, tracks rewards and fees, and shows which cards are actually worth using.

**Core differentiator:** most expense trackers stop at spend visibility. This product adds card intelligence by showing spend, rewards, charges, and net value together.

---

## 25. Recommended Epics

- Epic 1: User Account and Onboarding
- Epic 2: Card Management
- Epic 3: Statement Ingestion
- Epic 4: Transaction Intelligence
- Epic 5: Dashboard and Analytics
- Epic 6: Rewards and Charges
- Epic 7: Audit and History

---

## 26. Founder-Ready Summary

This product solves a clear and recurring user pain: people with many credit cards cannot easily understand where they spend, what each card earns, and what each card costs.

The MVP should focus on:
- statement ingestion
- transaction extraction
- categorization
- dashboarding
- rewards summary
- charge tracking
- card-level value analysis

That scope is strong enough to provide immediate user value and differentiated enough to stand out from a basic expense tracker.

The next step after this PRD is to convert it into:
- feature-wise epics and tickets
- wireframes for each page
- backend schema plus API contracts
