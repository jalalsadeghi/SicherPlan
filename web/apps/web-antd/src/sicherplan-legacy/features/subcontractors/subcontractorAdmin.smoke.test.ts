// @vitest-environment happy-dom

import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { defineComponent } from "vue";

import SubcontractorAdminView from "../../views/SubcontractorAdminView.vue";

const authState = vi.hoisted(() => ({
  role: "tenant_admin",
  tenantId: "tenant-1",
  token: "token-1",
}));

const mocks = vi.hoisted(() => ({
  addPlatformDocumentVersionMock: vi.fn(async () => ({})),
  archiveSubcontractorMock: vi.fn(async () => ({})),
  createPlatformDocumentMock: vi.fn(async () => ({ id: "doc-1" })),
  createSubcontractorAddressOptionMock: vi.fn(async () => ({
    id: "address-new",
    street_line_1: "Neue Straße 1",
    street_line_2: null,
    postal_code: "50667",
    city: "Koeln",
    state: null,
    country_code: "DE",
  })),
  createSubcontractorContactMock: vi.fn(async () => ({})),
  createSubcontractorHistoryEntryMock: vi.fn(async () => ({ id: "history-1" })),
  createSubcontractorMock: vi.fn(async () => ({
    id: "subcontractor-new",
    tenant_id: "tenant-1",
    subcontractor_number: "SU-3000",
    legal_name: "DomSchild Sicherheitsdienste GmbH",
    display_name: "",
    managing_director_name: null,
    latitude: null,
    longitude: null,
    status: "active",
    archived_at: null,
    version_no: 1,
  })),
  createSubcontractorScopeMock: vi.fn(async () => ({})),
  downloadSubcontractorDocumentMock: vi.fn(async () => ({ blob: new Blob(), fileName: "file.pdf" })),
  getSubcontractorFinanceProfileMock: vi.fn<() => Promise<any>>(async () => {
    throw new Error("not-found");
  }),
  getSubcontractorReferenceDataMock: vi.fn(async () => ({
    legal_forms: [
      {
        id: "lookup-legal",
        code: "gmbh",
        label: "GmbH",
        description: null,
        is_active: true,
        status: "active",
        archived_at: null,
      },
    ],
  })),
  getSubcontractorMock: vi.fn(async (tenantId: string, subcontractorId: string) => ({
    id: subcontractorId,
    tenant_id: tenantId,
    subcontractor_number: "SU-1000",
    legal_name: "Bestand Partner GmbH",
    display_name: "Bestand Partner",
    managing_director_name: null,
    latitude: null,
    longitude: null,
    status: "active",
    archived_at: null,
    version_no: 3,
    legal_form_lookup_id: null,
    subcontractor_status_lookup_id: null,
    address_id: null,
    notes: null,
    address: null,
    contacts: [],
    scopes: [],
    finance_profile: null,
  })),
  linkSubcontractorHistoryAttachmentMock: vi.fn(async () => ({})),
  listBranchesMock: vi.fn(async () => []),
  listLookupValuesMock: vi.fn(async () => []),
  listMandatesMock: vi.fn(async () => []),
  listSubcontractorAddressOptionsMock: vi.fn(async () => []),
  listSubcontractorContactUserOptionsMock: vi.fn(async () => []),
  listSubcontractorContactsMock: vi.fn(async () => []),
  listSubcontractorHistoryMock: vi.fn(async () => []),
  listSubcontractorScopesMock: vi.fn(async () => []),
  listSubcontractorsMock: vi.fn(async () => [
    {
      id: "subcontractor-1",
      tenant_id: "tenant-1",
      subcontractor_number: "SU-1000",
      legal_name: "Bestand Partner GmbH",
      display_name: "Bestand Partner",
      managing_director_name: null,
      latitude: null,
      longitude: null,
      status: "active",
      archived_at: null,
      version_no: 1,
    },
  ]),
  patchSubcontractorFinanceProfileMock: vi.fn(async () => ({})),
  putSubcontractorFinanceProfileMock: vi.fn(async () => ({})),
  reactivateSubcontractorMock: vi.fn(async () => ({})),
  updateSubcontractorContactMock: vi.fn(async () => ({})),
  updateSubcontractorMock: vi.fn(async () => ({})),
  updateSubcontractorScopeMock: vi.fn(async () => ({})),
}));

vi.mock("@vben/locales", () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}));

vi.mock("@/stores/auth", () => ({
  useAuthStore: () => ({
    accessToken: authState.token,
    effectiveRole: authState.role,
    sessionUser: { tenant_id: authState.tenantId },
    tenantScopeId: authState.tenantId,
    setTenantScopeId: vi.fn(),
  }),
}));

vi.mock("@/api/coreAdmin", () => ({
  listBranches: mocks.listBranchesMock,
  listLookupValues: mocks.listLookupValuesMock,
  listMandates: mocks.listMandatesMock,
}));

vi.mock("@/api/subcontractors", () => ({
  SubcontractorAdminApiError: class MockSubcontractorAdminApiError extends Error {
    statusCode: number;
    code: string;
    messageKey: string;

    constructor(
      statusCodeOrMessageKey: number | string,
      payload?: { code?: string; message_key?: string },
    ) {
      const statusCode = typeof statusCodeOrMessageKey === "number" ? statusCodeOrMessageKey : 500;
      const messageKey =
        typeof statusCodeOrMessageKey === "string"
          ? statusCodeOrMessageKey
          : payload?.message_key || "errors.platform.internal";
      super(messageKey);
      this.statusCode = statusCode;
      this.code = payload?.code || "platform.internal";
      this.messageKey = messageKey;
    }
  },
  addPlatformDocumentVersion: mocks.addPlatformDocumentVersionMock,
  archiveSubcontractor: mocks.archiveSubcontractorMock,
  createPlatformDocument: mocks.createPlatformDocumentMock,
  createSubcontractor: mocks.createSubcontractorMock,
  createSubcontractorAddressOption: mocks.createSubcontractorAddressOptionMock,
  createSubcontractorContact: mocks.createSubcontractorContactMock,
  createSubcontractorHistoryEntry: mocks.createSubcontractorHistoryEntryMock,
  createSubcontractorScope: mocks.createSubcontractorScopeMock,
  downloadSubcontractorDocument: mocks.downloadSubcontractorDocumentMock,
  getSubcontractor: mocks.getSubcontractorMock,
  getSubcontractorFinanceProfile: mocks.getSubcontractorFinanceProfileMock,
  getSubcontractorReferenceData: mocks.getSubcontractorReferenceDataMock,
  linkSubcontractorHistoryAttachment: mocks.linkSubcontractorHistoryAttachmentMock,
  listSubcontractorAddressOptions: mocks.listSubcontractorAddressOptionsMock,
  listSubcontractorContactUserOptions: mocks.listSubcontractorContactUserOptionsMock,
  listSubcontractorContacts: mocks.listSubcontractorContactsMock,
  listSubcontractorHistory: mocks.listSubcontractorHistoryMock,
  listSubcontractorScopes: mocks.listSubcontractorScopesMock,
  listSubcontractors: mocks.listSubcontractorsMock,
  patchSubcontractorFinanceProfile: mocks.patchSubcontractorFinanceProfileMock,
  putSubcontractorFinanceProfile: mocks.putSubcontractorFinanceProfileMock,
  reactivateSubcontractor: mocks.reactivateSubcontractorMock,
  updateSubcontractor: mocks.updateSubcontractorMock,
  updateSubcontractorContact: mocks.updateSubcontractorContactMock,
  updateSubcontractorScope: mocks.updateSubcontractorScopeMock,
}));

const StatusBadgeStub = defineComponent({
  name: "StatusBadgeStub",
  template: '<div class="status-badge-stub" />',
});

const WorkforceStub = defineComponent({
  name: "SubcontractorWorkforcePanelStub",
  template: '<div class="workforce-stub" />',
});

const LocationPickerStub = defineComponent({
  name: "PlanningLocationPickerModal",
  props: {
    open: { type: Boolean, default: false },
  },
  emits: ["update:open", "confirm"],
  template: '<div v-if="open" class="location-picker-stub" />',
});

async function mountView() {
  const wrapper = mount(SubcontractorAdminView, {
    global: {
      stubs: {
        StatusBadge: StatusBadgeStub,
        SubcontractorWorkforcePanel: WorkforceStub,
        PlanningLocationPickerModal: LocationPickerStub,
      },
    },
  });
  await flushPromises();
  await flushPromises();
  return wrapper;
}

describe("SubcontractorAdminView address modal flow", () => {
  beforeEach(() => {
    Object.values(mocks).forEach((mock) => mock.mockClear());
    mocks.listSubcontractorsMock.mockResolvedValue([
      {
        id: "subcontractor-1",
        tenant_id: "tenant-1",
        subcontractor_number: "SU-1000",
        legal_name: "Bestand Partner GmbH",
        display_name: "Bestand Partner",
        managing_director_name: null,
        latitude: null,
        longitude: null,
        status: "active",
        archived_at: null,
        version_no: 1,
      },
    ]);
    mocks.getSubcontractorMock.mockImplementation(async (tenantId: string, subcontractorId: string) => ({
      id: subcontractorId,
      tenant_id: tenantId,
      subcontractor_number: subcontractorId === "subcontractor-new" ? "SU-3000" : "SU-1000",
      legal_name: subcontractorId === "subcontractor-new" ? "DomSchild Sicherheitsdienste GmbH" : "Bestand Partner GmbH",
      display_name: "",
      managing_director_name: null,
      latitude: null,
      longitude: null,
      status: "active",
      archived_at: null,
      version_no: 3,
      legal_form_lookup_id: null,
      subcontractor_status_lookup_id: null,
      address_id: null,
      notes: null,
      address: null,
      contacts: [],
      scopes: [],
      finance_profile: null,
    }));
    mocks.getSubcontractorReferenceDataMock.mockResolvedValue({
      legal_forms: [
        {
          id: "lookup-legal",
          code: "gmbh",
          label: "GmbH",
          description: null,
          is_active: true,
          status: "active",
          archived_at: null,
        },
      ],
    });
    mocks.listBranchesMock.mockResolvedValue([
      {
        id: "branch-1",
        code: "BER",
        name: "Berlin",
        archived_at: null,
      },
      {
        id: "branch-2",
        code: "CGN",
        name: "Koeln",
        archived_at: null,
      },
    ] as any);
    mocks.listMandatesMock.mockResolvedValue([
      {
        id: "mandate-1",
        branch_id: "branch-1",
        code: "M-BER",
        name: "Berlin Mandat",
        archived_at: null,
      },
      {
        id: "mandate-2",
        branch_id: "branch-2",
        code: "M-CGN",
        name: "Koeln Mandat",
        archived_at: null,
      },
    ] as any);
    mocks.listSubcontractorAddressOptionsMock.mockResolvedValue([]);
    mocks.createSubcontractorAddressOptionMock.mockResolvedValue({
      id: "address-new",
      street_line_1: "Neue Straße 1",
      street_line_2: null,
      postal_code: "50667",
      city: "Koeln",
      state: null,
      country_code: "DE",
    });
    mocks.createSubcontractorMock.mockResolvedValue({
      id: "subcontractor-new",
      tenant_id: "tenant-1",
      subcontractor_number: "SU-3000",
      legal_name: "DomSchild Sicherheitsdienste GmbH",
      display_name: "",
      managing_director_name: null,
      latitude: null,
      longitude: null,
      status: "active",
      archived_at: null,
      version_no: 1,
    });
  });

  it("opens the address modal on click in existing-subcontractor mode and applies the created address", async () => {
    const wrapper = await mountView();

    await wrapper.find(".subcontractor-admin-row").trigger("click");
    await flushPromises();
    await flushPromises();

    await wrapper.get('[data-testid="subcontractor-create-address"]').trigger("click");
    expect(wrapper.find('[data-testid="subcontractor-address-modal"]').exists()).toBe(true);

    await wrapper.get('[data-testid="subcontractor-address-street1"]').setValue("Neue Straße 1");
    await wrapper.get('[data-testid="subcontractor-address-postal"]').setValue("50667");
    await wrapper.get('[data-testid="subcontractor-address-city"]').setValue("Koeln");
    await wrapper.get('[data-testid="subcontractor-address-country"]').setValue("DE");
    await wrapper.get('[data-testid="subcontractor-address-modal"] form').trigger("submit");
    await flushPromises();

    expect(mocks.createSubcontractorAddressOptionMock).toHaveBeenCalledTimes(1);
    expect(wrapper.find('[data-testid="subcontractor-address-modal"]').exists()).toBe(false);
    expect((wrapper.get('[data-testid="subcontractor-primary-address"]').element as HTMLSelectElement).value).toBe("address-new");
  });

  it("opens the address modal in create-new mode, stores the address locally, and persists it after subcontractor save", async () => {
    const wrapper = await mountView();

    await wrapper.get('[data-testid="subcontractor-new"]').trigger("click");
    await flushPromises();

    const createAddressButton = wrapper.get('[data-testid="subcontractor-create-address"]');
    expect(createAddressButton.attributes("disabled")).toBeUndefined();

    await createAddressButton.trigger("click");
    expect(wrapper.find('[data-testid="subcontractor-address-modal"]').exists()).toBe(true);

    await wrapper.get('[data-testid="subcontractor-address-street1"]').setValue("Domplatz 1");
    await wrapper.get('[data-testid="subcontractor-address-postal"]').setValue("50667");
    await wrapper.get('[data-testid="subcontractor-address-city"]').setValue("Koeln");
    await wrapper.get('[data-testid="subcontractor-address-country"]').setValue("DE");
    await wrapper.get('[data-testid="subcontractor-address-modal"] form').trigger("submit");
    await flushPromises();

    expect(mocks.createSubcontractorAddressOptionMock).not.toHaveBeenCalled();
    const localAddressValue = (wrapper.get('[data-testid="subcontractor-primary-address"]').element as HTMLInputElement | HTMLSelectElement).value;
    expect(localAddressValue).toMatch(/^pending-address-/);

    await wrapper.get('[data-testid="subcontractor-number"]').setValue("SU-3000");
    await wrapper.get('[data-testid="subcontractor-legal-name"]').setValue("DomSchild Sicherheitsdienste GmbH");
    await wrapper.get('[data-testid="subcontractor-tab-panel-overview"] form').trigger("submit");
    await flushPromises();
    await flushPromises();

    expect(mocks.createSubcontractorMock).toHaveBeenCalledTimes(1);
    expect(mocks.createSubcontractorAddressOptionMock).toHaveBeenCalledTimes(1);
    expect(mocks.updateSubcontractorMock).toHaveBeenCalledTimes(1);
  });

  it("closes the address modal on cancel without changing the current address selection", async () => {
    const wrapper = await mountView();

    await wrapper.get('[data-testid="subcontractor-new"]').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="subcontractor-create-address"]').trigger("click");
    await wrapper.get('[data-testid="subcontractor-address-street1"]').setValue("Domplatz 1");
    await wrapper.get('[data-testid="subcontractor-address-cancel"]').trigger("click");
    await flushPromises();

    expect(wrapper.find('[data-testid="subcontractor-address-modal"]').exists()).toBe(false);
    expect((wrapper.get('[data-testid="subcontractor-primary-address"]').element as HTMLInputElement | HTMLSelectElement).value).toBe("");
    expect(mocks.createSubcontractorAddressOptionMock).not.toHaveBeenCalled();
  });

  it("renders legal form as a lookup select and submits legal_form_lookup_id unchanged", async () => {
    const wrapper = await mountView();

    await wrapper.get('[data-testid="subcontractor-new"]').trigger("click");
    await flushPromises();

    const legalFormSelect = wrapper.get('[data-testid="subcontractor-legal-form"]');
    expect(legalFormSelect.element.tagName).toBe("SELECT");
    expect(legalFormSelect.attributes("disabled")).toBeUndefined();
    expect(wrapper.text()).not.toContain("sicherplan.subcontractors.fields.legalFormHelp");
    expect(wrapper.text()).not.toContain("sicherplan.subcontractors.fields.locationPicker");
    expect(wrapper.text()).not.toContain("sicherplan.subcontractors.fields.locationPickerHelp");
    expect(wrapper.find('[data-testid="subcontractor-pick-location"]').exists()).toBe(true);

    await legalFormSelect.setValue("lookup-legal");
    await wrapper.get('[data-testid="subcontractor-number"]').setValue("SU-3000");
    await wrapper.get('[data-testid="subcontractor-legal-name"]').setValue("DomSchild Sicherheitsdienste GmbH");
    await wrapper.get('[data-testid="subcontractor-tab-panel-overview"] form').trigger("submit");
    await flushPromises();

    expect(mocks.getSubcontractorReferenceDataMock).toHaveBeenCalledTimes(1);
    expect(mocks.createSubcontractorMock).toHaveBeenCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({
        legal_form_lookup_id: "lookup-legal",
      }),
    );
  });

  it("preserves an existing saved legal form value when it is no longer in active options", async () => {
    mocks.getSubcontractorReferenceDataMock.mockResolvedValue({ legal_forms: [] });
    mocks.getSubcontractorFinanceProfileMock.mockImplementation(async () => null);
    mocks.getSubcontractorMock.mockResolvedValue({
      id: "subcontractor-1",
      tenant_id: "tenant-1",
      subcontractor_number: "SU-1000",
      legal_name: "Bestand Partner GmbH",
      display_name: "Bestand Partner",
      managing_director_name: null,
      latitude: null,
      longitude: null,
      status: "active",
      archived_at: null,
      version_no: 3,
      legal_form_lookup_id: "lookup-legacy",
      subcontractor_status_lookup_id: null,
      address_id: null,
      notes: null,
      address: null,
      contacts: [],
      scopes: [],
      finance_profile: null,
    } as any);

    const wrapper = await mountView();
    await wrapper.find(".subcontractor-admin-row").trigger("click");
    await flushPromises();
    await flushPromises();

    const legalFormSelect = wrapper.get('[data-testid="subcontractor-legal-form"]').element as HTMLSelectElement;
    expect(legalFormSelect.value).toBe("lookup-legacy");
    expect([...legalFormSelect.options].some((option) => option.value === "lookup-legacy")).toBe(true);
  });

  it("renders scope branch and mandate as selects, filters mandates by branch, and submits ids unchanged", async () => {
    const wrapper = await mountView();

    await wrapper.find(".subcontractor-admin-row").trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="subcontractor-tab-scope_release"]').trigger("click");
    await flushPromises();

    const branchSelect = wrapper.get('[data-testid="subcontractor-scope-branch"]');
    const mandateSelect = wrapper.get('[data-testid="subcontractor-scope-mandate"]');
    expect(branchSelect.element.tagName).toBe("SELECT");
    expect(mandateSelect.element.tagName).toBe("SELECT");

    await branchSelect.setValue("branch-1");
    expect((branchSelect.element as HTMLSelectElement).value).toBe("branch-1");
    expect(
      [...(mandateSelect.element as HTMLSelectElement).options].some((option) => option.value === "mandate-1"),
    ).toBe(true);
    expect(
      [...(mandateSelect.element as HTMLSelectElement).options].some((option) => option.value === "mandate-2"),
    ).toBe(false);

    await mandateSelect.setValue("mandate-1");
    expect((mandateSelect.element as HTMLSelectElement).value).toBe("mandate-1");

    await branchSelect.setValue("branch-2");
    await flushPromises();
    expect((mandateSelect.element as HTMLSelectElement).value).toBe("");

    await mandateSelect.setValue("mandate-2");
    await wrapper.get('input[type="date"]').setValue("2026-05-01");
    await wrapper.get('[data-testid="subcontractor-tab-panel-scope-release"] form').trigger("submit");
    await flushPromises();

    expect(mocks.createSubcontractorScopeMock).toHaveBeenCalledWith(
      "tenant-1",
      "subcontractor-1",
      "token-1",
      expect.objectContaining({
        branch_id: "branch-2",
        mandate_id: "mandate-2",
      }),
    );
  });

  it("shows neutral ready-state placeholders for scope selects when options are available", async () => {
    const wrapper = await mountView();
    await wrapper.find(".subcontractor-admin-row").trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="subcontractor-tab-scope_release"]').trigger("click");
    await flushPromises();

    const branchSelect = wrapper.get('[data-testid="subcontractor-scope-branch"]').element as HTMLSelectElement;
    const mandateSelect = wrapper.get('[data-testid="subcontractor-scope-mandate"]').element as HTMLSelectElement;
    expect(branchSelect.options[0]?.text).toBe("sicherplan.subcontractors.fields.branchPlaceholder");
    expect(mandateSelect.options[0]?.text).toBe("sicherplan.subcontractors.fields.mandatePlaceholder");
  });

  it("shows unavailable placeholders only when structure loading fails", async () => {
    mocks.listBranchesMock.mockRejectedValueOnce(new Error("branch-failed"));
    mocks.listMandatesMock.mockRejectedValueOnce(new Error("mandate-failed"));

    const wrapper = await mountView();
    await wrapper.find(".subcontractor-admin-row").trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="subcontractor-tab-scope_release"]').trigger("click");
    await flushPromises();

    const branchSelect = wrapper.get('[data-testid="subcontractor-scope-branch"]').element as HTMLSelectElement;
    const mandateSelect = wrapper.get('[data-testid="subcontractor-scope-mandate"]').element as HTMLSelectElement;
    expect(branchSelect.options[0]?.text).toBe("sicherplan.subcontractors.fields.branchUnavailablePlaceholder");
    expect(mandateSelect.options[0]?.text).toBe("sicherplan.subcontractors.fields.mandateUnavailablePlaceholder");
  });

  it("does not eagerly load finance profile when opening overview or scope tabs", async () => {
    const wrapper = await mountView();

    await wrapper.find(".subcontractor-admin-row").trigger("click");
    await flushPromises();
    await flushPromises();

    expect(mocks.getSubcontractorFinanceProfileMock).not.toHaveBeenCalled();

    await wrapper.get('[data-testid="subcontractor-tab-scope_release"]').trigger("click");
    await flushPromises();

    expect(mocks.getSubcontractorFinanceProfileMock).not.toHaveBeenCalled();
    expect(wrapper.find('[data-testid="subcontractor-tab-panel-scope-release"]').exists()).toBe(true);
  });

  it("treats finance-profile 404 as missing and keeps Billing create-ready without breaking other tabs", async () => {
    const FinanceError = (await import("@/api/subcontractors")).SubcontractorAdminApiError;
    mocks.getSubcontractorFinanceProfileMock.mockRejectedValueOnce(
      new FinanceError(404, {
        code: "subcontractors.finance_profile.not_found",
        message_key: "errors.subcontractors.finance_profile.not_found",
        request_id: "req-finance-404",
        details: {},
      }),
    );

    const wrapper = await mountView();
    await wrapper.find(".subcontractor-admin-row").trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="subcontractor-tab-scope_release"]').trigger("click");
    await flushPromises();

    expect(wrapper.find('[data-testid="subcontractor-tab-panel-scope-release"]').exists()).toBe(true);
    expect(wrapper.find(".subcontractor-admin-feedback").exists()).toBe(false);

    await wrapper.get('[data-testid="subcontractor-tab-billing"]').trigger("click");
    await flushPromises();
    await flushPromises();

    expect(mocks.getSubcontractorFinanceProfileMock).toHaveBeenCalledTimes(1);
    expect(wrapper.find('[data-testid="subcontractor-tab-panel-billing"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("sicherplan.subcontractors.actions.createFinance");
    expect(wrapper.find(".subcontractor-admin-feedback").exists()).toBe(false);
  });

  it("still surfaces real non-404 finance-profile errors when Billing is opened", async () => {
    const FinanceError = (await import("@/api/subcontractors")).SubcontractorAdminApiError;
    mocks.getSubcontractorFinanceProfileMock.mockRejectedValueOnce(
      new FinanceError(500, {
        code: "platform.internal_error",
        message_key: "errors.platform.internal",
        request_id: "req-finance-500",
        details: {},
      }),
    );

    const wrapper = await mountView();
    await wrapper.find(".subcontractor-admin-row").trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="subcontractor-tab-billing"]').trigger("click");
    await flushPromises();
    await flushPromises();

    expect(wrapper.find(".subcontractor-admin-feedback").exists()).toBe(true);
  });

  it("preserves existing scope branch and mandate values in edit mode", async () => {
    mocks.listSubcontractorScopesMock.mockResolvedValue([
      {
        id: "scope-1",
        tenant_id: "tenant-1",
        subcontractor_id: "subcontractor-1",
        branch_id: "branch-1",
        mandate_id: "mandate-1",
        valid_from: "2026-05-01",
        valid_to: null,
        notes: null,
        status: "active",
        archived_at: null,
        version_no: 2,
      },
    ] as any);

    const wrapper = await mountView();
    await wrapper.find(".subcontractor-admin-row").trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="subcontractor-tab-scope_release"]').trigger("click");
    await flushPromises();
    await wrapper.find('[data-testid="subcontractor-tab-panel-scope-release"] .subcontractor-admin-row').trigger("click");
    await flushPromises();

    expect((wrapper.get('[data-testid="subcontractor-scope-branch"]').element as HTMLSelectElement).value).toBe("branch-1");
    expect((wrapper.get('[data-testid="subcontractor-scope-mandate"]').element as HTMLSelectElement).value).toBe("mandate-1");
  });
});
