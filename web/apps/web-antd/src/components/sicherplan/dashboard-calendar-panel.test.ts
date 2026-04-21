// @vitest-environment happy-dom

import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import { defineComponent } from "vue";

import DashboardCalendarPanel from "./dashboard-calendar-panel.vue";

const CardStub = defineComponent({
  name: "CardStub",
  template: '<div class="card-stub"><slot /></div>',
});

const ButtonStub = defineComponent({
  name: "ButtonStub",
  template: '<button type="button"><slot /></button>',
});

const SpaceStub = defineComponent({
  name: "SpaceStub",
  template: '<div class="space-stub"><slot /></div>',
});

const SectionHeaderStub = defineComponent({
  name: "SectionHeaderStub",
  props: {
    description: { type: String, default: "" },
    title: { type: String, default: "" },
  },
  template: '<div class="section-header-stub">{{ title }}|{{ description }}</div>',
});

function mountComponent(overrides: Record<string, unknown> = {}) {
  return mount(DashboardCalendarPanel, {
    props: {
      cells: [
        {
          dateKey: "2026-04-01",
          dayLabel: "1",
          inMonth: true,
          isToday: false,
          visibleItems: [],
          moreCount: 0,
          shiftCount: 2,
          orderCount: 1,
        },
      ],
      description: "description",
      monthHint: "month hint",
      monthLabel: "April 2026",
      moreLabel: "more",
      nextLabel: "next",
      orderShortLabel: "ORD",
      previousLabel: "prev",
      shiftShortLabel: "SH",
      summary: [
        { label: "Orders", value: "1" },
        { label: "Shifts", value: "2" },
      ],
      title: "Calendar",
      weekDayLabels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
      ...overrides,
    },
    global: {
      stubs: {
        Button: ButtonStub,
        Card: CardStub,
        RouterLink: defineComponent({
          name: "RouterLinkStub",
          template: '<a><slot /></a>',
        }),
        SectionHeader: SectionHeaderStub,
        Space: SpaceStub,
      },
    },
  });
}

describe("DashboardCalendarPanel", () => {
  it("renders order pills before shift pills inside a calendar cell", () => {
    const wrapper = mountComponent();

    const pills = wrapper.findAll(".sp-dashboard__calendar-pill");
    expect(pills).toHaveLength(2);
    expect(pills[0]?.text()).toContain("1 ORD");
    expect(pills[1]?.text()).toContain("2 SH");
  });

  it("renders order and shift pills as siblings in the same calendar-events container", () => {
    const wrapper = mountComponent();

    const events = wrapper.get(".sp-dashboard__calendar-events");
    const pills = events.findAll(".sp-dashboard__calendar-pill");

    expect(pills).toHaveLength(2);
    expect(pills[0]?.element.parentElement).toBe(events.element);
    expect(pills[1]?.element.parentElement).toBe(events.element);
    expect(pills[0]?.classes()).toContain("sp-dashboard__calendar-pill--amber");
    expect(pills[1]?.classes()).toContain("sp-dashboard__calendar-pill--teal");
  });

  it("shows and hides an inline loading indicator without hiding calendar controls or grid", async () => {
    const wrapper = mountComponent({
      loading: true,
      loadingLabel: "Loading calendar data",
    });

    const loadingIndicator = wrapper.get('[data-testid="customer-dashboard-calendar-loading-indicator"]');
    expect(loadingIndicator.text()).toBe("Loading calendar data");
    expect(loadingIndicator.attributes("role")).toBe("status");
    expect(loadingIndicator.attributes("aria-live")).toBe("polite");
    expect(loadingIndicator.find(".sp-dashboard__calendar-loading-dot").exists()).toBe(true);
    expect(wrapper.text()).toContain("April 2026");
    expect(wrapper.text()).toContain("prev");
    expect(wrapper.text()).toContain("next");
    expect(wrapper.find(".sp-dashboard__calendar-grid").exists()).toBe(true);

    await wrapper.setProps({ loading: false });

    expect(wrapper.find('[data-testid="customer-dashboard-calendar-loading-indicator"]').exists()).toBe(false);
    expect(wrapper.find(".sp-dashboard__calendar-grid").exists()).toBe(true);
    expect(wrapper.text()).toContain("April 2026");
  });
});
