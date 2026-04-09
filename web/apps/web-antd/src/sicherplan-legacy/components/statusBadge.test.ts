// @vitest-environment happy-dom

import { createPinia, setActivePinia } from "pinia";
import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it } from "vitest";

import StatusBadge from "./StatusBadge.vue";

describe("StatusBadge", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it.each([
    ["active", "Aktiv"],
    ["inactive", "Inaktiv"],
    ["archived", "Archiviert"],
    ["draft", "Entwurf"],
    ["release_ready", "Release Ready"],
    ["released", "Freigegeben"],
  ])("renders %s with the correct label", (status, label) => {
    const wrapper = mount(StatusBadge, {
      props: {
        status,
      },
    });

    expect(wrapper.text()).toBe(label);
    expect(wrapper.attributes("data-status")).toBe(status);
  });

  it("keeps unknown statuses neutral instead of coercing them to inactive", () => {
    const wrapper = mount(StatusBadge, {
      props: {
        status: "mystery_state",
      },
    });

    expect(wrapper.text()).toBe("Unbekannt");
    expect(wrapper.attributes("data-status")).toBe("unknown");
  });
});
