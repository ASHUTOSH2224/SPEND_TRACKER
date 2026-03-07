import type {
  CardChargeSummaryRead,
  CardCreatePayload,
  CardRead,
  CardRewardSummaryRead,
  CardSummaryRead,
  CardUpdatePayload,
  CategoryCreatePayload,
  CategoryRead,
  DashboardSummaryRead,
  MonthlyTrendRead,
  RewardLedgerCreatePayload,
  RewardLedgerRead,
  RewardLedgerUpdatePayload,
  RewardVsChargesRead,
  RuleCreatePayload,
  RuleRead,
  SpendByCardRead,
  SpendByCategoryRead,
  StatementCreatePayload,
  StatementDeleteResult,
  StatementRead,
  TopMerchantRead,
  TransactionRead,
  TransactionBulkUpdatePayload,
  TransactionBulkUpdateResult,
  TransactionUpdatePayload,
  UploadPresignRead,
  UserRead,
} from "@/lib/api/types";
import type { ApiRequestOptions, ApiResult } from "@/lib/api/http";

export type ApiRequester = <T>(path: string, options?: ApiRequestOptions) => Promise<ApiResult<T>>;

export function createApiClient(request: ApiRequester) {
  return {
    auth: {
      me: () => request<UserRead>("/auth/me"),
    },
    dashboard: {
      summary: (query?: ApiRequestOptions["query"]) =>
        request<DashboardSummaryRead>("/dashboard/summary", { query }),
      spendByCategory: (query?: ApiRequestOptions["query"]) =>
        request<SpendByCategoryRead[]>("/dashboard/spend-by-category", { query }),
      spendByCard: (query?: ApiRequestOptions["query"]) =>
        request<SpendByCardRead[]>("/dashboard/spend-by-card", { query }),
      rewardsVsCharges: (query?: ApiRequestOptions["query"]) =>
        request<RewardVsChargesRead[]>("/dashboard/rewards-vs-charges", { query }),
      monthlyTrend: (query?: ApiRequestOptions["query"]) =>
        request<MonthlyTrendRead[]>("/dashboard/monthly-trend", { query }),
      topMerchants: (query?: ApiRequestOptions["query"]) =>
        request<TopMerchantRead[]>("/dashboard/top-merchants", { query }),
    },
    cards: {
      list: () => request<CardRead[]>("/cards"),
      create: (body: CardCreatePayload) => request<CardRead>("/cards", { method: "POST", body }),
      get: (cardId: string) => request<CardRead>(`/cards/${cardId}`),
      update: (cardId: string, body: CardUpdatePayload) =>
        request<CardRead>(`/cards/${cardId}`, { method: "PATCH", body }),
      summary: (cardId: string, query?: ApiRequestOptions["query"]) =>
        request<CardSummaryRead>(`/cards/${cardId}/summary`, { query }),
      rewards: (cardId: string) => request<CardRewardSummaryRead>(`/cards/${cardId}/rewards`),
      charges: (cardId: string) => request<CardChargeSummaryRead>(`/cards/${cardId}/charges`),
      monthlyTrend: (cardId: string, query?: ApiRequestOptions["query"]) =>
        request<MonthlyTrendRead[]>(`/cards/${cardId}/monthly-trend`, { query }),
      transactions: (cardId: string, query?: ApiRequestOptions["query"]) =>
        request<TransactionRead[]>(`/cards/${cardId}/transactions`, { query }),
      archive: (cardId: string) => request<CardRead>(`/cards/${cardId}`, { method: "DELETE" }),
    },
    categories: {
      list: () => request<CategoryRead[]>("/categories"),
      create: (body: CategoryCreatePayload) => request<CategoryRead>("/categories", { method: "POST", body }),
      archive: (categoryId: string) => request<CategoryRead>(`/categories/${categoryId}`, { method: "DELETE" }),
    },
    rules: {
      list: () => request<RuleRead[]>("/rules"),
      create: (body: RuleCreatePayload) => request<RuleRead>("/rules", { method: "POST", body }),
      disable: (ruleId: string) => request<RuleRead>(`/rules/${ruleId}`, { method: "DELETE" }),
    },
    uploads: {
      presign: (body: { file_name: string; content_type: string }) =>
        request<UploadPresignRead>("/uploads/presign", { method: "POST", body }),
    },
    statements: {
      list: (query?: ApiRequestOptions["query"]) =>
        request<StatementRead[]>("/statements", { query }),
      create: (body: StatementCreatePayload) =>
        request<StatementRead>("/statements", { method: "POST", body }),
      retry: (statementId: string) =>
        request<StatementRead>(`/statements/${statementId}/retry`, { method: "POST" }),
      remove: (statementId: string) =>
        request<StatementDeleteResult>(`/statements/${statementId}`, { method: "DELETE" }),
    },
    transactions: {
      list: (query?: ApiRequestOptions["query"]) =>
        request<TransactionRead[]>("/transactions", { query }),
      update: (transactionId: string, body: TransactionUpdatePayload) =>
        request<TransactionRead>(`/transactions/${transactionId}`, { method: "PATCH", body }),
      bulkUpdate: (body: TransactionBulkUpdatePayload) =>
        request<TransactionBulkUpdateResult>("/transactions/bulk-update", { method: "POST", body }),
    },
    rewardLedgers: {
      list: (query?: ApiRequestOptions["query"]) =>
        request<RewardLedgerRead[]>("/reward-ledgers", { query }),
      create: (body: RewardLedgerCreatePayload) =>
        request<RewardLedgerRead>("/reward-ledgers", { method: "POST", body }),
      update: (rewardLedgerId: string, body: RewardLedgerUpdatePayload) =>
        request<RewardLedgerRead>(`/reward-ledgers/${rewardLedgerId}`, { method: "PATCH", body }),
      remove: (rewardLedgerId: string) =>
        request<RewardLedgerRead>(`/reward-ledgers/${rewardLedgerId}`, { method: "DELETE" }),
    },
  };
}
