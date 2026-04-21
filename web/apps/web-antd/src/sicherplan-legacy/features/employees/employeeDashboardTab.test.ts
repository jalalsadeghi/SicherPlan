// @vitest-environment happy-dom

import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import EmployeeDashboardTab from "../../components/employees/EmployeeDashboardTab.vue";

vi.mock("@/i18n", () => ({
  useI18n: () => ({
    locale: { value: "en-US" },
    t: (key: string) => {
      const translations: Record<string, string> = {
        "employeeAdmin.dashboard.calendarDescription": "Only assigned shifts.",
        "employeeAdmin.dashboard.calendarMore": "more",
        "employeeAdmin.dashboard.calendarMonthHint": "Month view",
        "employeeAdmin.dashboard.calendarNext": "Next",
        "employeeAdmin.dashboard.calendarOrderShort": "ord.",
        "employeeAdmin.dashboard.calendarPrevious": "Previous",
        "employeeAdmin.dashboard.calendarShiftShort": "sh.",
        "employeeAdmin.dashboard.calendarSummary.orders": "Orders",
        "employeeAdmin.dashboard.calendarSummary.projects": "Projects",
        "employeeAdmin.dashboard.calendarSummary.shifts": "Shifts",
        "employeeAdmin.dashboard.calendarTitle": "Employee calendar",
        "employeeAdmin.dashboard.noStaffingAccess": "No staffing access.",
        "employeeAdmin.dashboard.photo.add": "Add photo",
        "employeeAdmin.dashboard.photo.alt": "Employee photo",
        "employeeAdmin.dashboard.photo.change": "Change photo",
        "employeeAdmin.dashboard.photo.uploading": "Uploading photo...",
        "employeeAdmin.dashboard.projectsEyebrow": "Assignment contexts",
        "employeeAdmin.dashboard.projectsTitle": "Past, current, and future projects",
        "employeeAdmin.summary.none": "None",
      };
      return translations[key] ?? key;
    },
  }),
}));

vi.mock("@/api/planningStaffing", () => ({
  listStaffingBoard: vi.fn().mockResolvedValue([]),
}));

const employee = {
  id: "employee-1",
  tenant_id: "tenant-1",
  personnel_no: "P-1000",
  first_name: "Mara",
  last_name: "Schulz",
  preferred_name: null,
  work_email: "mara.schulz@example.test",
  work_phone: null,
  mobile_phone: null,
  default_branch_id: null,
  default_mandate_id: null,
  hire_date: "2026-04-01",
  termination_date: null,
  employment_type_code: "full_time",
  target_weekly_hours: 40,
  target_monthly_hours: null,
  user_id: null,
  notes: null,
  status: "active",
  created_at: "2026-04-01T08:00:00Z",
  updated_at: "2026-04-01T08:00:00Z",
  archived_at: null,
  version_no: 1,
  group_memberships: [],
};

function mountDashboard(overrides: Record<string, unknown> = {}) {
  return mount(EmployeeDashboardTab, {
    props: {
      accessToken: "token-1",
      canManagePhoto: true,
      canReadStaffing: false,
      employee,
      photoPreviewUrl: "",
      selectedEmployeeBranchLabel: "Berlin",
      selectedEmployeeMandateLabel: "Mitte",
      tenantId: "tenant-1",
      ...overrides,
    },
    global: {
      stubs: {
        DashboardCalendarPanel: true,
        StatusBadge: {
          props: ["status"],
          template: '<span data-testid="status-badge">{{ status }}</span>',
        },
      },
    },
  });
}

describe("EmployeeDashboardTab photo UX", () => {
  it("renders change-photo affordance when a preview image exists", () => {
    const wrapper = mountDashboard({ photoPreviewUrl: "blob:employee-photo" });

    expect(wrapper.get('[data-testid="employee-dashboard-photo-button"]').attributes("aria-label")).toBe("Change photo");
    expect(wrapper.get('[data-testid="employee-dashboard-photo-image"]').attributes("src")).toBe("blob:employee-photo");
    expect(wrapper.get('[data-testid="employee-dashboard-photo-image"]').attributes("alt")).toBe("Employee photo");
  });

  it("renders add-photo affordance when no preview image exists", () => {
    const wrapper = mountDashboard();

    expect(wrapper.get('[data-testid="employee-dashboard-photo-button"]').attributes("aria-label")).toBe("Add photo");
    expect(wrapper.get('[data-testid="employee-dashboard-photo-placeholder"]').text()).toBe("MS");
  });

  it("opens the hidden image input from the photo button", async () => {
    const wrapper = mountDashboard();
    const input = wrapper.get('[data-testid="employee-dashboard-photo-input"]');
    const clickSpy = vi.spyOn(input.element as HTMLInputElement, "click");

    expect(input.attributes("accept")).toBe("image/*");
    await wrapper.get('[data-testid="employee-dashboard-photo-button"]').trigger("click");

    expect(clickSpy).toHaveBeenCalled();
  });

  it("emits selected image files from the hidden input", async () => {
    const wrapper = mountDashboard();
    const input = wrapper.get('[data-testid="employee-dashboard-photo-input"]');
    const file = new File(["photo"], "employee.png", { type: "image/png" });
    Object.defineProperty(input.element, "files", {
      configurable: true,
      value: [file],
    });

    await input.trigger("change");

    expect(wrapper.emitted("photoSelected")?.[0]).toEqual([file]);
  });

  it("keeps the avatar visible but disables upload without photo permission", async () => {
    const wrapper = mountDashboard({ canManagePhoto: false });
    const input = wrapper.get('[data-testid="employee-dashboard-photo-input"]');
    const clickSpy = vi.spyOn(input.element as HTMLInputElement, "click");

    expect(wrapper.find('[data-testid="employee-dashboard-photo-placeholder"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="employee-dashboard-photo-button"]').attributes("disabled")).toBeDefined();
    await wrapper.get('[data-testid="employee-dashboard-photo-button"]').trigger("click");

    expect(clickSpy).not.toHaveBeenCalled();
  });

  it("shows local avatar upload progress", () => {
    const wrapper = mountDashboard({ photoUploading: true });

    expect(wrapper.get('[data-testid="employee-dashboard-photo-uploading"]').text()).toBe("Uploading photo...");
    expect(wrapper.get('[data-testid="employee-dashboard-photo-button"]').attributes("disabled")).toBeDefined();
  });
});
