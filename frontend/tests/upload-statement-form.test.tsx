import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { UploadStatementForm } from "@/components/forms/upload-statement-form";

const { refreshMock, presignMock, createStatementMock } = vi.hoisted(() => ({
  refreshMock: vi.fn(),
  presignMock: vi.fn(),
  createStatementMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    refresh: refreshMock,
  }),
}));

vi.mock("@/lib/api/browser", () => ({
  browserApi: {
    uploads: {
      presign: presignMock,
    },
    statements: {
      create: createStatementMock,
    },
  },
}));

describe("UploadStatementForm", () => {
  beforeEach(() => {
    presignMock.mockReset();
    createStatementMock.mockReset();
    refreshMock.mockReset();
    vi.restoreAllMocks();
  });

  it("uploads the selected file before creating statement metadata", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          data: {
            stored: true,
            file_storage_key: "statements/user-1/generated-march.pdf",
          },
          meta: {},
          error: null,
        }),
        {
          status: 200,
          headers: {
            "content-type": "application/json",
          },
        },
      ),
    );

    presignMock.mockResolvedValue({
      data: {
        upload_url: "/api/v1/uploads/content?file_storage_key=statements%2Fuser-1%2Fgenerated-march.pdf",
        file_storage_key: "statements/user-1/generated-march.pdf",
      },
      meta: {},
    });
    createStatementMock.mockResolvedValue({
      data: {
        id: "statement-1",
      },
      meta: {},
    });

    const { container } = render(
      <UploadStatementForm
        cards={[
          {
            id: "card-1",
            nickname: "Primary Card",
            issuer_name: "HDFC",
            network: "Visa",
            last4: "1234",
            statement_cycle_day: 12,
            annual_fee_expected: "12500.00",
            joining_fee_expected: "12500.00",
            reward_program_name: "Rewards",
            reward_type: "points",
            reward_conversion_rate: "0.5",
            reward_rule_config_json: null,
            status: "active",
          },
        ]}
      />,
    );

    fireEvent.change(screen.getByRole("combobox"), {
      target: { value: "card-1" },
    });
    fireEvent.change(screen.getByLabelText("Statement period start"), {
      target: { value: "2026-03-01" },
    });
    fireEvent.change(screen.getByLabelText("Statement period end"), {
      target: { value: "2026-03-31" },
    });

    const file = new File(["statement pdf body"], "march_2026.pdf", {
      type: "application/pdf",
    });
    const input = container.querySelector('input[type="file"]');
    expect(input).not.toBeNull();
    fireEvent.change(input as HTMLInputElement, {
      target: { files: [file] },
    });

    fireEvent.click(screen.getByRole("button", { name: "Upload statement" }));

    await waitFor(() => {
      expect(presignMock).toHaveBeenCalledWith({
        file_name: "march_2026.pdf",
        content_type: "application/pdf",
      });
    });
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/uploads/content?file_storage_key=statements%2Fuser-1%2Fgenerated-march.pdf",
        expect.objectContaining({
          method: "PUT",
          headers: expect.any(Headers),
        }),
      );
    });
    await waitFor(() => {
      expect(createStatementMock).toHaveBeenCalledWith({
        card_id: "card-1",
        file_name: "march_2026.pdf",
        file_storage_key: "statements/user-1/generated-march.pdf",
        file_type: "pdf",
        statement_period_start: "2026-03-01",
        statement_period_end: "2026-03-31",
      });
    });
    expect(await screen.findByText("Statement uploaded and queued successfully.")).toBeInTheDocument();
    expect(refreshMock).toHaveBeenCalled();
  });
});
