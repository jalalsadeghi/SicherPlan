import { notification } from "ant-design-vue";

export type SicherPlanFeedbackTone =
  | "bad"
  | "danger"
  | "error"
  | "good"
  | "info"
  | "neutral"
  | "success"
  | "warning";

type FeedbackMethod = "error" | "info" | "success" | "warning";

type ShowFeedbackToastOptions = {
  duration?: number;
  key?: string;
  message: string;
  placement?: "bottomRight";
  title?: string;
  tone: SicherPlanFeedbackTone;
};

const DEFAULT_PLACEMENT = "bottomRight";
const SHORT_DURATION_SECONDS = 3.5;
const LONG_DURATION_SECONDS = 5;

function resolveFeedbackMethod(tone: SicherPlanFeedbackTone): FeedbackMethod {
  switch (tone) {
    case "good":
    case "success": {
      return "success";
    }
    case "warning": {
      return "warning";
    }
    case "bad":
    case "danger":
    case "error": {
      return "error";
    }
    case "info":
    case "neutral":
    default: {
      return "info";
    }
  }
}

function resolveFeedbackDuration(tone: SicherPlanFeedbackTone): number {
  switch (resolveFeedbackMethod(tone)) {
    case "error":
    case "warning": {
      return LONG_DURATION_SECONDS;
    }
    case "info":
    case "success":
    default: {
      return SHORT_DURATION_SECONDS;
    }
  }
}

export function useSicherPlanFeedback() {
  function showFeedbackToast({
    duration,
    key,
    message,
    placement = DEFAULT_PLACEMENT,
    title,
    tone,
  }: ShowFeedbackToastOptions) {
    const method = resolveFeedbackMethod(tone);
    const headline = title?.trim() || message;
    const body = title?.trim() && title.trim() !== message ? message : undefined;

    notification[method]({
      description: body,
      duration: duration ?? resolveFeedbackDuration(tone),
      key,
      message: headline,
      placement,
    });
  }

  return {
    showFeedbackToast,
  };
}

