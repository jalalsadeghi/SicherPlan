// @vitest-environment happy-dom

import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import SicherPlanLoadingOverlay from "./SicherPlanLoadingOverlay.vue";

vi.mock("@vben/common-ui", () => ({
  Spinner: {
    name: "Spinner",
    props: ["spinning"],
    template: '<div data-testid="mock-spinner" :data-spinning="spinning ? `true` : `false`"></div>',
  },
}));

describe("SicherPlanLoadingOverlay", () => {
  it("marks the covered region busy and shows the overlay while active", async () => {
    const wrapper = mount(SicherPlanLoadingOverlay, {
      props: {
        busy: true,
        busyTestid: "overlay-under-test",
        text: "Processing request",
      },
      slots: {
        default: '<div class="inner-content">Form body</div>',
      },
    });

    expect(wrapper.attributes("aria-busy")).toBe("true");
    expect(wrapper.get('[data-testid="overlay-under-test"]').attributes("data-busy")).toBe("true");
    expect(wrapper.text()).toContain("Processing request");
    expect(wrapper.get('[data-testid="mock-spinner"]').attributes("data-spinning")).toBe("true");
  });

  it("clears the busy state after the minimum visible duration", async () => {
    vi.useFakeTimers();
    const wrapper = mount(SicherPlanLoadingOverlay, {
      props: {
        busy: true,
        busyTestid: "overlay-under-test",
        minVisibleMs: 50,
      },
      slots: {
        default: '<div class="inner-content">Form body</div>',
      },
    });

    await wrapper.setProps({ busy: false });
    expect(wrapper.attributes("aria-busy")).toBe("true");

    vi.advanceTimersByTime(60);
    await wrapper.vm.$nextTick();

    expect(wrapper.attributes("aria-busy")).toBe("false");
    expect(wrapper.get('[data-testid="overlay-under-test"]').attributes("data-busy")).toBe("false");
    vi.useRealTimers();
  });
});
