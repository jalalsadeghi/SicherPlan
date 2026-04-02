import { beforeEach, describe, expect, it, vi } from "vitest";

const notification = {
  error: vi.fn(),
  info: vi.fn(),
  success: vi.fn(),
  warning: vi.fn(),
};

vi.mock("ant-design-vue", () => ({
  notification,
}));

describe("useSicherPlanFeedback", () => {
  beforeEach(() => {
    notification.error.mockReset();
    notification.info.mockReset();
    notification.success.mockReset();
    notification.warning.mockReset();
  });

  it("routes success feedback to bottom-right auto-dismiss notifications", async () => {
    const { useSicherPlanFeedback } = await import("./useSicherPlanFeedback");
    const { showFeedbackToast } = useSicherPlanFeedback();

    showFeedbackToast({
      key: "employee-admin-feedback",
      message: "Employee saved",
      title: "Saved",
      tone: "success",
    });

    expect(notification.success).toHaveBeenCalledWith({
      description: "Employee saved",
      duration: 3.5,
      key: "employee-admin-feedback",
      message: "Saved",
      placement: "bottomRight",
    });
  });

  it("maps neutral feedback to info notifications without duplicating the message body", async () => {
    const { useSicherPlanFeedback } = await import("./useSicherPlanFeedback");
    const { showFeedbackToast } = useSicherPlanFeedback();

    showFeedbackToast({
      message: "Scope remembered",
      tone: "neutral",
    });

    expect(notification.info).toHaveBeenCalledWith({
      description: undefined,
      duration: 3.5,
      key: undefined,
      message: "Scope remembered",
      placement: "bottomRight",
    });
  });

  it("routes error feedback to the longer-lived error notification style", async () => {
    const { useSicherPlanFeedback } = await import("./useSicherPlanFeedback");
    const { showFeedbackToast } = useSicherPlanFeedback();

    showFeedbackToast({
      message: "Customer save failed",
      title: "Could not save customer",
      tone: "error",
    });

    expect(notification.error).toHaveBeenCalledWith({
      description: "Customer save failed",
      duration: 5,
      key: undefined,
      message: "Could not save customer",
      placement: "bottomRight",
    });
  });
});

