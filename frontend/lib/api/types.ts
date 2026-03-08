export type ApiNumber = number | string;

export interface ApiErrorPayload {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
}

export interface ResponseEnvelope<T> {
  data: T | null;
  meta: Record<string, unknown>;
  error: ApiErrorPayload | null;
}

export interface UserRead {
  id: string;
  email: string;
  full_name: string;
}

export interface AuthResponse {
  user: UserRead;
  token: string;
}

export interface CardRead {
  id: string;
  nickname: string;
  issuer_name: string;
  network: string;
  last4: string;
  statement_cycle_day: number | null;
  annual_fee_expected: ApiNumber | null;
  joining_fee_expected: ApiNumber | null;
  reward_program_name: string | null;
  reward_type: "points" | "cashback" | "miles";
  reward_conversion_rate: ApiNumber | null;
  reward_rule_config_json: Record<string, unknown> | null;
  status: "active" | "archived";
}

export interface CardCreatePayload {
  nickname: string;
  issuer_name: string;
  network: string;
  last4: string;
  statement_cycle_day?: number | null;
  annual_fee_expected?: ApiNumber | null;
  joining_fee_expected?: ApiNumber | null;
  reward_program_name?: string | null;
  reward_type: "points" | "cashback" | "miles";
  reward_conversion_rate?: ApiNumber | null;
  reward_rule_config_json?: Record<string, unknown> | null;
}

export interface CardUpdatePayload {
  nickname?: string | null;
  issuer_name?: string | null;
  network?: string | null;
  last4?: string | null;
  statement_cycle_day?: number | null;
  annual_fee_expected?: ApiNumber | null;
  joining_fee_expected?: ApiNumber | null;
  reward_program_name?: string | null;
  reward_type?: "points" | "cashback" | "miles" | null;
  reward_conversion_rate?: ApiNumber | null;
  reward_rule_config_json?: Record<string, unknown> | null;
}

export interface CategoryRead {
  id: string;
  name: string;
  slug: string;
  group_name: "spend" | "charges" | "rewards";
  is_default: boolean;
  is_archived: boolean;
}

export interface CategoryCreatePayload {
  name: string;
  group_name: "spend" | "charges" | "rewards";
}

export interface RuleRead {
  id: string;
  rule_name: string;
  match_type: RuleMatchType;
  match_value: string;
  assigned_category_id: string;
  priority: number;
  is_active: boolean;
}

export type RuleMatchType = "description_contains" | "merchant_equals" | "regex";

export interface RuleCreatePayload {
  rule_name: string;
  match_type: RuleMatchType;
  match_value: string;
  assigned_category_id: string;
  priority?: number;
  is_active?: boolean;
}

export interface UploadPresignRead {
  upload_url: string;
  file_storage_key: string;
}

export interface StatementRead {
  id: string;
  card_id: string;
  file_name: string;
  file_storage_key: string;
  file_type: "pdf" | "csv" | "xls" | "xlsx";
  statement_period_start: string;
  statement_period_end: string;
  upload_status: "uploaded" | "processing" | "completed" | "failed";
  extraction_status: "pending" | "running" | "completed" | "failed";
  categorization_status: "pending" | "running" | "completed" | "failed";
  transaction_count: number;
  processing_error: string | null;
  uploaded_at: string;
  created_at: string;
  updated_at: string;
}

export interface StatementCreatePayload {
  card_id: string;
  file_name: string;
  file_storage_key: string;
  file_password?: string | null;
  file_type: "pdf" | "csv" | "xls" | "xlsx";
  statement_period_start: string;
  statement_period_end: string;
}

export interface StatementDeleteResult {
  id: string;
  deleted: boolean;
  transactions_deleted: number;
  storage_object_deleted: boolean;
  delete_policy: string;
}

export interface TransactionCategorySummary {
  id: string;
  name: string;
}

export interface TransactionRead {
  id: string;
  txn_date: string;
  posted_date: string | null;
  card_id: string;
  card_name: string;
  statement_id: string;
  raw_description: string;
  normalized_merchant: string;
  amount: ApiNumber;
  currency: string;
  txn_direction: string;
  txn_type: string;
  category: TransactionCategorySummary | null;
  category_source: string | null;
  category_confidence: ApiNumber | null;
  category_explanation: string | null;
  review_required: boolean;
  duplicate_flag: boolean;
  is_card_charge: boolean;
  charge_type: string | null;
  is_reward_related: boolean;
  reward_points_delta: ApiNumber | null;
  cashback_amount: ApiNumber | null;
  source_hash: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface TransactionUpdatePayload {
  category_id?: string | null;
  review_required?: boolean;
  create_rule?: boolean;
  rule_match_type?: RuleMatchType;
  rule_match_value?: string;
}

export interface TransactionBulkUpdatePayload {
  transaction_ids: string[];
  category_id?: string | null;
  review_required?: boolean;
}

export interface TransactionBulkUpdateResult {
  updated_count: number;
  audit_count: number;
}

export interface DashboardSummaryRead {
  total_spend: ApiNumber;
  previous_period_spend: ApiNumber;
  spend_change_pct: ApiNumber;
  total_rewards_value: ApiNumber;
  total_charges: ApiNumber;
  net_card_value: ApiNumber;
  transaction_count: number;
  needs_review_count: number;
  top_category: {
    category_id: string | null;
    name: string;
    amount: ApiNumber;
  } | null;
  top_card: {
    card_id: string;
    name: string;
    amount: ApiNumber;
  } | null;
}

export interface SpendByCategoryRead {
  category_id: string | null;
  category_name: string;
  amount: ApiNumber;
  transaction_count: number;
}

export interface SpendByCardRead {
  card_id: string;
  card_name: string;
  amount: ApiNumber;
  transaction_count: number;
}

export interface RewardVsChargesRead {
  card_id: string;
  card_name: string;
  total_spend: ApiNumber;
  reward_value: ApiNumber;
  charges: ApiNumber;
  net_value: ApiNumber;
}

export interface MonthlyTrendRead {
  month: string;
  total_spend: ApiNumber;
  reward_value: ApiNumber;
  charges: ApiNumber;
  net_value: ApiNumber;
}

export interface TopMerchantRead {
  merchant_name: string;
  amount: ApiNumber;
  transaction_count: number;
}

export interface CardSummaryRead {
  card: {
    id: string;
    nickname: string;
    last4: string;
    issuer_name: string;
  };
  total_spend: ApiNumber;
  eligible_spend: ApiNumber;
  reward_points: ApiNumber;
  reward_value: ApiNumber;
  charges: ApiNumber;
  annual_fee: ApiNumber;
  joining_fee: ApiNumber;
  other_charges: ApiNumber;
  net_value: ApiNumber;
}

export interface CardRewardSummaryRead {
  card_id: string;
  reward_type: string;
  total_points_earned: ApiNumber;
  total_points_redeemed: ApiNumber;
  total_points_expired: ApiNumber;
  estimated_reward_value: ApiNumber;
  current_balance: ApiNumber;
}

export interface CardChargeSummaryRead {
  card_id: string;
  source: string;
  summary_period_count: number;
  annual_fee_amount: ApiNumber;
  joining_fee_amount: ApiNumber;
  late_fee_amount: ApiNumber;
  finance_charge_amount: ApiNumber;
  emi_processing_fee_amount: ApiNumber;
  cash_advance_fee_amount: ApiNumber;
  forex_markup_amount: ApiNumber;
  tax_amount: ApiNumber;
  other_charge_amount: ApiNumber;
  total_charge_amount: ApiNumber;
}

export type RewardEventType = "earned" | "redeemed" | "expired" | "adjusted" | "cashback";
export type RewardLedgerSource = "manual" | "extracted" | "estimated";

export interface RewardLedgerRead {
  id: string;
  card_id: string;
  statement_id: string | null;
  event_date: string;
  event_type: RewardEventType;
  reward_points: ApiNumber | null;
  reward_value_estimate: ApiNumber | null;
  source: RewardLedgerSource;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface RewardLedgerCreatePayload {
  card_id: string;
  statement_id?: string | null;
  event_date: string;
  event_type: RewardEventType;
  reward_points?: ApiNumber | null;
  reward_value_estimate?: ApiNumber | null;
  source?: RewardLedgerSource;
  notes?: string | null;
}

export interface RewardLedgerUpdatePayload {
  statement_id?: string | null;
  event_date?: string;
  event_type?: RewardEventType;
  reward_points?: ApiNumber | null;
  reward_value_estimate?: ApiNumber | null;
  source?: RewardLedgerSource;
  notes?: string | null;
}

export interface QueryFilters {
  [key: string]: string | number | boolean | null | undefined;
}

export interface PageMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface LocalSettingsPreference {
  id: string;
  label: string;
  value: string;
  note: string;
}

export type TransactionSortBy = "txn_date" | "posted_date" | "amount" | "created_at" | "updated_at";
export type SortOrder = "asc" | "desc";
