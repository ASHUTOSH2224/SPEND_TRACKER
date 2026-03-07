import { EmptyState } from "@/components/shared/empty-state";

export default function CardNotFoundPage() {
  return (
    <EmptyState
      title="Card not found"
      description="This card does not exist or is not owned by the current user."
      actionHref="/cards"
      actionLabel="Back to cards"
    />
  );
}
