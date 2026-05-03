# Assistant Field Dictionary

## assignment.actor_kind

- canonical_name: actor_kind
- module_key: planning
- page_id: P-04
- entity_type: Assignment
- route_names: SicherPlanPlanningStaffing
- form_contexts: planning_staffing.demand_and_assignment, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: False
- confidence: low
- labels_de: Aktor-Typ
- labels_en: Actor kind
- definition_de: Feld Aktor-Typ im Kontext von Assignment.
- definition_en: Actor kind field used in the Assignment context.
- related_fields: none
- aliases: actor_kind, Actor kind, Aktor-Typ, Assignment
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.demand_and_assignment includes field actor_kind labeled Actor kind.
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.demand_and_assignment includes field actor_kind labeled Aktor-Typ.

## assignment.date_from

- canonical_name: date_from
- module_key: planning
- page_id: P-04
- entity_type: Assignment
- route_names: SicherPlanPlanningStaffing
- form_contexts: planning_staffing.filters_and_scope, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: False
- confidence: medium
- labels_de: Von
- labels_en: From
- definition_de: Feld Von im Kontext von Assignment.
- definition_en: From field used in the Assignment context.
- related_fields: none
- aliases: date_from, From, Von, Assignment
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.filters_and_scope includes field date_from labeled From.
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.filters_and_scope includes field date_from labeled Von.
  - [typescript_api_interface] ShiftSeriesListItem: ShiftSeriesListItem includes field date_from.
  - [typescript_api_interface] CoverageFilterParams: CoverageFilterParams includes field date_from.
  - [typescript_api_interface] DemandGroupBulkApplyRequest: DemandGroupBulkApplyRequest includes field date_from.
  - [typescript_api_interface] DemandGroupBulkUpdateRequest: DemandGroupBulkUpdateRequest includes field date_from.
  - [backend_schema] AssistantPlanningShiftSearchInput: AssistantPlanningShiftSearchInput includes field date_from.
  - [backend_schema] AssistantPlanningAssignmentSearchInput: AssistantPlanningAssignmentSearchInput includes field date_from.

## assignment.date_to

- canonical_name: date_to
- module_key: planning
- page_id: P-04
- entity_type: Assignment
- route_names: SicherPlanPlanningStaffing
- form_contexts: planning_staffing.filters_and_scope, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: False
- confidence: medium
- labels_de: Bis
- labels_en: To
- definition_de: Feld Bis im Kontext von Assignment.
- definition_en: To field used in the Assignment context.
- related_fields: none
- aliases: date_to, To, Bis, Assignment
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.filters_and_scope includes field date_to labeled To.
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.filters_and_scope includes field date_to labeled Bis.
  - [typescript_api_interface] ShiftSeriesListItem: ShiftSeriesListItem includes field date_to.
  - [typescript_api_interface] CoverageFilterParams: CoverageFilterParams includes field date_to.
  - [typescript_api_interface] DemandGroupBulkApplyRequest: DemandGroupBulkApplyRequest includes field date_to.
  - [typescript_api_interface] DemandGroupBulkUpdateRequest: DemandGroupBulkUpdateRequest includes field date_to.
  - [backend_schema] AssistantPlanningShiftSearchInput: AssistantPlanningShiftSearchInput includes field date_to.
  - [backend_schema] AssistantPlanningAssignmentSearchInput: AssistantPlanningAssignmentSearchInput includes field date_to.

## assignment.demand_group_id

- canonical_name: demand_group_id
- module_key: planning
- page_id: P-04
- entity_type: Assignment
- route_names: SicherPlanPlanningStaffing
- form_contexts: planning_staffing.demand_and_assignment, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: False
- confidence: medium
- labels_de: Demand Group
- labels_en: Demand group
- definition_de: Feld Demand Group im Kontext von Assignment.
- definition_en: Demand group field used in the Assignment context.
- related_fields: none
- aliases: demand_group_id, Demand group, Demand Group, Assignment
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.demand_and_assignment includes field demand_group_id labeled Demand group.
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.demand_and_assignment includes field demand_group_id labeled Demand Group.
  - [typescript_api_interface] CoverageDemandGroupItem: CoverageDemandGroupItem includes field demand_group_id.
  - [typescript_api_interface] StaffingBoardAssignmentItem: StaffingBoardAssignmentItem includes field demand_group_id.
  - [typescript_api_interface] AssignmentRead: AssignmentRead includes field demand_group_id.
  - [typescript_api_interface] DemandGroupBulkUpdateItemResult: DemandGroupBulkUpdateItemResult includes field demand_group_id.
  - [typescript_api_interface] SubcontractorReleaseRead: SubcontractorReleaseRead includes field demand_group_id.
  - [typescript_api_interface] StaffingAssignCommand: StaffingAssignCommand includes field demand_group_id.

## assignment.member_ref

- canonical_name: member_ref
- module_key: planning
- page_id: P-04
- entity_type: Assignment
- route_names: SicherPlanPlanningStaffing
- form_contexts: planning_staffing.demand_and_assignment, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: False
- confidence: low
- labels_de: Mitarbeiter
- labels_en: Employee
- definition_de: Feld Mitarbeiter im Kontext von Assignment.
- definition_en: Employee field used in the Assignment context.
- related_fields: none
- aliases: member_ref, Employee, Mitarbeiter, Assignment
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.demand_and_assignment includes field member_ref labeled Employee.
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.demand_and_assignment includes field member_ref labeled Mitarbeiter.

## assignment.planning_mode_code

- canonical_name: planning_mode_code
- module_key: planning
- page_id: P-04
- entity_type: Assignment
- route_names: SicherPlanPlanningStaffing
- form_contexts: planning_staffing.filters_and_scope, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: False
- confidence: medium
- labels_de: Planungsmodus
- labels_en: Planning mode
- definition_de: Feld Planungsmodus im Kontext von Assignment.
- definition_en: Planning mode field used in the Assignment context.
- related_fields: none
- aliases: planning_mode_code, Planning mode, Planungsmodus, Assignment
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.filters_and_scope includes field planning_mode_code labeled Planning mode.
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.filters_and_scope includes field planning_mode_code labeled Planungsmodus.
  - [typescript_api_interface] CustomerDashboardPlanItemRead: CustomerDashboardPlanItemRead includes field planning_mode_code.
  - [typescript_api_interface] CustomerRateLineRead: CustomerRateLineRead includes field planning_mode_code.
  - [typescript_api_interface] CustomerRateLinePayload: CustomerRateLinePayload includes field planning_mode_code.
  - [typescript_api_interface] FinanceBillingTimesheetLineRead: FinanceBillingTimesheetLineRead includes field planning_mode_code.
  - [typescript_api_interface] PlanningRecordListItem: PlanningRecordListItem includes field planning_mode_code.
  - [typescript_api_interface] PlanningRecordListFilters: PlanningRecordListFilters includes field planning_mode_code.

## assignment.planning_record_id

- canonical_name: planning_record_id
- module_key: planning
- page_id: P-04
- entity_type: Assignment
- route_names: SicherPlanPlanningStaffing
- form_contexts: planning_staffing.filters_and_scope, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: False
- confidence: medium
- labels_de: Planungsdatensatz
- labels_en: Planning record
- definition_de: Feld Planungsdatensatz im Kontext von Assignment.
- definition_en: Planning record field used in the Assignment context.
- related_fields: none
- aliases: planning_record_id, Planning record, Planungsdatensatz, Assignment
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.filters_and_scope includes field planning_record_id labeled Planning record.
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.filters_and_scope includes field planning_record_id labeled Planungsdatensatz.
  - [typescript_api_interface] CustomerDashboardCalendarItemRead: CustomerDashboardCalendarItemRead includes field planning_record_id.
  - [typescript_api_interface] FinanceBillingTimesheetLineRead: FinanceBillingTimesheetLineRead includes field planning_record_id.
  - [typescript_api_interface] FinanceBillingTimesheetRead: FinanceBillingTimesheetRead includes field planning_record_id.
  - [typescript_api_interface] PlanningCommercialLinkRead: PlanningCommercialLinkRead includes field planning_record_id.
  - [typescript_api_interface] ShiftPlanListItem: ShiftPlanListItem includes field planning_record_id.
  - [typescript_api_interface] PlanningBoardShiftListItem: PlanningBoardShiftListItem includes field planning_record_id.

## assignment.subcontractor_releases

- canonical_name: subcontractor_releases
- module_key: planning
- page_id: P-04
- entity_type: Assignment
- route_names: SicherPlanPlanningStaffing
- form_contexts: planning_staffing.teams_and_releases, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: False
- confidence: medium
- labels_de: Partnerfreigaben
- labels_en: Partner releases
- definition_de: Feld Partnerfreigaben im Kontext von Assignment.
- definition_en: Partner releases field used in the Assignment context.
- related_fields: none
- aliases: subcontractor_releases, Partner releases, Partnerfreigaben, Assignment
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.teams_and_releases includes field subcontractor_releases labeled Partner releases.
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.teams_and_releases includes field subcontractor_releases labeled Partnerfreigaben.
  - [backend_schema] DemandGroup: DemandGroup includes field subcontractor_releases.

## assignment.team_id

- canonical_name: team_id
- module_key: planning
- page_id: P-04
- entity_type: Assignment
- route_names: SicherPlanPlanningStaffing
- form_contexts: planning_staffing.demand_and_assignment, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: False
- confidence: medium
- labels_de: Team
- labels_en: Team
- definition_de: Feld Team im Kontext von Assignment.
- definition_en: Team field used in the Assignment context.
- related_fields: none
- aliases: team_id, Team, Assignment
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.demand_and_assignment includes field team_id labeled Team.
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.demand_and_assignment includes field team_id labeled Team.
  - [typescript_api_interface] StaffingBoardAssignmentItem: StaffingBoardAssignmentItem includes field team_id.
  - [typescript_api_interface] AssignmentRead: AssignmentRead includes field team_id.
  - [typescript_api_interface] TeamMemberRead: TeamMemberRead includes field team_id.
  - [typescript_api_interface] TeamMemberCreate: TeamMemberCreate includes field team_id.
  - [typescript_api_interface] StaffingAssignCommand: StaffingAssignCommand includes field team_id.
  - [typescript_api_interface] AssignmentCreate: AssignmentCreate includes field team_id.

## assignment.team_name

- canonical_name: team_name
- module_key: planning
- page_id: P-04
- entity_type: Assignment
- route_names: SicherPlanPlanningStaffing
- form_contexts: planning_staffing.teams_and_releases, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: False
- confidence: low
- labels_de: Teamname
- labels_en: Team name
- definition_de: Feld Teamname im Kontext von Assignment.
- definition_en: Team name field used in the Assignment context.
- related_fields: none
- aliases: team_name, Team name, Teamname, Assignment
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.teams_and_releases includes field team_name labeled Team name.
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.teams_and_releases includes field team_name labeled Teamname.

## assignment.team_scope

- canonical_name: team_scope
- module_key: planning
- page_id: P-04
- entity_type: Assignment
- route_names: SicherPlanPlanningStaffing
- form_contexts: planning_staffing.teams_and_releases, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: False
- confidence: low
- labels_de: Team-Scope
- labels_en: Team scope
- definition_de: Feld Team-Scope im Kontext von Assignment.
- definition_en: Team scope field used in the Assignment context.
- related_fields: none
- aliases: team_scope, Team scope, Team-Scope, Assignment
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.teams_and_releases includes field team_scope labeled Team scope.
  - [page_help_manifest] Assistant Page Help Manifest: P-04 manifest section planning_staffing.teams_and_releases includes field team_scope labeled Team-Scope.

## customer.address

- canonical_name: address
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: SicherPlanCustomers
- form_contexts: customers.contacts_addresses_billing, customer_create, customer_scoped_order_create, customer_order_create, customer_plan_create
- input_type: input
- required: False
- confidence: high
- labels_de: Adresse
- labels_en: Address
- definition_de: Feld Adresse im Kontext von Customer.
- definition_en: Address field used in the Customer context.
- related_fields: none
- aliases: address, Address, Adresse, customerAdmin.fields.address, addressDraft.address_id, Customer
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.contacts_addresses_billing includes field address labeled Address.
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.contacts_addresses_billing includes field address labeled Adresse.
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.address defines labels Address, Adresse.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds addressDraft.address_id next to customerAdmin.fields.address.
  - [typescript_api_interface] CustomerInvoicePartyRead: CustomerInvoicePartyRead includes field address.
  - [typescript_api_interface] EmployeeAddressHistoryCreatePayload: EmployeeAddressHistoryCreatePayload includes field address.
  - [typescript_api_interface] EmployeeAddressHistoryUpdatePayload: EmployeeAddressHistoryUpdatePayload includes field address.
  - [backend_schema] Branch: Branch includes field address.

## customer.address_id

- canonical_name: address_id
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: unknown
- required: unknown
- confidence: medium
- labels_de: Adress-ID
- labels_en: Address ID
- definition_de: Feld Adress-ID im Kontext von Customer.
- definition_en: Address ID field used in the Customer context.
- related_fields: none
- aliases: address_id, customerAdmin.fields.addressId, Adress-ID, Address ID, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.addressId defines labels Address ID, Adress-ID.
  - [typescript_api_interface] BranchRead: BranchRead includes field address_id.
  - [typescript_api_interface] TenantOnboardingPayload: TenantOnboardingPayload includes field address_id.
  - [typescript_api_interface] BranchCreatePayload: BranchCreatePayload includes field address_id.
  - [typescript_api_interface] BranchUpdatePayload: BranchUpdatePayload includes field address_id.
  - [typescript_api_interface] CustomerAddressRead: CustomerAddressRead includes field address_id.
  - [typescript_api_interface] CustomerInvoicePartyRead: CustomerInvoicePartyRead includes field address_id.
  - [typescript_api_interface] CustomerInvoicePartyPayload: CustomerInvoicePartyPayload includes field address_id.

## customer.address_type

- canonical_name: address_type
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Adresstyp
- labels_en: Address type
- definition_de: Feld Adresstyp im Kontext von Customer.
- definition_en: Address type field used in the Customer context.
- related_fields: none
- aliases: address_type, customerAdmin.fields.addressType, addressDraft.address_type, Adresstyp, Address type, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.addressType defines labels Address type, Adresstyp.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds addressDraft.address_type next to customerAdmin.fields.addressType.
  - [typescript_api_interface] CustomerAddressRead: CustomerAddressRead includes field address_type.
  - [typescript_api_interface] CustomerAddressPayload: CustomerAddressPayload includes field address_type.
  - [typescript_api_interface] EmployeeAddressHistoryRead: EmployeeAddressHistoryRead includes field address_type.
  - [typescript_api_interface] EmployeeAddressHistoryCreatePayload: EmployeeAddressHistoryCreatePayload includes field address_type.
  - [typescript_api_interface] EmployeeAddressHistoryUpdatePayload: EmployeeAddressHistoryUpdatePayload includes field address_type.
  - [backend_schema] CustomerAddressLink: CustomerAddressLink includes field address_type.

## customer.amount_mode

- canonical_name: amount_mode
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: unknown
- required: unknown
- confidence: low
- labels_de: Betragsmodus
- labels_en: Amount mode
- definition_de: Feld Betragsmodus im Kontext von Customer.
- definition_en: Amount mode field used in the Customer context.
- related_fields: none
- aliases: amount_mode, customerAdmin.fields.amountMode, Betragsmodus, Amount mode, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.amountMode defines labels Amount mode, Betragsmodus.

## customer.bank_account_holder

- canonical_name: bank_account_holder
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Kontoinhaber
- labels_en: Account holder
- definition_de: Feld Kontoinhaber im Kontext von Customer.
- definition_en: Account holder field used in the Customer context.
- related_fields: none
- aliases: bank_account_holder, customerAdmin.fields.bankAccountHolder, billingProfileDraft.bank_account_holder, Kontoinhaber, Account holder, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.bankAccountHolder defines labels Account holder, Kontoinhaber.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds billingProfileDraft.bank_account_holder next to customerAdmin.fields.bankAccountHolder.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field bank_account_holder.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field bank_account_holder.
  - [typescript_api_interface] EmployeePrivateProfileRead: EmployeePrivateProfileRead includes field bank_account_holder.
  - [typescript_api_interface] EmployeePrivateProfileWritePayload: EmployeePrivateProfileWritePayload includes field bank_account_holder.
  - [typescript_api_interface] EmployeePrivateProfileUpdatePayload: EmployeePrivateProfileUpdatePayload includes field bank_account_holder.
  - [typescript_api_interface] SubcontractorFinanceProfileRead: SubcontractorFinanceProfileRead includes field bank_account_holder.

## customer.bank_bic

- canonical_name: bank_bic
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: BIC
- labels_en: BIC
- definition_de: Feld BIC im Kontext von Customer.
- definition_en: BIC field used in the Customer context.
- related_fields: none
- aliases: bank_bic, customerAdmin.fields.bankBic, billingProfileDraft.bank_bic, BIC, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.bankBic defines labels BIC, BIC.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds billingProfileDraft.bank_bic next to customerAdmin.fields.bankBic.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field bank_bic.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field bank_bic.
  - [typescript_api_interface] EmployeePrivateProfileRead: EmployeePrivateProfileRead includes field bank_bic.
  - [typescript_api_interface] EmployeePrivateProfileWritePayload: EmployeePrivateProfileWritePayload includes field bank_bic.
  - [typescript_api_interface] EmployeePrivateProfileUpdatePayload: EmployeePrivateProfileUpdatePayload includes field bank_bic.
  - [typescript_api_interface] SubcontractorFinanceProfileRead: SubcontractorFinanceProfileRead includes field bank_bic.

## customer.bank_iban

- canonical_name: bank_iban
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: IBAN
- labels_en: IBAN
- definition_de: Feld IBAN im Kontext von Customer.
- definition_en: IBAN field used in the Customer context.
- related_fields: none
- aliases: bank_iban, customerAdmin.fields.bankIban, billingProfileDraft.bank_iban, IBAN, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.bankIban defines labels IBAN, IBAN.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds billingProfileDraft.bank_iban next to customerAdmin.fields.bankIban.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field bank_iban.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field bank_iban.
  - [typescript_api_interface] EmployeePrivateProfileRead: EmployeePrivateProfileRead includes field bank_iban.
  - [typescript_api_interface] EmployeePrivateProfileWritePayload: EmployeePrivateProfileWritePayload includes field bank_iban.
  - [typescript_api_interface] EmployeePrivateProfileUpdatePayload: EmployeePrivateProfileUpdatePayload includes field bank_iban.
  - [typescript_api_interface] SubcontractorFinanceProfileRead: SubcontractorFinanceProfileRead includes field bank_iban.

## customer.bank_name

- canonical_name: bank_name
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Bankname
- labels_en: Bank name
- definition_de: Feld Bankname im Kontext von Customer.
- definition_en: Bank name field used in the Customer context.
- related_fields: none
- aliases: bank_name, customerAdmin.fields.bankName, billingProfileDraft.bank_name, Bankname, Bank name, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.bankName defines labels Bank name, Bankname.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds billingProfileDraft.bank_name next to customerAdmin.fields.bankName.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field bank_name.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field bank_name.
  - [typescript_api_interface] SubcontractorFinanceProfileRead: SubcontractorFinanceProfileRead includes field bank_name.
  - [backend_schema] CustomerBillingProfile: CustomerBillingProfile includes field bank_name.
  - [backend_schema] CustomerBillingProfileCreate: CustomerBillingProfileCreate includes field bank_name.
  - [backend_schema] CustomerBillingProfileUpdate: CustomerBillingProfileUpdate includes field bank_name.

## customer.billing_address

- canonical_name: billing_address
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: medium
- labels_de: Rechnungsadresse
- labels_en: Billing address
- definition_de: Feld Rechnungsadresse im Kontext von Customer.
- definition_en: Billing address field used in the Customer context.
- related_fields: none
- aliases: billing_address, customerAdmin.fields.billingAddress, invoicePartyDraft.address_id, Rechnungsadresse, Billing address, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.billingAddress defines labels Billing address, Rechnungsadresse.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds invoicePartyDraft.address_id next to customerAdmin.fields.billingAddress.

## customer.billing_note

- canonical_name: billing_note
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: textarea
- required: unknown
- confidence: high
- labels_de: Abrechnungsnotiz
- labels_en: Billing note
- definition_de: Feld Abrechnungsnotiz im Kontext von Customer.
- definition_en: Billing note field used in the Customer context.
- related_fields: none
- aliases: billing_note, customerAdmin.fields.billingNote, billingProfileDraft.billing_note, Abrechnungsnotiz, Billing note, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.billingNote defines labels Abrechnungsnotiz, Billing note.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds billingProfileDraft.billing_note next to customerAdmin.fields.billingNote.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field billing_note.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field billing_note.
  - [typescript_api_interface] SubcontractorFinanceProfileRead: SubcontractorFinanceProfileRead includes field billing_note.
  - [backend_schema] CustomerBillingProfile: CustomerBillingProfile includes field billing_note.
  - [backend_schema] CustomerBillingProfileCreate: CustomerBillingProfileCreate includes field billing_note.
  - [backend_schema] CustomerBillingProfileUpdate: CustomerBillingProfileUpdate includes field billing_note.

## customer.billing_unit

- canonical_name: billing_unit
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Abrechnungseinheit
- labels_en: Billing unit
- definition_de: Feld Abrechnungseinheit im Kontext von Customer.
- definition_en: Billing unit field used in the Customer context.
- related_fields: none
- aliases: billing_unit, customerAdmin.fields.billingUnit, rateLineDraft.billing_unit, Abrechnungseinheit, Billing unit, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.billingUnit defines labels Abrechnungseinheit, Billing unit.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds rateLineDraft.billing_unit next to customerAdmin.fields.billingUnit.
  - [typescript_api_interface] CustomerRateLineRead: CustomerRateLineRead includes field billing_unit.
  - [typescript_api_interface] CustomerRateLinePayload: CustomerRateLinePayload includes field billing_unit.
  - [backend_schema] CustomerRateLine: CustomerRateLine includes field billing_unit.
  - [backend_schema] CustomerRateLineCreate: CustomerRateLineCreate includes field billing_unit.
  - [backend_schema] CustomerRateLineUpdate: CustomerRateLineUpdate includes field billing_unit.
  - [backend_schema] CustomerRateLineRead: CustomerRateLineRead includes field billing_unit.

## customer.city

- canonical_name: city
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Ort
- labels_en: City
- definition_de: Feld Ort im Kontext von Customer.
- definition_en: City field used in the Customer context.
- related_fields: none
- aliases: city, customerAdmin.fields.city, addressDirectoryDraft.city, Ort, City, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.city defines labels City, Ort.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds addressDirectoryDraft.city next to customerAdmin.fields.city.
  - [typescript_api_interface] CustomerAddressRead: CustomerAddressRead includes field city.
  - [typescript_api_interface] CustomerAvailableAddressRead: CustomerAvailableAddressRead includes field city.
  - [typescript_api_interface] CustomerAvailableAddressCreatePayload: CustomerAvailableAddressCreatePayload includes field city.
  - [typescript_api_interface] EmployeeAddressHistoryRead: EmployeeAddressHistoryRead includes field city.
  - [typescript_api_interface] EmployeeAddressWriteAddressInput: EmployeeAddressWriteAddressInput includes field city.
  - [backend_schema] Address: Address includes field city.

## customer.classification_lookup_id

- canonical_name: classification_lookup_id
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: SicherPlanCustomers
- form_contexts: customers.master_profile, customer_create, customer_scoped_order_create, customer_order_create, customer_plan_create
- input_type: input
- required: False
- confidence: high
- labels_de: Klassifikation
- labels_en: Classification
- definition_de: Feld Klassifikation im Kontext von Customer.
- definition_en: Classification field used in the Customer context.
- related_fields: none
- aliases: classification_lookup_id, Classification, Klassifikation, customerAdmin.fields.classificationLookupId, customerDraft.classification_lookup_id, Customer
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.master_profile includes field classification_lookup_id labeled Classification.
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.master_profile includes field classification_lookup_id labeled Klassifikation.
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.classificationLookupId defines labels Classification, Klassifikation.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds customerDraft.classification_lookup_id next to customerAdmin.fields.classificationLookupId.
  - [typescript_api_interface] CustomerListItem: CustomerListItem includes field classification_lookup_id.
  - [typescript_api_interface] CustomerCreatePayload: CustomerCreatePayload includes field classification_lookup_id.
  - [backend_schema] Customer: Customer includes field classification_lookup_id.
  - [backend_schema] CustomerCreate: CustomerCreate includes field classification_lookup_id.

## customer.company_name

- canonical_name: company_name
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Firmenname
- labels_en: Company name
- definition_de: Feld Firmenname im Kontext von Customer.
- definition_en: Company name field used in the Customer context.
- related_fields: none
- aliases: company_name, customerAdmin.fields.companyName, invoicePartyDraft.company_name, Firmenname, Company name, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.companyName defines labels Company name, Firmenname.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds invoicePartyDraft.company_name next to customerAdmin.fields.companyName.
  - [typescript_api_interface] CustomerInvoicePartyRead: CustomerInvoicePartyRead includes field company_name.
  - [typescript_api_interface] CustomerInvoicePartyPayload: CustomerInvoicePartyPayload includes field company_name.
  - [backend_schema] CustomerInvoiceParty: CustomerInvoiceParty includes field company_name.
  - [backend_schema] CustomerInvoicePartyCreate: CustomerInvoicePartyCreate includes field company_name.
  - [backend_schema] CustomerInvoicePartyUpdate: CustomerInvoicePartyUpdate includes field company_name.
  - [backend_schema] CustomerInvoicePartyListItem: CustomerInvoicePartyListItem includes field company_name.

## customer.contact_name

- canonical_name: contact_name
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Ansprechpartner
- labels_en: Contact name
- definition_de: Feld Ansprechpartner im Kontext von Customer.
- definition_en: Contact name field used in the Customer context.
- related_fields: none
- aliases: contact_name, customerAdmin.fields.contactName, invoicePartyDraft.contact_name, Ansprechpartner, Contact name, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.contactName defines labels Ansprechpartner, Contact name.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds invoicePartyDraft.contact_name next to customerAdmin.fields.contactName.
  - [typescript_api_interface] CustomerPortalAccessListItem: CustomerPortalAccessListItem includes field contact_name.
  - [typescript_api_interface] CustomerLoginHistoryEntryRead: CustomerLoginHistoryEntryRead includes field contact_name.
  - [typescript_api_interface] CustomerInvoicePartyRead: CustomerInvoicePartyRead includes field contact_name.
  - [typescript_api_interface] CustomerInvoicePartyPayload: CustomerInvoicePartyPayload includes field contact_name.
  - [backend_schema] CustomerInvoiceParty: CustomerInvoiceParty includes field contact_name.
  - [backend_schema] CustomerInvoicePartyCreate: CustomerInvoicePartyCreate includes field contact_name.

## customer.contact_title

- canonical_name: contact_title
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: medium
- labels_de: Titel
- labels_en: Title
- definition_de: Feld Titel im Kontext von Customer.
- definition_en: Title field used in the Customer context.
- related_fields: none
- aliases: contact_title, customerAdmin.fields.contactTitle, contactDraft.title, Titel, Title, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.contactTitle defines labels Titel, Title.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds contactDraft.title next to customerAdmin.fields.contactTitle.

## customer.contract_reference

- canonical_name: contract_reference
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Vertragsreferenz
- labels_en: Contract reference
- definition_de: Feld Vertragsreferenz im Kontext von Customer.
- definition_en: Contract reference field used in the Customer context.
- related_fields: none
- aliases: contract_reference, customerAdmin.fields.contractReference, billingProfileDraft.contract_reference, Vertragsreferenz, Contract reference, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.contractReference defines labels Contract reference, Vertragsreferenz.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds billingProfileDraft.contract_reference next to customerAdmin.fields.contractReference.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field contract_reference.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field contract_reference.
  - [backend_schema] CustomerBillingProfile: CustomerBillingProfile includes field contract_reference.
  - [backend_schema] CustomerBillingProfileCreate: CustomerBillingProfileCreate includes field contract_reference.
  - [backend_schema] CustomerBillingProfileUpdate: CustomerBillingProfileUpdate includes field contract_reference.
  - [backend_schema] CustomerBillingProfileRead: CustomerBillingProfileRead includes field contract_reference.

## customer.country_code

- canonical_name: country_code
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Ländercode
- labels_en: Country code
- definition_de: Feld Ländercode im Kontext von Customer.
- definition_en: Country code field used in the Customer context.
- related_fields: none
- aliases: country_code, customerAdmin.fields.countryCode, addressDirectoryDraft.country_code, Ländercode, Country code, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.countryCode defines labels Country code, Ländercode.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds addressDirectoryDraft.country_code next to customerAdmin.fields.countryCode.
  - [typescript_api_interface] CustomerAddressRead: CustomerAddressRead includes field country_code.
  - [typescript_api_interface] CustomerAvailableAddressRead: CustomerAvailableAddressRead includes field country_code.
  - [typescript_api_interface] CustomerAvailableAddressCreatePayload: CustomerAvailableAddressCreatePayload includes field country_code.
  - [typescript_api_interface] EmployeeAddressHistoryRead: EmployeeAddressHistoryRead includes field country_code.
  - [typescript_api_interface] EmployeeAddressWriteAddressInput: EmployeeAddressWriteAddressInput includes field country_code.
  - [backend_schema] Address: Address includes field country_code.

## customer.currency_code

- canonical_name: currency_code
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Währung
- labels_en: Currency
- definition_de: Feld Währung im Kontext von Customer.
- definition_en: Currency field used in the Customer context.
- related_fields: none
- aliases: currency_code, customerAdmin.fields.currencyCode, rateCardDraft.currency_code, Währung, Currency, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.currencyCode defines labels Currency, Währung.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds rateCardDraft.currency_code next to customerAdmin.fields.currencyCode.
  - [typescript_api_interface] CustomerPortalInvoiceRead: CustomerPortalInvoiceRead includes field currency_code.
  - [typescript_api_interface] CustomerDashboardFinanceSummaryRead: CustomerDashboardFinanceSummaryRead includes field currency_code.
  - [typescript_api_interface] CustomerSurchargeRuleRead: CustomerSurchargeRuleRead includes field currency_code.
  - [typescript_api_interface] CustomerRateCardRead: CustomerRateCardRead includes field currency_code.
  - [typescript_api_interface] CustomerRateCardPayload: CustomerRateCardPayload includes field currency_code.
  - [typescript_api_interface] CustomerSurchargeRulePayload: CustomerSurchargeRulePayload includes field currency_code.

## customer.customer_number

- canonical_name: customer_number
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: SicherPlanCustomers
- form_contexts: customers.master_profile, customer_create, customer_scoped_order_create, customer_order_create, customer_plan_create
- input_type: input
- required: True
- confidence: high
- labels_de: Kundennummer
- labels_en: Customer number
- definition_de: Feld Kundennummer im Kontext von Customer.
- definition_en: Customer number field used in the Customer context.
- related_fields: none
- aliases: customer_number, Customer number, Kundennummer, customerAdmin.fields.customerNumber, customerDraft.customer_number, Customer, شماره مشتری
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.master_profile includes field customer_number labeled Customer number.
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.master_profile includes field customer_number labeled Kundennummer.
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.customerNumber defines labels Customer number, Kundennummer.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds customerDraft.customer_number next to customerAdmin.fields.customerNumber.
  - [typescript_api_interface] CustomerPortalContextRead: CustomerPortalContextRead includes field customer_number.
  - [typescript_api_interface] CustomerListItem: CustomerListItem includes field customer_number.
  - [typescript_api_interface] CustomerCreatePayload: CustomerCreatePayload includes field customer_number.
  - [backend_schema] Customer: Customer includes field customer_number.

## customer.customer_status_lookup_id

- canonical_name: customer_status_lookup_id
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Kundenstatus-Metadaten
- labels_en: Customer status metadata
- definition_de: Feld Kundenstatus-Metadaten im Kontext von Customer.
- definition_en: Customer status metadata field used in the Customer context.
- related_fields: none
- aliases: customer_status_lookup_id, customerAdmin.fields.customerStatusLookupId, customerDraft.customer_status_lookup_id, Kundenstatus-Metadaten, Customer status metadata, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.customerStatusLookupId defines labels Customer status metadata, Kundenstatus-Metadaten.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds customerDraft.customer_status_lookup_id next to customerAdmin.fields.customerStatusLookupId.
  - [typescript_api_interface] CustomerListItem: CustomerListItem includes field customer_status_lookup_id.
  - [typescript_api_interface] CustomerCreatePayload: CustomerCreatePayload includes field customer_status_lookup_id.
  - [backend_schema] Customer: Customer includes field customer_status_lookup_id.
  - [backend_schema] CustomerCreate: CustomerCreate includes field customer_status_lookup_id.
  - [backend_schema] CustomerUpdate: CustomerUpdate includes field customer_status_lookup_id.
  - [backend_schema] CustomerListItem: CustomerListItem includes field customer_status_lookup_id.

## customer.debtor_number

- canonical_name: debtor_number
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Debitorennummer
- labels_en: Debtor number
- definition_de: Feld Debitorennummer im Kontext von Customer.
- definition_en: Debtor number field used in the Customer context.
- related_fields: none
- aliases: debtor_number, customerAdmin.fields.debtorNumber, billingProfileDraft.debtor_number, Debitorennummer, Debtor number, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.debtorNumber defines labels Debitorennummer, Debtor number.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds billingProfileDraft.debtor_number next to customerAdmin.fields.debtorNumber.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field debtor_number.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field debtor_number.
  - [backend_schema] CustomerBillingProfile: CustomerBillingProfile includes field debtor_number.
  - [backend_schema] CustomerBillingProfileCreate: CustomerBillingProfileCreate includes field debtor_number.
  - [backend_schema] CustomerBillingProfileUpdate: CustomerBillingProfileUpdate includes field debtor_number.
  - [backend_schema] CustomerBillingProfileRead: CustomerBillingProfileRead includes field debtor_number.

## customer.default_branch_id

- canonical_name: default_branch_id
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Standardniederlassung
- labels_en: Default branch
- definition_de: Feld Standardniederlassung im Kontext von Customer.
- definition_en: Default branch field used in the Customer context.
- related_fields: none
- aliases: default_branch_id, customerAdmin.fields.defaultBranchId, advancedFilterDraft.default_branch_id, Standardniederlassung, Default branch, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.defaultBranchId defines labels Default branch, Standardniederlassung.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds advancedFilterDraft.default_branch_id next to customerAdmin.fields.defaultBranchId.
  - [typescript_api_interface] CustomerListItem: CustomerListItem includes field default_branch_id.
  - [typescript_api_interface] CustomerFilterParams: CustomerFilterParams includes field default_branch_id.
  - [typescript_api_interface] CustomerCreatePayload: CustomerCreatePayload includes field default_branch_id.
  - [typescript_api_interface] EmployeeListItem: EmployeeListItem includes field default_branch_id.
  - [typescript_api_interface] EmployeeListFilters: EmployeeListFilters includes field default_branch_id.
  - [backend_schema] Customer: Customer includes field default_branch_id.

## customer.default_mandate_id

- canonical_name: default_mandate_id
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Standardmandat
- labels_en: Default mandate
- definition_de: Feld Standardmandat im Kontext von Customer.
- definition_en: Default mandate field used in the Customer context.
- related_fields: none
- aliases: default_mandate_id, customerAdmin.fields.defaultMandateId, advancedFilterDraft.default_mandate_id, Standardmandat, Default mandate, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.defaultMandateId defines labels Default mandate, Standardmandat.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds advancedFilterDraft.default_mandate_id next to customerAdmin.fields.defaultMandateId.
  - [typescript_api_interface] CustomerFilterParams: CustomerFilterParams includes field default_mandate_id.
  - [typescript_api_interface] CustomerCreatePayload: CustomerCreatePayload includes field default_mandate_id.
  - [typescript_api_interface] EmployeeListItem: EmployeeListItem includes field default_mandate_id.
  - [typescript_api_interface] EmployeeListFilters: EmployeeListFilters includes field default_mandate_id.
  - [backend_schema] Customer: Customer includes field default_mandate_id.
  - [backend_schema] CustomerFilter: CustomerFilter includes field default_mandate_id.

## customer.document_id

- canonical_name: document_id
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Dokument-ID
- labels_en: Document ID
- definition_de: Feld Dokument-ID im Kontext von Customer.
- definition_en: Document ID field used in the Customer context.
- related_fields: none
- aliases: document_id, customerAdmin.fields.documentId, historyAttachmentDraft.document_id, Dokument-ID, Document ID, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.documentId defines labels Document ID, Dokument-ID.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds historyAttachmentDraft.document_id next to customerAdmin.fields.documentId.
  - [typescript_api_interface] CustomerPortalDocumentRefRead: CustomerPortalDocumentRefRead includes field document_id.
  - [typescript_api_interface] CustomerHistoryAttachmentRead: CustomerHistoryAttachmentRead includes field document_id.
  - [typescript_api_interface] CustomerHistoryAttachmentLinkPayload: CustomerHistoryAttachmentLinkPayload includes field document_id.
  - [typescript_api_interface] CustomerExportResult: CustomerExportResult includes field document_id.
  - [typescript_api_interface] CustomerVCardResult: CustomerVCardResult includes field document_id.
  - [typescript_api_interface] EmployeeDocumentListItemRead: EmployeeDocumentListItemRead includes field document_id.

## customer.dunning_policy_code

- canonical_name: dunning_policy_code
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Mahnprofil
- labels_en: Dunning policy
- definition_de: Feld Mahnprofil im Kontext von Customer.
- definition_en: Dunning policy field used in the Customer context.
- related_fields: none
- aliases: dunning_policy_code, customerAdmin.fields.dunningPolicyCode, billingProfileDraft.dunning_policy_code, Mahnprofil, Dunning policy, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.dunningPolicyCode defines labels Dunning policy, Mahnprofil.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds billingProfileDraft.dunning_policy_code next to customerAdmin.fields.dunningPolicyCode.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field dunning_policy_code.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field dunning_policy_code.
  - [typescript_api_interface] PlanningCommercialLinkRead: PlanningCommercialLinkRead includes field dunning_policy_code.
  - [backend_schema] CustomerBillingProfile: CustomerBillingProfile includes field dunning_policy_code.
  - [backend_schema] CustomerBillingProfileCreate: CustomerBillingProfileCreate includes field dunning_policy_code.
  - [backend_schema] CustomerBillingProfileUpdate: CustomerBillingProfileUpdate includes field dunning_policy_code.

## customer.e_invoice_enabled

- canonical_name: e_invoice_enabled
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: checkbox
- required: unknown
- confidence: high
- labels_de: E-Rechnung aktiviert
- labels_en: E-invoicing enabled
- definition_de: Feld E-Rechnung aktiviert im Kontext von Customer.
- definition_en: E-invoicing enabled field used in the Customer context.
- related_fields: none
- aliases: e_invoice_enabled, customerAdmin.fields.eInvoiceEnabled, billingProfileDraft.tax_exempt, E-Rechnung aktiviert, E-invoicing enabled, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.eInvoiceEnabled defines labels E-Rechnung aktiviert, E-invoicing enabled.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds billingProfileDraft.tax_exempt next to customerAdmin.fields.eInvoiceEnabled.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field e_invoice_enabled.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field e_invoice_enabled.
  - [typescript_api_interface] FinanceBillingInvoiceRead: FinanceBillingInvoiceRead includes field e_invoice_enabled.
  - [typescript_api_interface] PlanningCommercialLinkRead: PlanningCommercialLinkRead includes field e_invoice_enabled.
  - [backend_schema] CustomerBillingProfile: CustomerBillingProfile includes field e_invoice_enabled.
  - [backend_schema] CustomerBillingProfileCreate: CustomerBillingProfileCreate includes field e_invoice_enabled.

## customer.effective_from

- canonical_name: effective_from
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Gültig ab
- labels_en: Effective from
- definition_de: Feld Gültig ab im Kontext von Customer.
- definition_en: Effective from field used in the Customer context.
- related_fields: none
- aliases: effective_from, customerAdmin.fields.effectiveFrom, rateCardDraft.effective_from, Gültig ab, Effective from, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.effectiveFrom defines labels Effective from, Gültig ab.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds rateCardDraft.effective_from next to customerAdmin.fields.effectiveFrom.
  - [typescript_api_interface] CustomerEmployeeBlockRead: CustomerEmployeeBlockRead includes field effective_from.
  - [typescript_api_interface] CustomerSurchargeRuleRead: CustomerSurchargeRuleRead includes field effective_from.
  - [typescript_api_interface] CustomerRateCardRead: CustomerRateCardRead includes field effective_from.
  - [typescript_api_interface] CustomerRateCardPayload: CustomerRateCardPayload includes field effective_from.
  - [typescript_api_interface] CustomerSurchargeRulePayload: CustomerSurchargeRulePayload includes field effective_from.
  - [typescript_api_interface] CustomerEmployeeBlockPayload: CustomerEmployeeBlockPayload includes field effective_from.

## customer.effective_to

- canonical_name: effective_to
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Gültig bis
- labels_en: Effective to
- definition_de: Feld Gültig bis im Kontext von Customer.
- definition_en: Effective to field used in the Customer context.
- related_fields: none
- aliases: effective_to, customerAdmin.fields.effectiveTo, rateCardDraft.effective_to, Gültig bis, Effective to, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.effectiveTo defines labels Effective to, Gültig bis.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds rateCardDraft.effective_to next to customerAdmin.fields.effectiveTo.
  - [typescript_api_interface] CustomerEmployeeBlockRead: CustomerEmployeeBlockRead includes field effective_to.
  - [typescript_api_interface] CustomerSurchargeRuleRead: CustomerSurchargeRuleRead includes field effective_to.
  - [typescript_api_interface] CustomerRateCardRead: CustomerRateCardRead includes field effective_to.
  - [typescript_api_interface] CustomerRateCardPayload: CustomerRateCardPayload includes field effective_to.
  - [typescript_api_interface] CustomerSurchargeRulePayload: CustomerSurchargeRulePayload includes field effective_to.
  - [typescript_api_interface] CustomerEmployeeBlockPayload: CustomerEmployeeBlockPayload includes field effective_to.

## customer.email

- canonical_name: email
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: SicherPlanCustomers
- form_contexts: customers.contacts_addresses_billing, customer_create, customer_scoped_order_create, customer_order_create, customer_plan_create
- input_type: input
- required: False
- confidence: high
- labels_de: E-Mail
- labels_en: Email
- definition_de: Feld E-Mail im Kontext von Customer.
- definition_en: Email field used in the Customer context.
- related_fields: none
- aliases: email, Email, E-Mail, customerAdmin.fields.email, contactDraft.email, Customer
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.contacts_addresses_billing includes field email labeled Email.
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.contacts_addresses_billing includes field email labeled E-Mail.
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.email defines labels E-Mail, Email.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds contactDraft.email next to customerAdmin.fields.email.
  - [typescript_api_interface] CustomerPortalAccessListItem: CustomerPortalAccessListItem includes field email.
  - [typescript_api_interface] CustomerPortalAccessCreatePayload: CustomerPortalAccessCreatePayload includes field email.
  - [typescript_api_interface] TenantAdminUserListItem: TenantAdminUserListItem includes field email.
  - [typescript_api_interface] TenantAdminUserCreatePayload: TenantAdminUserCreatePayload includes field email.

## customer.employee_id

- canonical_name: employee_id
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Mitarbeiter-ID
- labels_en: Employee ID
- definition_de: Feld Mitarbeiter-ID im Kontext von Customer.
- definition_en: Employee ID field used in the Customer context.
- related_fields: none
- aliases: employee_id, customerAdmin.fields.employeeId, employeeBlockDraft.employee_id, Mitarbeiter-ID, Employee ID, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.employeeId defines labels Employee ID, Mitarbeiter-ID.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds employeeBlockDraft.employee_id next to customerAdmin.fields.employeeId.
  - [typescript_api_interface] CustomerEmployeeBlockRead: CustomerEmployeeBlockRead includes field employee_id.
  - [typescript_api_interface] CustomerEmployeeBlockPayload: CustomerEmployeeBlockPayload includes field employee_id.
  - [typescript_api_interface] EmployeeGroupMembershipRead: EmployeeGroupMembershipRead includes field employee_id.
  - [typescript_api_interface] EmployeePrivateProfileRead: EmployeePrivateProfileRead includes field employee_id.
  - [typescript_api_interface] EmployeePrivateProfileWritePayload: EmployeePrivateProfileWritePayload includes field employee_id.
  - [typescript_api_interface] EmployeeAddressHistoryRead: EmployeeAddressHistoryRead includes field employee_id.

## customer.external_ref

- canonical_name: external_ref
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Externe Referenz
- labels_en: External reference
- definition_de: Feld Externe Referenz im Kontext von Customer.
- definition_en: External reference field used in the Customer context.
- related_fields: none
- aliases: external_ref, customerAdmin.fields.externalRef, customerDraft.external_ref, Externe Referenz, External reference, Customer, ارجاع خارجی
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.externalRef defines labels External reference, Externe Referenz.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds customerDraft.external_ref next to customerAdmin.fields.externalRef.
  - [typescript_api_interface] MandateRead: MandateRead includes field external_ref.
  - [typescript_api_interface] TenantOnboardingPayload: TenantOnboardingPayload includes field external_ref.
  - [typescript_api_interface] MandateCreatePayload: MandateCreatePayload includes field external_ref.
  - [typescript_api_interface] MandateUpdatePayload: MandateUpdatePayload includes field external_ref.
  - [typescript_api_interface] CustomerInvoicePartyRead: CustomerInvoicePartyRead includes field external_ref.
  - [typescript_api_interface] CustomerInvoicePartyPayload: CustomerInvoicePartyPayload includes field external_ref.

## customer.fixed_amount

- canonical_name: fixed_amount
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: number
- required: unknown
- confidence: high
- labels_de: Fixbetrag
- labels_en: Fixed amount
- definition_de: Feld Fixbetrag im Kontext von Customer.
- definition_en: Fixed amount field used in the Customer context.
- related_fields: none
- aliases: fixed_amount, customerAdmin.fields.fixedAmount, surchargeRuleDraft.fixed_amount, Fixbetrag, Fixed amount, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.fixedAmount defines labels Fixbetrag, Fixed amount.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds surchargeRuleDraft.fixed_amount next to customerAdmin.fields.fixedAmount.
  - [typescript_api_interface] CustomerSurchargeRuleRead: CustomerSurchargeRuleRead includes field fixed_amount.
  - [typescript_api_interface] CustomerSurchargeRulePayload: CustomerSurchargeRulePayload includes field fixed_amount.
  - [typescript_api_interface] PayrollSurchargeRuleRead: PayrollSurchargeRuleRead includes field fixed_amount.
  - [backend_schema] CustomerSurchargeRule: CustomerSurchargeRule includes field fixed_amount.
  - [backend_schema] CustomerSurchargeRuleCreate: CustomerSurchargeRuleCreate includes field fixed_amount.
  - [backend_schema] CustomerSurchargeRuleUpdate: CustomerSurchargeRuleUpdate includes field fixed_amount.

## customer.full_name

- canonical_name: full_name
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: SicherPlanCustomers
- form_contexts: customers.contacts_addresses_billing, customer_create, customer_scoped_order_create, customer_order_create, customer_plan_create
- input_type: input
- required: True
- confidence: high
- labels_de: Vollständiger Name
- labels_en: Full name
- definition_de: Feld Vollständiger Name im Kontext von Customer.
- definition_en: Full name field used in the Customer context.
- related_fields: none
- aliases: full_name, Full name, Vollständiger Name, customerAdmin.fields.fullName, contactDraft.full_name, Customer
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.contacts_addresses_billing includes field full_name labeled Full name.
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.contacts_addresses_billing includes field full_name labeled Vollständiger Name.
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.fullName defines labels Full name, Vollständiger Name.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds contactDraft.full_name next to customerAdmin.fields.fullName.
  - [typescript_api_interface] CustomerPortalAccessListItem: CustomerPortalAccessListItem includes field full_name.
  - [typescript_api_interface] CustomerPortalAccessCreatePayload: CustomerPortalAccessCreatePayload includes field full_name.
  - [typescript_api_interface] TenantAdminUserListItem: TenantAdminUserListItem includes field full_name.
  - [typescript_api_interface] TenantAdminUserCreatePayload: TenantAdminUserCreatePayload includes field full_name.

## customer.function_label

- canonical_name: function_label
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Funktion
- labels_en: Function
- definition_de: Feld Funktion im Kontext von Customer.
- definition_en: Function field used in the Customer context.
- related_fields: none
- aliases: function_label, customerAdmin.fields.functionLabel, contactDraft.function_label, Funktion, Function, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.functionLabel defines labels Function, Funktion.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds contactDraft.function_label next to customerAdmin.fields.functionLabel.
  - [typescript_api_interface] CustomerPortalContextRead: CustomerPortalContextRead includes field function_label.
  - [typescript_api_interface] SubcontractorPortalContextRead: SubcontractorPortalContextRead includes field function_label.
  - [typescript_api_interface] CustomerContactRead: CustomerContactRead includes field function_label.
  - [typescript_api_interface] CustomerContactPayload: CustomerContactPayload includes field function_label.
  - [typescript_api_interface] SubcontractorContactRead: SubcontractorContactRead includes field function_label.
  - [backend_schema] CustomerContact: CustomerContact includes field function_label.

## customer.function_type_id

- canonical_name: function_type_id
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Funktions-ID
- labels_en: Function ID
- definition_de: Feld Funktions-ID im Kontext von Customer.
- definition_en: Function ID field used in the Customer context.
- related_fields: none
- aliases: function_type_id, customerAdmin.fields.functionTypeId, rateLineDraft.function_type_id, Funktions-ID, Function ID, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.functionTypeId defines labels Function ID, Funktions-ID.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds rateLineDraft.function_type_id next to customerAdmin.fields.functionTypeId.
  - [typescript_api_interface] CustomerRateLineRead: CustomerRateLineRead includes field function_type_id.
  - [typescript_api_interface] CustomerRateLinePayload: CustomerRateLinePayload includes field function_type_id.
  - [typescript_api_interface] EmployeeQualificationRead: EmployeeQualificationRead includes field function_type_id.
  - [typescript_api_interface] EmployeeQualificationCreatePayload: EmployeeQualificationCreatePayload includes field function_type_id.
  - [typescript_api_interface] EmployeeQualificationUpdatePayload: EmployeeQualificationUpdatePayload includes field function_type_id.
  - [typescript_api_interface] PayrollTariffRateRead: PayrollTariffRateRead includes field function_type_id.

## customer.history_entry

- canonical_name: history_entry
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: medium
- labels_de: Historieneintrag
- labels_en: History entry
- definition_de: Feld Historieneintrag im Kontext von Customer.
- definition_en: History entry field used in the Customer context.
- related_fields: none
- aliases: history_entry, customerAdmin.fields.historyEntry, historyAttachmentDraft.history_entry_id, Historieneintrag, History entry, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.historyEntry defines labels Historieneintrag, History entry.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds historyAttachmentDraft.history_entry_id next to customerAdmin.fields.historyEntry.

## customer.invoice_email

- canonical_name: invoice_email
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: SicherPlanCustomers
- form_contexts: customers.contacts_addresses_billing, customer_create, customer_scoped_order_create, customer_order_create, customer_plan_create
- input_type: input
- required: False
- confidence: high
- labels_de: Rechnungs-E-Mail
- labels_en: Invoice email
- definition_de: Feld Rechnungs-E-Mail im Kontext von Customer.
- definition_en: Invoice email field used in the Customer context.
- related_fields: none
- aliases: invoice_email, Invoice email, Rechnungs-E-Mail, customerAdmin.fields.invoiceEmail, billingProfileDraft.invoice_email, Customer
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.contacts_addresses_billing includes field invoice_email labeled Invoice email.
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.contacts_addresses_billing includes field invoice_email labeled Rechnungs-E-Mail.
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.invoiceEmail defines labels Invoice email, Rechnungs-E-Mail.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds billingProfileDraft.invoice_email next to customerAdmin.fields.invoiceEmail.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field invoice_email.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field invoice_email.
  - [typescript_api_interface] CustomerInvoicePartyRead: CustomerInvoicePartyRead includes field invoice_email.
  - [typescript_api_interface] CustomerInvoicePartyPayload: CustomerInvoicePartyPayload includes field invoice_email.

## customer.invoice_layout_code

- canonical_name: invoice_layout_code
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Rechnungslayout
- labels_en: Invoice layout
- definition_de: Feld Rechnungslayout im Kontext von Customer.
- definition_en: Invoice layout field used in the Customer context.
- related_fields: none
- aliases: invoice_layout_code, customerAdmin.fields.invoiceLayoutCode, billingProfileDraft.invoice_layout_code, Rechnungslayout, Invoice layout, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.invoiceLayoutCode defines labels Invoice layout, Rechnungslayout.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds billingProfileDraft.invoice_layout_code next to customerAdmin.fields.invoiceLayoutCode.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field invoice_layout_code.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field invoice_layout_code.
  - [typescript_api_interface] PlanningCommercialLinkRead: PlanningCommercialLinkRead includes field invoice_layout_code.
  - [backend_schema] CustomerBillingProfile: CustomerBillingProfile includes field invoice_layout_code.
  - [backend_schema] CustomerBillingProfileCreate: CustomerBillingProfileCreate includes field invoice_layout_code.
  - [backend_schema] CustomerBillingProfileUpdate: CustomerBillingProfileUpdate includes field invoice_layout_code.

## customer.invoice_layout_lookup_id

- canonical_name: invoice_layout_lookup_id
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Rechnungslayout
- labels_en: Invoice layout
- definition_de: Feld Rechnungslayout im Kontext von Customer.
- definition_en: Invoice layout field used in the Customer context.
- related_fields: none
- aliases: invoice_layout_lookup_id, customerAdmin.fields.invoiceLayoutLookupId, invoicePartyDraft.invoice_layout_lookup_id, Rechnungslayout, Invoice layout, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.invoiceLayoutLookupId defines labels Invoice layout, Rechnungslayout.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds invoicePartyDraft.invoice_layout_lookup_id next to customerAdmin.fields.invoiceLayoutLookupId.
  - [typescript_api_interface] CustomerInvoicePartyRead: CustomerInvoicePartyRead includes field invoice_layout_lookup_id.
  - [typescript_api_interface] CustomerInvoicePartyPayload: CustomerInvoicePartyPayload includes field invoice_layout_lookup_id.
  - [backend_schema] CustomerInvoiceParty: CustomerInvoiceParty includes field invoice_layout_lookup_id.
  - [backend_schema] CustomerInvoicePartyCreate: CustomerInvoicePartyCreate includes field invoice_layout_lookup_id.
  - [backend_schema] CustomerInvoicePartyUpdate: CustomerInvoicePartyUpdate includes field invoice_layout_lookup_id.
  - [backend_schema] CustomerInvoicePartyListItem: CustomerInvoicePartyListItem includes field invoice_layout_lookup_id.

## customer.is_billing_contact

- canonical_name: is_billing_contact
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: unknown
- required: unknown
- confidence: medium
- labels_de: Als Rechnungskontakt markieren
- labels_en: Mark as billing contact
- definition_de: Feld Als Rechnungskontakt markieren im Kontext von Customer.
- definition_en: Mark as billing contact field used in the Customer context.
- related_fields: none
- aliases: is_billing_contact, customerAdmin.fields.isBillingContact, Als Rechnungskontakt markieren, Mark as billing contact, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.isBillingContact defines labels Als Rechnungskontakt markieren, Mark as billing contact.
  - [typescript_api_interface] CustomerContactRead: CustomerContactRead includes field is_billing_contact.
  - [typescript_api_interface] CustomerContactPayload: CustomerContactPayload includes field is_billing_contact.
  - [backend_schema] CustomerContact: CustomerContact includes field is_billing_contact.
  - [backend_schema] CustomerContactCreate: CustomerContactCreate includes field is_billing_contact.
  - [backend_schema] CustomerContactUpdate: CustomerContactUpdate includes field is_billing_contact.
  - [backend_schema] CustomerContactListItem: CustomerContactListItem includes field is_billing_contact.

## customer.is_default

- canonical_name: is_default
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: unknown
- required: unknown
- confidence: medium
- labels_de: Als Standardadresse markieren
- labels_en: Mark as default address
- definition_de: Feld Als Standardadresse markieren im Kontext von Customer.
- definition_en: Mark as default address field used in the Customer context.
- related_fields: none
- aliases: is_default, customerAdmin.fields.isDefault, Als Standardadresse markieren, Mark as default address, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.isDefault defines labels Als Standardadresse markieren, Mark as default address.
  - [typescript_api_interface] CustomerAddressRead: CustomerAddressRead includes field is_default.
  - [typescript_api_interface] CustomerInvoicePartyRead: CustomerInvoicePartyRead includes field is_default.
  - [typescript_api_interface] CustomerInvoicePartyPayload: CustomerInvoicePartyPayload includes field is_default.
  - [typescript_api_interface] CustomerAddressPayload: CustomerAddressPayload includes field is_default.
  - [backend_schema] CustomerInvoiceParty: CustomerInvoiceParty includes field is_default.
  - [backend_schema] CustomerAddressLink: CustomerAddressLink includes field is_default.
  - [backend_schema] CustomerAddressCreate: CustomerAddressCreate includes field is_default.

## customer.is_default_invoice_party

- canonical_name: is_default_invoice_party
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: unknown
- required: unknown
- confidence: low
- labels_de: Als Standard-Rechnungspartei markieren
- labels_en: Mark as default invoice party
- definition_de: Feld Als Standard-Rechnungspartei markieren im Kontext von Customer.
- definition_en: Mark as default invoice party field used in the Customer context.
- related_fields: none
- aliases: is_default_invoice_party, customerAdmin.fields.isDefaultInvoiceParty, Als Standard-Rechnungspartei markieren, Mark as default invoice party, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.isDefaultInvoiceParty defines labels Als Standard-Rechnungspartei markieren, Mark as default invoice party.

## customer.is_primary_contact

- canonical_name: is_primary_contact
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: checkbox
- required: unknown
- confidence: high
- labels_de: Als Primärkontakt markieren
- labels_en: Mark as primary contact
- definition_de: Feld Als Primärkontakt markieren im Kontext von Customer.
- definition_en: Mark as primary contact field used in the Customer context.
- related_fields: none
- aliases: is_primary_contact, customerAdmin.fields.isPrimaryContact, contactDraft.is_billing_contact, Als Primärkontakt markieren, Mark as primary contact, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.isPrimaryContact defines labels Als Primärkontakt markieren, Mark as primary contact.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds contactDraft.is_billing_contact next to customerAdmin.fields.isPrimaryContact.
  - [typescript_api_interface] CustomerContactRead: CustomerContactRead includes field is_primary_contact.
  - [typescript_api_interface] CustomerContactPayload: CustomerContactPayload includes field is_primary_contact.
  - [typescript_api_interface] SubcontractorContactRead: SubcontractorContactRead includes field is_primary_contact.
  - [backend_schema] CustomerContact: CustomerContact includes field is_primary_contact.
  - [backend_schema] CustomerContactCreate: CustomerContactCreate includes field is_primary_contact.
  - [backend_schema] CustomerContactUpdate: CustomerContactUpdate includes field is_primary_contact.

## customer.label

- canonical_name: label
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Bezeichnung
- labels_en: Label
- definition_de: Feld Bezeichnung im Kontext von Customer.
- definition_en: Label field used in the Customer context.
- related_fields: none
- aliases: label, customerAdmin.fields.label, addressDraft.label, Bezeichnung, Label, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.label defines labels Bezeichnung, Label.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds addressDraft.label next to customerAdmin.fields.label.
  - [typescript_api_interface] AssistantLink: AssistantLink includes field label.
  - [typescript_api_interface] AssistantPageHelpField: AssistantPageHelpField includes field label.
  - [typescript_api_interface] AssistantPageHelpAction: AssistantPageHelpAction includes field label.
  - [typescript_api_interface] LookupValueRead: LookupValueRead includes field label.
  - [typescript_api_interface] LookupValueCreatePayload: LookupValueCreatePayload includes field label.
  - [typescript_api_interface] LookupValueUpdatePayload: LookupValueUpdatePayload includes field label.

## customer.legal_form_lookup_id

- canonical_name: legal_form_lookup_id
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Rechtsform
- labels_en: Legal form
- definition_de: Feld Rechtsform im Kontext von Customer.
- definition_en: Legal form field used in the Customer context.
- related_fields: none
- aliases: legal_form_lookup_id, customerAdmin.fields.legalFormLookupId, customerDraft.legal_form_lookup_id, Rechtsform, Legal form, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.legalFormLookupId defines labels Legal form, Rechtsform.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds customerDraft.legal_form_lookup_id next to customerAdmin.fields.legalFormLookupId.
  - [typescript_api_interface] CustomerCreatePayload: CustomerCreatePayload includes field legal_form_lookup_id.
  - [backend_schema] Customer: Customer includes field legal_form_lookup_id.
  - [backend_schema] CustomerCreate: CustomerCreate includes field legal_form_lookup_id.
  - [backend_schema] CustomerUpdate: CustomerUpdate includes field legal_form_lookup_id.
  - [backend_schema] CustomerRead: CustomerRead includes field legal_form_lookup_id.
  - [backend_schema] Subcontractor: Subcontractor includes field legal_form_lookup_id.

## customer.legal_name

- canonical_name: legal_name
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: SicherPlanCustomers
- form_contexts: customers.master_profile, customer_create, customer_scoped_order_create, customer_order_create, customer_plan_create
- input_type: input
- required: False
- confidence: high
- labels_de: Rechtlicher Name
- labels_en: Legal name
- definition_de: Offizieller rechtlicher Name des Kunden oder der juristischen Einheit, der in Verträgen, Rechnungen und offiziellen Dokumenten verwendet wird.
- definition_en: Official legal name of the customer or legal entity used for contracts, invoices, and formal documents.
- related_fields: customer.name, customer.customer_number, customer.external_ref
- aliases: legal_name, Legal name, Rechtlicher Name, customerAdmin.fields.legalName, customerDraft.legal_name, Customer, نام قانونی
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.master_profile includes field legal_name labeled Legal name.
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.master_profile includes field legal_name labeled Rechtlicher Name.
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.legalName defines labels Legal name, Rechtlicher Name.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds customerDraft.legal_name next to customerAdmin.fields.legalName.
  - [typescript_api_interface] SubcontractorPortalContextRead: SubcontractorPortalContextRead includes field legal_name.
  - [typescript_api_interface] TenantOnboardingPayload: TenantOnboardingPayload includes field legal_name.
  - [typescript_api_interface] TenantUpdatePayload: TenantUpdatePayload includes field legal_name.
  - [typescript_api_interface] CustomerCreatePayload: CustomerCreatePayload includes field legal_name.

## customer.leitweg_id

- canonical_name: leitweg_id
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Leitweg-/Routing-ID
- labels_en: Leitweg/routing ID
- definition_de: Feld Leitweg-/Routing-ID im Kontext von Customer.
- definition_en: Leitweg/routing ID field used in the Customer context.
- related_fields: none
- aliases: leitweg_id, customerAdmin.fields.leitwegId, billingProfileDraft.leitweg_id, Leitweg-/Routing-ID, Leitweg/routing ID, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.leitwegId defines labels Leitweg-/Routing-ID, Leitweg/routing ID.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds billingProfileDraft.leitweg_id next to customerAdmin.fields.leitwegId.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field leitweg_id.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field leitweg_id.
  - [typescript_api_interface] FinanceBillingInvoiceRead: FinanceBillingInvoiceRead includes field leitweg_id.
  - [backend_schema] CustomerBillingProfile: CustomerBillingProfile includes field leitweg_id.
  - [backend_schema] CustomerBillingProfileCreate: CustomerBillingProfileCreate includes field leitweg_id.
  - [backend_schema] CustomerBillingProfileUpdate: CustomerBillingProfileUpdate includes field leitweg_id.

## customer.lifecycle_status

- canonical_name: lifecycle_status
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: SicherPlanCustomers
- form_contexts: customers.list_and_search, customer_create, customer_scoped_order_create, customer_order_create, customer_plan_create
- input_type: input
- required: False
- confidence: high
- labels_de: Lifecycle-Status
- labels_en: Lifecycle status
- definition_de: Feld Lifecycle-Status im Kontext von Customer.
- definition_en: Lifecycle status field used in the Customer context.
- related_fields: none
- aliases: lifecycle_status, Lifecycle status, Lifecycle-Status, customerAdmin.fields.lifecycleStatus, customerDraft.status, Customer
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.list_and_search includes field lifecycle_status labeled Lifecycle status.
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.list_and_search includes field lifecycle_status labeled Lifecycle-Status.
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.lifecycleStatus defines labels Lifecycle status, Lifecycle-Status.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds customerDraft.status next to customerAdmin.fields.lifecycleStatus.
  - [typescript_api_interface] CustomerFilterParams: CustomerFilterParams includes field lifecycle_status.
  - [typescript_api_interface] CustomerOrderListFilters: CustomerOrderListFilters includes field lifecycle_status.
  - [typescript_api_interface] PlanningRecordListFilters: PlanningRecordListFilters includes field lifecycle_status.
  - [typescript_api_interface] SubcontractorListFilters: SubcontractorListFilters includes field lifecycle_status.

## customer.line_kind

- canonical_name: line_kind
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Zeilenart
- labels_en: Line kind
- definition_de: Feld Zeilenart im Kontext von Customer.
- definition_en: Line kind field used in the Customer context.
- related_fields: none
- aliases: line_kind, customerAdmin.fields.lineKind, rateLineDraft.line_kind, Zeilenart, Line kind, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.lineKind defines labels Line kind, Zeilenart.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds rateLineDraft.line_kind next to customerAdmin.fields.lineKind.
  - [typescript_api_interface] CustomerRateLineRead: CustomerRateLineRead includes field line_kind.
  - [typescript_api_interface] CustomerRateLinePayload: CustomerRateLinePayload includes field line_kind.
  - [backend_schema] CustomerRateLine: CustomerRateLine includes field line_kind.
  - [backend_schema] CustomerRateLineCreate: CustomerRateLineCreate includes field line_kind.
  - [backend_schema] CustomerRateLineUpdate: CustomerRateLineUpdate includes field line_kind.
  - [backend_schema] CustomerRateLineRead: CustomerRateLineRead includes field line_kind.

## customer.locale

- canonical_name: locale
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Sprache
- labels_en: Locale
- definition_de: Feld Sprache im Kontext von Customer.
- definition_en: Locale field used in the Customer context.
- related_fields: none
- aliases: locale, customerAdmin.fields.locale, portalAccessDraft.locale, Sprache, Locale, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.locale defines labels Locale, Sprache.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds portalAccessDraft.locale next to customerAdmin.fields.locale.
  - [typescript_api_interface] AssistantConversation: AssistantConversation includes field locale.
  - [typescript_api_interface] CustomerPortalAccessListItem: CustomerPortalAccessListItem includes field locale.
  - [typescript_api_interface] CustomerPortalAccessCreatePayload: CustomerPortalAccessCreatePayload includes field locale.
  - [typescript_api_interface] TenantAdminUserListItem: TenantAdminUserListItem includes field locale.
  - [typescript_api_interface] TenantAdminUserCreatePayload: TenantAdminUserCreatePayload includes field locale.
  - [typescript_api_interface] AuthenticatedUser: AuthenticatedUser includes field locale.

## customer.minimum_quantity

- canonical_name: minimum_quantity
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: number
- required: unknown
- confidence: high
- labels_de: Mindestmenge
- labels_en: Minimum quantity
- definition_de: Feld Mindestmenge im Kontext von Customer.
- definition_en: Minimum quantity field used in the Customer context.
- related_fields: none
- aliases: minimum_quantity, customerAdmin.fields.minimumQuantity, rateLineDraft.minimum_quantity, Mindestmenge, Minimum quantity, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.minimumQuantity defines labels Mindestmenge, Minimum quantity.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds rateLineDraft.minimum_quantity next to customerAdmin.fields.minimumQuantity.
  - [typescript_api_interface] CustomerRateLineRead: CustomerRateLineRead includes field minimum_quantity.
  - [typescript_api_interface] CustomerRateLinePayload: CustomerRateLinePayload includes field minimum_quantity.
  - [backend_schema] CustomerRateLine: CustomerRateLine includes field minimum_quantity.
  - [backend_schema] CustomerRateLineCreate: CustomerRateLineCreate includes field minimum_quantity.
  - [backend_schema] CustomerRateLineUpdate: CustomerRateLineUpdate includes field minimum_quantity.
  - [backend_schema] CustomerRateLineRead: CustomerRateLineRead includes field minimum_quantity.

## customer.mobile

- canonical_name: mobile
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: textarea
- required: unknown
- confidence: high
- labels_de: Mobil
- labels_en: Mobile
- definition_de: Feld Mobil im Kontext von Customer.
- definition_en: Mobile field used in the Customer context.
- related_fields: none
- aliases: mobile, customerAdmin.fields.mobile, contactDraft.mobile, Mobil, Mobile, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.mobile defines labels Mobil, Mobile.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds contactDraft.mobile next to customerAdmin.fields.mobile.
  - [typescript_api_interface] CustomerPortalContextRead: CustomerPortalContextRead includes field mobile.
  - [typescript_api_interface] SubcontractorPortalContextRead: SubcontractorPortalContextRead includes field mobile.
  - [typescript_api_interface] CustomerContactRead: CustomerContactRead includes field mobile.
  - [typescript_api_interface] CustomerContactPayload: CustomerContactPayload includes field mobile.
  - [typescript_api_interface] SubcontractorWorkerListItem: SubcontractorWorkerListItem includes field mobile.
  - [typescript_api_interface] SubcontractorPortalWorkerCreate: SubcontractorPortalWorkerCreate includes field mobile.

## customer.name

- canonical_name: name
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: SicherPlanCustomers
- form_contexts: customers.master_profile, customer_create, customer_scoped_order_create, customer_order_create, customer_plan_create
- input_type: input
- required: True
- confidence: high
- labels_de: Anzeigename
- labels_en: Display name
- definition_de: Feld Anzeigename im Kontext von Customer.
- definition_en: Display name field used in the Customer context.
- related_fields: none
- aliases: name, Display name, Anzeigename, customerAdmin.fields.name, customerDraft.name, Customer
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.master_profile includes field name labeled Display name.
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.master_profile includes field name labeled Anzeigename.
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.name defines labels Anzeigename, Display name.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds customerDraft.name next to customerAdmin.fields.name.
  - [typescript_api_interface] TenantListItem: TenantListItem includes field name.
  - [typescript_api_interface] CustomerPortalContextRead: CustomerPortalContextRead includes field name.
  - [typescript_api_interface] BranchRead: BranchRead includes field name.
  - [typescript_api_interface] MandateRead: MandateRead includes field name.

## customer.note

- canonical_name: note
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: textarea
- required: unknown
- confidence: high
- labels_de: Hinweis
- labels_en: Note
- definition_de: Feld Hinweis im Kontext von Customer.
- definition_en: Note field used in the Customer context.
- related_fields: none
- aliases: note, customerAdmin.fields.note, invoicePartyDraft.note, Hinweis, Note, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.note defines labels Hinweis, Note.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds invoicePartyDraft.note next to customerAdmin.fields.note.
  - [typescript_api_interface] CustomerInvoicePartyRead: CustomerInvoicePartyRead includes field note.
  - [typescript_api_interface] CustomerInvoicePartyPayload: CustomerInvoicePartyPayload includes field note.
  - [typescript_api_interface] ApplicantActivityEventRead: ApplicantActivityEventRead includes field note.
  - [typescript_api_interface] ApplicantTransitionPayload: ApplicantTransitionPayload includes field note.
  - [typescript_api_interface] ApplicantActivityPayload: ApplicantActivityPayload includes field note.
  - [backend_schema] CustomerInvoiceParty: CustomerInvoiceParty includes field note.

## customer.notes

- canonical_name: notes
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: textarea
- required: unknown
- confidence: high
- labels_de: Notizen
- labels_en: Notes
- definition_de: Feld Notizen im Kontext von Customer.
- definition_en: Notes field used in the Customer context.
- related_fields: none
- aliases: notes, customerAdmin.fields.notes, customerDraft.notes, Notizen, Notes, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.notes defines labels Notes, Notizen.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds customerDraft.notes next to customerAdmin.fields.notes.
  - [typescript_api_interface] MandateRead: MandateRead includes field notes.
  - [typescript_api_interface] TenantOnboardingPayload: TenantOnboardingPayload includes field notes.
  - [typescript_api_interface] MandateCreatePayload: MandateCreatePayload includes field notes.
  - [typescript_api_interface] MandateUpdatePayload: MandateUpdatePayload includes field notes.
  - [typescript_api_interface] CustomerContactRead: CustomerContactRead includes field notes.
  - [typescript_api_interface] CustomerRateLineRead: CustomerRateLineRead includes field notes.

## customer.payment_terms_days

- canonical_name: payment_terms_days
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: SicherPlanCustomers
- form_contexts: customers.contacts_addresses_billing, customer_create, customer_scoped_order_create, customer_order_create, customer_plan_create
- input_type: input
- required: False
- confidence: high
- labels_de: Zahlungsziel in Tagen
- labels_en: Payment terms days, Payment terms in days
- definition_de: Feld Zahlungsziel in Tagen im Kontext von Customer.
- definition_en: Payment terms days field used in the Customer context.
- related_fields: none
- aliases: payment_terms_days, Payment terms days, Zahlungsziel in Tagen, customerAdmin.fields.paymentTermsDays, billingProfileDraft.payment_terms_days, Payment terms in days, Customer
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.contacts_addresses_billing includes field payment_terms_days labeled Payment terms days.
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.contacts_addresses_billing includes field payment_terms_days labeled Zahlungsziel in Tagen.
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.paymentTermsDays defines labels Payment terms in days, Zahlungsziel in Tagen.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds billingProfileDraft.payment_terms_days next to customerAdmin.fields.paymentTermsDays.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field payment_terms_days.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field payment_terms_days.
  - [typescript_api_interface] FinanceBillingInvoiceRead: FinanceBillingInvoiceRead includes field payment_terms_days.
  - [typescript_api_interface] SubcontractorFinanceProfileRead: SubcontractorFinanceProfileRead includes field payment_terms_days.

## customer.payment_terms_note

- canonical_name: payment_terms_note
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Zahlungsbedingung
- labels_en: Payment note
- definition_de: Feld Zahlungsbedingung im Kontext von Customer.
- definition_en: Payment note field used in the Customer context.
- related_fields: none
- aliases: payment_terms_note, customerAdmin.fields.paymentTermsNote, billingProfileDraft.payment_terms_note, Zahlungsbedingung, Payment note, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.paymentTermsNote defines labels Payment note, Zahlungsbedingung.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds billingProfileDraft.payment_terms_note next to customerAdmin.fields.paymentTermsNote.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field payment_terms_note.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field payment_terms_note.
  - [typescript_api_interface] SubcontractorFinanceProfileRead: SubcontractorFinanceProfileRead includes field payment_terms_note.
  - [backend_schema] CustomerBillingProfile: CustomerBillingProfile includes field payment_terms_note.
  - [backend_schema] CustomerBillingProfileCreate: CustomerBillingProfileCreate includes field payment_terms_note.
  - [backend_schema] CustomerBillingProfileUpdate: CustomerBillingProfileUpdate includes field payment_terms_note.

## customer.percent_value

- canonical_name: percent_value
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: number
- required: unknown
- confidence: high
- labels_de: Prozentwert
- labels_en: Percent value
- definition_de: Feld Prozentwert im Kontext von Customer.
- definition_en: Percent value field used in the Customer context.
- related_fields: none
- aliases: percent_value, customerAdmin.fields.percentValue, surchargeRuleDraft.percent_value, Prozentwert, Percent value, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.percentValue defines labels Percent value, Prozentwert.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds surchargeRuleDraft.percent_value next to customerAdmin.fields.percentValue.
  - [typescript_api_interface] CustomerSurchargeRuleRead: CustomerSurchargeRuleRead includes field percent_value.
  - [typescript_api_interface] CustomerSurchargeRulePayload: CustomerSurchargeRulePayload includes field percent_value.
  - [typescript_api_interface] PayrollSurchargeRuleRead: PayrollSurchargeRuleRead includes field percent_value.
  - [backend_schema] CustomerSurchargeRule: CustomerSurchargeRule includes field percent_value.
  - [backend_schema] CustomerSurchargeRuleCreate: CustomerSurchargeRuleCreate includes field percent_value.
  - [backend_schema] CustomerSurchargeRuleUpdate: CustomerSurchargeRuleUpdate includes field percent_value.

## customer.person_names_released

- canonical_name: person_names_released
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: unknown
- required: unknown
- confidence: medium
- labels_de: Personennamen im Portal freigeben
- labels_en: Release personal names in portal
- definition_de: Feld Personennamen im Portal freigeben im Kontext von Customer.
- definition_en: Release personal names in portal field used in the Customer context.
- related_fields: none
- aliases: person_names_released, customerAdmin.fields.personNamesReleased, Personennamen im Portal freigeben, Release personal names in portal, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.personNamesReleased defines labels Personennamen im Portal freigeben, Release personal names in portal.
  - [typescript_api_interface] CustomerPortalPrivacyRead: CustomerPortalPrivacyRead includes field person_names_released.
  - [typescript_api_interface] CustomerPortalPrivacyUpdatePayload: CustomerPortalPrivacyUpdatePayload includes field person_names_released.
  - [backend_schema] CustomerPortalPrivacyRead: CustomerPortalPrivacyRead includes field person_names_released.
  - [backend_schema] CustomerPortalPrivacyUpdate: CustomerPortalPrivacyUpdate includes field person_names_released.

## customer.phone

- canonical_name: phone
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: SicherPlanCustomers
- form_contexts: customers.contacts_addresses_billing, customer_create, customer_scoped_order_create, customer_order_create, customer_plan_create
- input_type: input
- required: False
- confidence: high
- labels_de: Telefon
- labels_en: Phone
- definition_de: Feld Telefon im Kontext von Customer.
- definition_en: Phone field used in the Customer context.
- related_fields: none
- aliases: phone, Phone, Telefon, customerAdmin.fields.phone, contactDraft.phone, Customer
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.contacts_addresses_billing includes field phone labeled Phone.
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.contacts_addresses_billing includes field phone labeled Telefon.
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.phone defines labels Phone, Telefon.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds contactDraft.phone next to customerAdmin.fields.phone.
  - [typescript_api_interface] CustomerPortalContextRead: CustomerPortalContextRead includes field phone.
  - [typescript_api_interface] SubcontractorPortalContextRead: SubcontractorPortalContextRead includes field phone.
  - [typescript_api_interface] CustomerContactRead: CustomerContactRead includes field phone.
  - [typescript_api_interface] CustomerContactPayload: CustomerContactPayload includes field phone.

## customer.planning_mode_code

- canonical_name: planning_mode_code
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Planungsmodus
- labels_en: Planning mode
- definition_de: Feld Planungsmodus im Kontext von Customer.
- definition_en: Planning mode field used in the Customer context.
- related_fields: none
- aliases: planning_mode_code, customerAdmin.fields.planningModeCode, rateLineDraft.planning_mode_code, Planungsmodus, Planning mode, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.planningModeCode defines labels Planning mode, Planungsmodus.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds rateLineDraft.planning_mode_code next to customerAdmin.fields.planningModeCode.
  - [typescript_api_interface] CustomerDashboardPlanItemRead: CustomerDashboardPlanItemRead includes field planning_mode_code.
  - [typescript_api_interface] CustomerRateLineRead: CustomerRateLineRead includes field planning_mode_code.
  - [typescript_api_interface] CustomerRateLinePayload: CustomerRateLinePayload includes field planning_mode_code.
  - [typescript_api_interface] FinanceBillingTimesheetLineRead: FinanceBillingTimesheetLineRead includes field planning_mode_code.
  - [typescript_api_interface] PlanningRecordListItem: PlanningRecordListItem includes field planning_mode_code.
  - [typescript_api_interface] PlanningRecordListFilters: PlanningRecordListFilters includes field planning_mode_code.

## customer.postal_code

- canonical_name: postal_code
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Postleitzahl
- labels_en: Postal code
- definition_de: Feld Postleitzahl im Kontext von Customer.
- definition_en: Postal code field used in the Customer context.
- related_fields: none
- aliases: postal_code, customerAdmin.fields.postalCode, addressDirectoryDraft.postal_code, Postleitzahl, Postal code, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.postalCode defines labels Postal code, Postleitzahl.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds addressDirectoryDraft.postal_code next to customerAdmin.fields.postalCode.
  - [typescript_api_interface] CustomerAddressRead: CustomerAddressRead includes field postal_code.
  - [typescript_api_interface] CustomerAvailableAddressRead: CustomerAvailableAddressRead includes field postal_code.
  - [typescript_api_interface] CustomerAvailableAddressCreatePayload: CustomerAvailableAddressCreatePayload includes field postal_code.
  - [typescript_api_interface] EmployeeAddressHistoryRead: EmployeeAddressHistoryRead includes field postal_code.
  - [typescript_api_interface] EmployeeAddressWriteAddressInput: EmployeeAddressWriteAddressInput includes field postal_code.
  - [backend_schema] Address: Address includes field postal_code.

## customer.qualification_type_id

- canonical_name: qualification_type_id
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Qualifikations-ID
- labels_en: Qualification ID
- definition_de: Feld Qualifikations-ID im Kontext von Customer.
- definition_en: Qualification ID field used in the Customer context.
- related_fields: none
- aliases: qualification_type_id, customerAdmin.fields.qualificationTypeId, rateLineDraft.qualification_type_id, Qualifikations-ID, Qualification ID, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.qualificationTypeId defines labels Qualification ID, Qualifikations-ID.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds rateLineDraft.qualification_type_id next to customerAdmin.fields.qualificationTypeId.
  - [typescript_api_interface] CustomerRateLineRead: CustomerRateLineRead includes field qualification_type_id.
  - [typescript_api_interface] CustomerRateLinePayload: CustomerRateLinePayload includes field qualification_type_id.
  - [typescript_api_interface] EmployeeQualificationRead: EmployeeQualificationRead includes field qualification_type_id.
  - [typescript_api_interface] EmployeeQualificationCreatePayload: EmployeeQualificationCreatePayload includes field qualification_type_id.
  - [typescript_api_interface] EmployeeQualificationUpdatePayload: EmployeeQualificationUpdatePayload includes field qualification_type_id.
  - [typescript_api_interface] PayrollTariffRateRead: PayrollTariffRateRead includes field qualification_type_id.

## customer.ranking_lookup_id

- canonical_name: ranking_lookup_id
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: SicherPlanCustomers
- form_contexts: customers.master_profile, customer_create, customer_scoped_order_create, customer_order_create, customer_plan_create
- input_type: input
- required: False
- confidence: high
- labels_de: Ranking
- labels_en: Ranking
- definition_de: Feld Ranking im Kontext von Customer.
- definition_en: Ranking field used in the Customer context.
- related_fields: none
- aliases: ranking_lookup_id, Ranking, customerAdmin.fields.rankingLookupId, customerDraft.ranking_lookup_id, Customer
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.master_profile includes field ranking_lookup_id labeled Ranking.
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.master_profile includes field ranking_lookup_id labeled Ranking.
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.rankingLookupId defines labels Ranking, Ranking.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds customerDraft.ranking_lookup_id next to customerAdmin.fields.rankingLookupId.
  - [typescript_api_interface] CustomerCreatePayload: CustomerCreatePayload includes field ranking_lookup_id.
  - [backend_schema] Customer: Customer includes field ranking_lookup_id.
  - [backend_schema] CustomerCreate: CustomerCreate includes field ranking_lookup_id.
  - [backend_schema] CustomerUpdate: CustomerUpdate includes field ranking_lookup_id.

## customer.rate_kind

- canonical_name: rate_kind
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Preisart
- labels_en: Rate kind
- definition_de: Feld Preisart im Kontext von Customer.
- definition_en: Rate kind field used in the Customer context.
- related_fields: none
- aliases: rate_kind, customerAdmin.fields.rateKind, rateCardDraft.rate_kind, Preisart, Rate kind, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.rateKind defines labels Preisart, Rate kind.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds rateCardDraft.rate_kind next to customerAdmin.fields.rateKind.
  - [typescript_api_interface] CustomerRateCardRead: CustomerRateCardRead includes field rate_kind.
  - [typescript_api_interface] CustomerRateCardPayload: CustomerRateCardPayload includes field rate_kind.
  - [backend_schema] CustomerRateCard: CustomerRateCard includes field rate_kind.
  - [backend_schema] CustomerRateCardCreate: CustomerRateCardCreate includes field rate_kind.
  - [backend_schema] CustomerRateCardUpdate: CustomerRateCardUpdate includes field rate_kind.
  - [backend_schema] CustomerRateCardListItem: CustomerRateCardListItem includes field rate_kind.

## customer.reason

- canonical_name: reason
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Begründung
- labels_en: Reason
- definition_de: Feld Begründung im Kontext von Customer.
- definition_en: Reason field used in the Customer context.
- related_fields: none
- aliases: reason, customerAdmin.fields.reason, employeeBlockDraft.reason, Begründung, Reason, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.reason defines labels Begründung, Reason.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds employeeBlockDraft.reason next to customerAdmin.fields.reason.
  - [typescript_api_interface] AssistantLink: AssistantLink includes field reason.
  - [typescript_api_interface] AssistantMissingPermission: AssistantMissingPermission includes field reason.
  - [typescript_api_interface] CustomerEmployeeBlockRead: CustomerEmployeeBlockRead includes field reason.
  - [typescript_api_interface] CustomerEmployeeBlockPayload: CustomerEmployeeBlockPayload includes field reason.
  - [backend_schema] AssistantNavigationLink: AssistantNavigationLink includes field reason.
  - [backend_schema] AssistantMissingPermission: AssistantMissingPermission includes field reason.

## customer.region_code

- canonical_name: region_code
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Regionscode
- labels_en: Region code
- definition_de: Feld Regionscode im Kontext von Customer.
- definition_en: Region code field used in the Customer context.
- related_fields: none
- aliases: region_code, customerAdmin.fields.regionCode, surchargeRuleDraft.region_code, Regionscode, Region code, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.regionCode defines labels Region code, Regionscode.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds surchargeRuleDraft.region_code next to customerAdmin.fields.regionCode.
  - [typescript_api_interface] CustomerSurchargeRuleRead: CustomerSurchargeRuleRead includes field region_code.
  - [typescript_api_interface] CustomerSurchargeRulePayload: CustomerSurchargeRulePayload includes field region_code.
  - [typescript_api_interface] PayrollTariffTableListItem: PayrollTariffTableListItem includes field region_code.
  - [backend_schema] CustomerSurchargeRule: CustomerSurchargeRule includes field region_code.
  - [backend_schema] CustomerSurchargeRuleCreate: CustomerSurchargeRuleCreate includes field region_code.
  - [backend_schema] CustomerSurchargeRuleUpdate: CustomerSurchargeRuleUpdate includes field region_code.

## customer.search

- canonical_name: search
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: SicherPlanCustomers
- form_contexts: customers.list_and_search, customer_create, customer_scoped_order_create, customer_order_create, customer_plan_create
- input_type: input
- required: False
- confidence: medium
- labels_de: Suche
- labels_en: Search
- definition_de: Feld Suche im Kontext von Customer.
- definition_en: Search field used in the Customer context.
- related_fields: none
- aliases: search, Search, Suche, Customer
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.list_and_search includes field search labeled Search.
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.list_and_search includes field search labeled Suche.
  - [typescript_api_interface] CustomerFilterParams: CustomerFilterParams includes field search.
  - [typescript_api_interface] CustomerExportPayload: CustomerExportPayload includes field search.
  - [typescript_api_interface] EmployeeListFilters: EmployeeListFilters includes field search.
  - [typescript_api_interface] CustomerOrderListFilters: CustomerOrderListFilters includes field search.
  - [typescript_api_interface] PlanningRecordListFilters: PlanningRecordListFilters includes field search.
  - [typescript_api_interface] RecruitingApplicantFilterParams: RecruitingApplicantFilterParams includes field search.

## customer.shipping_method_code

- canonical_name: shipping_method_code
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Versandweg
- labels_en: Dispatch method
- definition_de: Feld Versandweg im Kontext von Customer.
- definition_en: Dispatch method field used in the Customer context.
- related_fields: none
- aliases: shipping_method_code, customerAdmin.fields.shippingMethodCode, billingProfileDraft.shipping_method_code, Versandweg, Dispatch method, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.shippingMethodCode defines labels Dispatch method, Versandweg.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds billingProfileDraft.shipping_method_code next to customerAdmin.fields.shippingMethodCode.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field shipping_method_code.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field shipping_method_code.
  - [typescript_api_interface] PlanningCommercialLinkRead: PlanningCommercialLinkRead includes field shipping_method_code.
  - [backend_schema] CustomerBillingProfile: CustomerBillingProfile includes field shipping_method_code.
  - [backend_schema] CustomerBillingProfileCreate: CustomerBillingProfileCreate includes field shipping_method_code.
  - [backend_schema] CustomerBillingProfileUpdate: CustomerBillingProfileUpdate includes field shipping_method_code.

## customer.sort_order

- canonical_name: sort_order
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: number
- required: unknown
- confidence: high
- labels_de: Sortierung
- labels_en: Sort order
- definition_de: Feld Sortierung im Kontext von Customer.
- definition_en: Sort order field used in the Customer context.
- related_fields: none
- aliases: sort_order, customerAdmin.fields.sortOrder, rateLineDraft.sort_order, Sortierung, Sort order, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.sortOrder defines labels Sort order, Sortierung.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds rateLineDraft.sort_order next to customerAdmin.fields.sortOrder.
  - [typescript_api_interface] LookupValueRead: LookupValueRead includes field sort_order.
  - [typescript_api_interface] LookupValueCreatePayload: LookupValueCreatePayload includes field sort_order.
  - [typescript_api_interface] LookupValueUpdatePayload: LookupValueUpdatePayload includes field sort_order.
  - [typescript_api_interface] CustomerHistoryEntryRead: CustomerHistoryEntryRead includes field sort_order.
  - [typescript_api_interface] CustomerRateLineRead: CustomerRateLineRead includes field sort_order.
  - [typescript_api_interface] CustomerSurchargeRuleRead: CustomerSurchargeRuleRead includes field sort_order.

## customer.state

- canonical_name: state
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Bundesland / Region
- labels_en: State / region
- definition_de: Feld Bundesland / Region im Kontext von Customer.
- definition_en: State / region field used in the Customer context.
- related_fields: none
- aliases: state, customerAdmin.fields.state, addressDirectoryDraft.state, Bundesland / Region, State / region, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.state defines labels Bundesland / Region, State / region.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds addressDirectoryDraft.state next to customerAdmin.fields.state.
  - [typescript_api_interface] CustomerAddressRead: CustomerAddressRead includes field state.
  - [typescript_api_interface] CustomerAvailableAddressRead: CustomerAvailableAddressRead includes field state.
  - [typescript_api_interface] CustomerAvailableAddressCreatePayload: CustomerAvailableAddressCreatePayload includes field state.
  - [backend_schema] Address: Address includes field state.
  - [backend_schema] AddressCreate: AddressCreate includes field state.

## customer.street_line1

- canonical_name: street_line1
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: medium
- labels_de: Straße und Hausnummer
- labels_en: Street and house number
- definition_de: Feld Straße und Hausnummer im Kontext von Customer.
- definition_en: Street and house number field used in the Customer context.
- related_fields: none
- aliases: street_line1, customerAdmin.fields.streetLine1, addressDirectoryDraft.street_line_1, Straße und Hausnummer, Street and house number, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.streetLine1 defines labels Straße und Hausnummer, Street and house number.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds addressDirectoryDraft.street_line_1 next to customerAdmin.fields.streetLine1.

## customer.street_line2

- canonical_name: street_line2
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: medium
- labels_de: Adresszusatz
- labels_en: Address line 2
- definition_de: Feld Adresszusatz im Kontext von Customer.
- definition_en: Address line 2 field used in the Customer context.
- related_fields: none
- aliases: street_line2, customerAdmin.fields.streetLine2, addressDirectoryDraft.street_line_2, Adresszusatz, Address line 2, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.streetLine2 defines labels Address line 2, Adresszusatz.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds addressDirectoryDraft.street_line_2 next to customerAdmin.fields.streetLine2.

## customer.surcharge_type

- canonical_name: surcharge_type
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Zuschlagstyp
- labels_en: Surcharge type
- definition_de: Feld Zuschlagstyp im Kontext von Customer.
- definition_en: Surcharge type field used in the Customer context.
- related_fields: none
- aliases: surcharge_type, customerAdmin.fields.surchargeType, surchargeRuleDraft.surcharge_type, Zuschlagstyp, Surcharge type, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.surchargeType defines labels Surcharge type, Zuschlagstyp.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds surchargeRuleDraft.surcharge_type next to customerAdmin.fields.surchargeType.
  - [typescript_api_interface] CustomerSurchargeRuleRead: CustomerSurchargeRuleRead includes field surcharge_type.
  - [typescript_api_interface] CustomerSurchargeRulePayload: CustomerSurchargeRulePayload includes field surcharge_type.
  - [backend_schema] CustomerSurchargeRule: CustomerSurchargeRule includes field surcharge_type.
  - [backend_schema] CustomerSurchargeRuleCreate: CustomerSurchargeRuleCreate includes field surcharge_type.
  - [backend_schema] CustomerSurchargeRuleUpdate: CustomerSurchargeRuleUpdate includes field surcharge_type.
  - [backend_schema] CustomerSurchargeRuleRead: CustomerSurchargeRuleRead includes field surcharge_type.

## customer.tax_exempt

- canonical_name: tax_exempt
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Steuerbefreit
- labels_en: Tax exempt
- definition_de: Feld Steuerbefreit im Kontext von Customer.
- definition_en: Tax exempt field used in the Customer context.
- related_fields: none
- aliases: tax_exempt, customerAdmin.fields.taxExempt, billingProfileDraft.tax_exemption_reason, Steuerbefreit, Tax exempt, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.taxExempt defines labels Steuerbefreit, Tax exempt.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds billingProfileDraft.tax_exemption_reason next to customerAdmin.fields.taxExempt.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field tax_exempt.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field tax_exempt.
  - [backend_schema] CustomerBillingProfile: CustomerBillingProfile includes field tax_exempt.
  - [backend_schema] CustomerBillingProfileCreate: CustomerBillingProfileCreate includes field tax_exempt.
  - [backend_schema] CustomerBillingProfileUpdate: CustomerBillingProfileUpdate includes field tax_exempt.
  - [backend_schema] CustomerBillingProfileRead: CustomerBillingProfileRead includes field tax_exempt.

## customer.tax_exemption_reason

- canonical_name: tax_exemption_reason
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Grund für Steuerbefreiung
- labels_en: Tax-exemption reason
- definition_de: Feld Grund für Steuerbefreiung im Kontext von Customer.
- definition_en: Tax-exemption reason field used in the Customer context.
- related_fields: none
- aliases: tax_exemption_reason, customerAdmin.fields.taxExemptionReason, billingProfileDraft.tax_exemption_reason, Grund für Steuerbefreiung, Tax-exemption reason, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.taxExemptionReason defines labels Grund für Steuerbefreiung, Tax-exemption reason.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds billingProfileDraft.tax_exemption_reason next to customerAdmin.fields.taxExemptionReason.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field tax_exemption_reason.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field tax_exemption_reason.
  - [backend_schema] CustomerBillingProfile: CustomerBillingProfile includes field tax_exemption_reason.
  - [backend_schema] CustomerBillingProfileCreate: CustomerBillingProfileCreate includes field tax_exemption_reason.
  - [backend_schema] CustomerBillingProfileUpdate: CustomerBillingProfileUpdate includes field tax_exemption_reason.
  - [backend_schema] CustomerBillingProfileRead: CustomerBillingProfileRead includes field tax_exemption_reason.

## customer.tax_number

- canonical_name: tax_number
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Steuernummer
- labels_en: Tax number
- definition_de: Feld Steuernummer im Kontext von Customer.
- definition_en: Tax number field used in the Customer context.
- related_fields: none
- aliases: tax_number, customerAdmin.fields.taxNumber, billingProfileDraft.tax_number, Steuernummer, Tax number, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.taxNumber defines labels Steuernummer, Tax number.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds billingProfileDraft.tax_number next to customerAdmin.fields.taxNumber.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field tax_number.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field tax_number.
  - [typescript_api_interface] SubcontractorFinanceProfileRead: SubcontractorFinanceProfileRead includes field tax_number.
  - [backend_schema] CustomerBillingProfile: CustomerBillingProfile includes field tax_number.
  - [backend_schema] CustomerBillingProfileCreate: CustomerBillingProfileCreate includes field tax_number.
  - [backend_schema] CustomerBillingProfileUpdate: CustomerBillingProfileUpdate includes field tax_number.

## customer.temporary_password

- canonical_name: temporary_password
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Temporäres Passwort
- labels_en: Temporary password
- definition_de: Feld Temporäres Passwort im Kontext von Customer.
- definition_en: Temporary password field used in the Customer context.
- related_fields: none
- aliases: temporary_password, customerAdmin.fields.temporaryPassword, portalAccessDraft.temporary_password, Temporäres Passwort, Temporary password, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.temporaryPassword defines labels Temporary password, Temporäres Passwort.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds portalAccessDraft.temporary_password next to customerAdmin.fields.temporaryPassword.
  - [typescript_api_interface] CustomerPortalAccessCreatePayload: CustomerPortalAccessCreatePayload includes field temporary_password.
  - [typescript_api_interface] CustomerPortalAccessPasswordResetPayload: CustomerPortalAccessPasswordResetPayload includes field temporary_password.
  - [typescript_api_interface] CustomerPortalAccessPasswordResponse: CustomerPortalAccessPasswordResponse includes field temporary_password.
  - [typescript_api_interface] TenantAdminUserCreatePayload: TenantAdminUserCreatePayload includes field temporary_password.
  - [typescript_api_interface] TenantAdminPasswordResponse: TenantAdminPasswordResponse includes field temporary_password.
  - [backend_schema] CustomerPortalAccessCreate: CustomerPortalAccessCreate includes field temporary_password.

## customer.time_from_minute

- canonical_name: time_from_minute
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Von Minute
- labels_en: From minute
- definition_de: Feld Von Minute im Kontext von Customer.
- definition_en: From minute field used in the Customer context.
- related_fields: none
- aliases: time_from_minute, customerAdmin.fields.timeFromMinute, surchargeTimeFromInput, Von Minute, From minute, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.timeFromMinute defines labels From minute, Von Minute.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds surchargeTimeFromInput next to customerAdmin.fields.timeFromMinute.
  - [typescript_api_interface] CustomerSurchargeRuleRead: CustomerSurchargeRuleRead includes field time_from_minute.
  - [typescript_api_interface] CustomerSurchargeRulePayload: CustomerSurchargeRulePayload includes field time_from_minute.
  - [backend_schema] CustomerSurchargeRule: CustomerSurchargeRule includes field time_from_minute.
  - [backend_schema] CustomerSurchargeRuleCreate: CustomerSurchargeRuleCreate includes field time_from_minute.
  - [backend_schema] CustomerSurchargeRuleUpdate: CustomerSurchargeRuleUpdate includes field time_from_minute.
  - [backend_schema] CustomerSurchargeRuleRead: CustomerSurchargeRuleRead includes field time_from_minute.

## customer.time_to_minute

- canonical_name: time_to_minute
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Bis Minute
- labels_en: To minute
- definition_de: Feld Bis Minute im Kontext von Customer.
- definition_en: To minute field used in the Customer context.
- related_fields: none
- aliases: time_to_minute, customerAdmin.fields.timeToMinute, surchargeTimeToInput, Bis Minute, To minute, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.timeToMinute defines labels Bis Minute, To minute.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds surchargeTimeToInput next to customerAdmin.fields.timeToMinute.
  - [typescript_api_interface] CustomerSurchargeRuleRead: CustomerSurchargeRuleRead includes field time_to_minute.
  - [typescript_api_interface] CustomerSurchargeRulePayload: CustomerSurchargeRulePayload includes field time_to_minute.
  - [backend_schema] CustomerSurchargeRule: CustomerSurchargeRule includes field time_to_minute.
  - [backend_schema] CustomerSurchargeRuleCreate: CustomerSurchargeRuleCreate includes field time_to_minute.
  - [backend_schema] CustomerSurchargeRuleUpdate: CustomerSurchargeRuleUpdate includes field time_to_minute.
  - [backend_schema] CustomerSurchargeRuleRead: CustomerSurchargeRuleRead includes field time_to_minute.

## customer.unit_price

- canonical_name: unit_price
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: number
- required: unknown
- confidence: high
- labels_de: Einzelpreis
- labels_en: Unit price
- definition_de: Feld Einzelpreis im Kontext von Customer.
- definition_en: Unit price field used in the Customer context.
- related_fields: none
- aliases: unit_price, customerAdmin.fields.unitPrice, rateLineDraft.unit_price, Einzelpreis, Unit price, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.unitPrice defines labels Einzelpreis, Unit price.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds rateLineDraft.unit_price next to customerAdmin.fields.unitPrice.
  - [typescript_api_interface] CustomerRateLineRead: CustomerRateLineRead includes field unit_price.
  - [typescript_api_interface] CustomerRateLinePayload: CustomerRateLinePayload includes field unit_price.
  - [typescript_api_interface] FinanceBillingInvoiceLineRead: FinanceBillingInvoiceLineRead includes field unit_price.
  - [typescript_api_interface] FinanceSubcontractorInvoiceCheckLineRead: FinanceSubcontractorInvoiceCheckLineRead includes field unit_price.
  - [typescript_api_interface] SubcontractorPortalInvoiceCheckLineRead: SubcontractorPortalInvoiceCheckLineRead includes field unit_price.
  - [backend_schema] CustomerRateLine: CustomerRateLine includes field unit_price.

## customer.user_id

- canonical_name: user_id
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: unknown
- required: unknown
- confidence: medium
- labels_de: Portal-Benutzer-ID
- labels_en: Portal user ID
- definition_de: Feld Portal-Benutzer-ID im Kontext von Customer.
- definition_en: Portal user ID field used in the Customer context.
- related_fields: none
- aliases: user_id, customerAdmin.fields.userId, Portal-Benutzer-ID, Portal user ID, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.userId defines labels Portal user ID, Portal-Benutzer-ID.
  - [typescript_api_interface] CustomerPortalAccessListItem: CustomerPortalAccessListItem includes field user_id.
  - [typescript_api_interface] CustomerPortalContextRead: CustomerPortalContextRead includes field user_id.
  - [typescript_api_interface] SubcontractorPortalContextRead: SubcontractorPortalContextRead includes field user_id.
  - [typescript_api_interface] CustomerContactRead: CustomerContactRead includes field user_id.
  - [typescript_api_interface] CustomerContactPayload: CustomerContactPayload includes field user_id.
  - [typescript_api_interface] EmployeeAccessLinkRead: EmployeeAccessLinkRead includes field user_id.
  - [typescript_api_interface] SubcontractorContactRead: SubcontractorContactRead includes field user_id.

## customer.username

- canonical_name: username
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Benutzername
- labels_en: Username
- definition_de: Feld Benutzername im Kontext von Customer.
- definition_en: Username field used in the Customer context.
- related_fields: none
- aliases: username, customerAdmin.fields.username, portalAccessDraft.username, Benutzername, Username, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.username defines labels Benutzername, Username.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds portalAccessDraft.username next to customerAdmin.fields.username.
  - [typescript_api_interface] CustomerPortalAccessListItem: CustomerPortalAccessListItem includes field username.
  - [typescript_api_interface] CustomerPortalAccessCreatePayload: CustomerPortalAccessCreatePayload includes field username.
  - [typescript_api_interface] TenantAdminUserListItem: TenantAdminUserListItem includes field username.
  - [typescript_api_interface] TenantAdminUserCreatePayload: TenantAdminUserCreatePayload includes field username.
  - [typescript_api_interface] AuthenticatedUser: AuthenticatedUser includes field username.
  - [typescript_api_interface] EmployeeAccessLinkRead: EmployeeAccessLinkRead includes field username.

## customer.vat_id

- canonical_name: vat_id
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: SicherPlanCustomers
- form_contexts: customers.contacts_addresses_billing, customer_create, customer_scoped_order_create, customer_order_create, customer_plan_create
- input_type: input
- required: False
- confidence: high
- labels_de: USt-IdNr.
- labels_en: VAT ID
- definition_de: Feld USt-IdNr. im Kontext von Customer.
- definition_en: VAT ID field used in the Customer context.
- related_fields: none
- aliases: vat_id, VAT ID, USt-IdNr., customerAdmin.fields.vatId, billingProfileDraft.vat_id, Customer
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.contacts_addresses_billing includes field vat_id labeled VAT ID.
  - [page_help_manifest] Assistant Page Help Manifest: C-01 manifest section customers.contacts_addresses_billing includes field vat_id labeled USt-IdNr..
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.vatId defines labels USt-IdNr., VAT ID.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds billingProfileDraft.vat_id next to customerAdmin.fields.vatId.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field vat_id.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field vat_id.
  - [typescript_api_interface] SubcontractorFinanceProfileRead: SubcontractorFinanceProfileRead includes field vat_id.
  - [backend_schema] CustomerBillingProfile: CustomerBillingProfile includes field vat_id.

## customer.weekday_mask

- canonical_name: weekday_mask
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: unknown
- required: unknown
- confidence: medium
- labels_de: Wochentagsmaske
- labels_en: Weekday mask
- definition_de: Feld Wochentagsmaske im Kontext von Customer.
- definition_en: Weekday mask field used in the Customer context.
- related_fields: none
- aliases: weekday_mask, customerAdmin.fields.weekdayMask, Wochentagsmaske, Weekday mask, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.weekdayMask defines labels Weekday mask, Wochentagsmaske.
  - [typescript_api_interface] CustomerSurchargeRuleRead: CustomerSurchargeRuleRead includes field weekday_mask.
  - [typescript_api_interface] CustomerSurchargeRulePayload: CustomerSurchargeRulePayload includes field weekday_mask.
  - [typescript_api_interface] EmployeeAvailabilityRuleRead: EmployeeAvailabilityRuleRead includes field weekday_mask.
  - [typescript_api_interface] EmployeeAvailabilityRuleCreatePayload: EmployeeAvailabilityRuleCreatePayload includes field weekday_mask.
  - [typescript_api_interface] EmployeeAvailabilityRuleUpdatePayload: EmployeeAvailabilityRuleUpdatePayload includes field weekday_mask.
  - [typescript_api_interface] PayrollSurchargeRuleRead: PayrollSurchargeRuleRead includes field weekday_mask.
  - [typescript_api_interface] ShiftSeriesListItem: ShiftSeriesListItem includes field weekday_mask.

## customer.weekdays

- canonical_name: weekdays
- module_key: customers
- page_id: C-01
- entity_type: Customer
- route_names: none
- form_contexts: none
- input_type: unknown
- required: unknown
- confidence: low
- labels_de: Wochentage
- labels_en: Weekdays
- definition_de: Feld Wochentage im Kontext von Customer.
- definition_en: Weekdays field used in the Customer context.
- related_fields: none
- aliases: weekdays, customerAdmin.fields.weekdays, Wochentage, Weekdays, Customer
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: customerAdmin.fields.weekdays defines labels Weekdays, Wochentage.

## customer_order.date_from

- canonical_name: date_from
- module_key: customers
- page_id: C-02
- entity_type: CustomerOrder
- route_names: SicherPlanCustomerOrderWorkspace
- form_contexts: customer_order_workspace.series_exceptions, customer_scoped_order_create, customer_plan_create, customer_contract_register_from_customer
- input_type: input
- required: False
- confidence: medium
- labels_de: Datum von
- labels_en: Date from
- definition_de: Feld Datum von im Kontext von CustomerOrder.
- definition_en: Date from field used in the CustomerOrder context.
- related_fields: none
- aliases: date_from, Date from, Datum von, CustomerOrder
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.series_exceptions includes field date_from labeled Date from.
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.series_exceptions includes field date_from labeled Datum von.
  - [typescript_api_interface] ShiftSeriesListItem: ShiftSeriesListItem includes field date_from.
  - [typescript_api_interface] CoverageFilterParams: CoverageFilterParams includes field date_from.
  - [typescript_api_interface] DemandGroupBulkApplyRequest: DemandGroupBulkApplyRequest includes field date_from.
  - [typescript_api_interface] DemandGroupBulkUpdateRequest: DemandGroupBulkUpdateRequest includes field date_from.
  - [backend_schema] AssistantPlanningShiftSearchInput: AssistantPlanningShiftSearchInput includes field date_from.
  - [backend_schema] AssistantPlanningAssignmentSearchInput: AssistantPlanningAssignmentSearchInput includes field date_from.

## customer_order.date_to

- canonical_name: date_to
- module_key: customers
- page_id: C-02
- entity_type: CustomerOrder
- route_names: SicherPlanCustomerOrderWorkspace
- form_contexts: customer_order_workspace.series_exceptions, customer_scoped_order_create, customer_plan_create, customer_contract_register_from_customer
- input_type: input
- required: False
- confidence: medium
- labels_de: Datum bis
- labels_en: Date to
- definition_de: Feld Datum bis im Kontext von CustomerOrder.
- definition_en: Date to field used in the CustomerOrder context.
- related_fields: none
- aliases: date_to, Date to, Datum bis, CustomerOrder
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.series_exceptions includes field date_to labeled Date to.
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.series_exceptions includes field date_to labeled Datum bis.
  - [typescript_api_interface] ShiftSeriesListItem: ShiftSeriesListItem includes field date_to.
  - [typescript_api_interface] CoverageFilterParams: CoverageFilterParams includes field date_to.
  - [typescript_api_interface] DemandGroupBulkApplyRequest: DemandGroupBulkApplyRequest includes field date_to.
  - [typescript_api_interface] DemandGroupBulkUpdateRequest: DemandGroupBulkUpdateRequest includes field date_to.
  - [backend_schema] AssistantPlanningShiftSearchInput: AssistantPlanningShiftSearchInput includes field date_to.
  - [backend_schema] AssistantPlanningAssignmentSearchInput: AssistantPlanningAssignmentSearchInput includes field date_to.

## customer_order.equipment_lines

- canonical_name: equipment_lines
- module_key: customers
- page_id: C-02
- entity_type: CustomerOrder
- route_names: SicherPlanCustomerOrderWorkspace
- form_contexts: customer_order_workspace.order_scope_documents, customer_scoped_order_create, customer_plan_create, customer_contract_register_from_customer
- input_type: input
- required: False
- confidence: medium
- labels_de: Equipment-Zeilen
- labels_en: Equipment lines
- definition_de: Feld Equipment-Zeilen im Kontext von CustomerOrder.
- definition_en: Equipment lines field used in the CustomerOrder context.
- related_fields: none
- aliases: equipment_lines, Equipment lines, Equipment-Zeilen, CustomerOrder
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.order_scope_documents includes field equipment_lines labeled Equipment lines.
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.order_scope_documents includes field equipment_lines labeled Equipment-Zeilen.
  - [backend_schema] CustomerOrder: CustomerOrder includes field equipment_lines.
  - [backend_schema] CustomerOrderRead: CustomerOrderRead includes field equipment_lines.

## customer_order.name

- canonical_name: name
- module_key: customers
- page_id: C-02
- entity_type: CustomerOrder
- route_names: SicherPlanCustomerOrderWorkspace
- form_contexts: customer_order_workspace.shift_plan, customer_scoped_order_create, customer_plan_create, customer_contract_register_from_customer
- input_type: input
- required: False
- confidence: medium
- labels_de: Name Schichtplan
- labels_en: Shift plan name
- definition_de: Feld Name Schichtplan im Kontext von CustomerOrder.
- definition_en: Shift plan name field used in the CustomerOrder context.
- related_fields: none
- aliases: name, Shift plan name, Name Schichtplan, CustomerOrder
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.shift_plan includes field name labeled Shift plan name.
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.shift_plan includes field name labeled Name Schichtplan.
  - [typescript_api_interface] TenantListItem: TenantListItem includes field name.
  - [typescript_api_interface] CustomerPortalContextRead: CustomerPortalContextRead includes field name.
  - [typescript_api_interface] BranchRead: BranchRead includes field name.
  - [typescript_api_interface] MandateRead: MandateRead includes field name.
  - [typescript_api_interface] TenantOnboardingPayload: TenantOnboardingPayload includes field name.
  - [typescript_api_interface] TenantUpdatePayload: TenantUpdatePayload includes field name.

## customer_order.order_documents

- canonical_name: order_documents
- module_key: customers
- page_id: C-02
- entity_type: CustomerOrder
- route_names: SicherPlanCustomerOrderWorkspace
- form_contexts: customer_order_workspace.order_scope_documents, customer_scoped_order_create, customer_plan_create, customer_contract_register_from_customer
- input_type: input
- required: False
- confidence: low
- labels_de: Auftragsdokumente
- labels_en: Order documents
- definition_de: Feld Auftragsdokumente im Kontext von CustomerOrder.
- definition_en: Order documents field used in the CustomerOrder context.
- related_fields: none
- aliases: order_documents, Order documents, Auftragsdokumente, CustomerOrder
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.order_scope_documents includes field order_documents labeled Order documents.
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.order_scope_documents includes field order_documents labeled Auftragsdokumente.

## customer_order.order_no

- canonical_name: order_no
- module_key: customers
- page_id: C-02
- entity_type: CustomerOrder
- route_names: SicherPlanCustomerOrderWorkspace
- form_contexts: customer_order_workspace.order_details, customer_scoped_order_create, customer_plan_create, customer_contract_register_from_customer
- input_type: input
- required: False
- confidence: medium
- labels_de: Auftragsnummer
- labels_en: Order no
- definition_de: Feld Auftragsnummer im Kontext von CustomerOrder.
- definition_en: Order no field used in the CustomerOrder context.
- related_fields: none
- aliases: order_no, Order no, Auftragsnummer, CustomerOrder
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.order_details includes field order_no labeled Order no.
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.order_details includes field order_no labeled Auftragsnummer.
  - [typescript_api_interface] CustomerDashboardPlanItemRead: CustomerDashboardPlanItemRead includes field order_no.
  - [typescript_api_interface] CustomerOrderListItem: CustomerOrderListItem includes field order_no.
  - [typescript_api_interface] PlanningBoardShiftListItem: PlanningBoardShiftListItem includes field order_no.
  - [typescript_api_interface] CoverageShiftItem: CoverageShiftItem includes field order_no.
  - [typescript_api_interface] StaffingBoardShiftItem: StaffingBoardShiftItem includes field order_no.
  - [typescript_api_interface] EmployeeProjectContext: EmployeeProjectContext includes field order_no.

## customer_order.planning_documents

- canonical_name: planning_documents
- module_key: customers
- page_id: C-02
- entity_type: CustomerOrder
- route_names: SicherPlanCustomerOrderWorkspace
- form_contexts: customer_order_workspace.planning_record_documents, customer_scoped_order_create, customer_plan_create, customer_contract_register_from_customer
- input_type: input
- required: False
- confidence: low
- labels_de: Planungsdokumente
- labels_en: Planning documents
- definition_de: Feld Planungsdokumente im Kontext von CustomerOrder.
- definition_en: Planning documents field used in the CustomerOrder context.
- related_fields: none
- aliases: planning_documents, Planning documents, Planungsdokumente, CustomerOrder
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.planning_record_documents includes field planning_documents labeled Planning documents.
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.planning_record_documents includes field planning_documents labeled Planungsdokumente.

## customer_order.planning_from

- canonical_name: planning_from
- module_key: customers
- page_id: C-02
- entity_type: CustomerOrder
- route_names: SicherPlanCustomerOrderWorkspace
- form_contexts: customer_order_workspace.planning_record_overview, customer_scoped_order_create, customer_plan_create, customer_contract_register_from_customer
- input_type: input
- required: False
- confidence: medium
- labels_de: Planung von
- labels_en: Planning from
- definition_de: Feld Planung von im Kontext von CustomerOrder.
- definition_en: Planning from field used in the CustomerOrder context.
- related_fields: none
- aliases: planning_from, Planning from, Planung von, CustomerOrder
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.planning_record_overview includes field planning_from labeled Planning from.
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.planning_record_overview includes field planning_from labeled Planung von.
  - [typescript_api_interface] CustomerDashboardPlanItemRead: CustomerDashboardPlanItemRead includes field planning_from.
  - [typescript_api_interface] PlanningRecordListItem: PlanningRecordListItem includes field planning_from.
  - [typescript_api_interface] PlanningRecordListFilters: PlanningRecordListFilters includes field planning_from.
  - [typescript_api_interface] ShiftPlanListItem: ShiftPlanListItem includes field planning_from.
  - [backend_schema] CustomerDashboardPlanItemRead: CustomerDashboardPlanItemRead includes field planning_from.
  - [backend_schema] PlanningRecord: PlanningRecord includes field planning_from.

## customer_order.planning_mode_code

- canonical_name: planning_mode_code
- module_key: customers
- page_id: C-02
- entity_type: CustomerOrder
- route_names: SicherPlanCustomerOrderWorkspace
- form_contexts: customer_order_workspace.planning_record_overview, customer_scoped_order_create, customer_plan_create, customer_contract_register_from_customer
- input_type: input
- required: False
- confidence: medium
- labels_de: Planungsmodus
- labels_en: Planning mode
- definition_de: Feld Planungsmodus im Kontext von CustomerOrder.
- definition_en: Planning mode field used in the CustomerOrder context.
- related_fields: none
- aliases: planning_mode_code, Planning mode, Planungsmodus, CustomerOrder
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.planning_record_overview includes field planning_mode_code labeled Planning mode.
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.planning_record_overview includes field planning_mode_code labeled Planungsmodus.
  - [typescript_api_interface] CustomerDashboardPlanItemRead: CustomerDashboardPlanItemRead includes field planning_mode_code.
  - [typescript_api_interface] CustomerRateLineRead: CustomerRateLineRead includes field planning_mode_code.
  - [typescript_api_interface] CustomerRateLinePayload: CustomerRateLinePayload includes field planning_mode_code.
  - [typescript_api_interface] FinanceBillingTimesheetLineRead: FinanceBillingTimesheetLineRead includes field planning_mode_code.
  - [typescript_api_interface] PlanningRecordListItem: PlanningRecordListItem includes field planning_mode_code.
  - [typescript_api_interface] PlanningRecordListFilters: PlanningRecordListFilters includes field planning_mode_code.

## customer_order.planning_to

- canonical_name: planning_to
- module_key: customers
- page_id: C-02
- entity_type: CustomerOrder
- route_names: SicherPlanCustomerOrderWorkspace
- form_contexts: customer_order_workspace.planning_record_overview, customer_scoped_order_create, customer_plan_create, customer_contract_register_from_customer
- input_type: input
- required: False
- confidence: medium
- labels_de: Planung bis
- labels_en: Planning to
- definition_de: Feld Planung bis im Kontext von CustomerOrder.
- definition_en: Planning to field used in the CustomerOrder context.
- related_fields: none
- aliases: planning_to, Planning to, Planung bis, CustomerOrder
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.planning_record_overview includes field planning_to labeled Planning to.
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.planning_record_overview includes field planning_to labeled Planung bis.
  - [typescript_api_interface] CustomerDashboardPlanItemRead: CustomerDashboardPlanItemRead includes field planning_to.
  - [typescript_api_interface] PlanningRecordListItem: PlanningRecordListItem includes field planning_to.
  - [typescript_api_interface] PlanningRecordListFilters: PlanningRecordListFilters includes field planning_to.
  - [typescript_api_interface] ShiftPlanListItem: ShiftPlanListItem includes field planning_to.
  - [backend_schema] CustomerDashboardPlanItemRead: CustomerDashboardPlanItemRead includes field planning_to.
  - [backend_schema] PlanningRecord: PlanningRecord includes field planning_to.

## customer_order.recurrence_code

- canonical_name: recurrence_code
- module_key: customers
- page_id: C-02
- entity_type: CustomerOrder
- route_names: SicherPlanCustomerOrderWorkspace
- form_contexts: customer_order_workspace.series_exceptions, customer_scoped_order_create, customer_plan_create, customer_contract_register_from_customer
- input_type: input
- required: False
- confidence: medium
- labels_de: Wiederholung
- labels_en: Recurrence
- definition_de: Feld Wiederholung im Kontext von CustomerOrder.
- definition_en: Recurrence field used in the CustomerOrder context.
- related_fields: none
- aliases: recurrence_code, Recurrence, Wiederholung, CustomerOrder
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.series_exceptions includes field recurrence_code labeled Recurrence.
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.series_exceptions includes field recurrence_code labeled Wiederholung.
  - [typescript_api_interface] ShiftSeriesListItem: ShiftSeriesListItem includes field recurrence_code.
  - [backend_schema] ShiftSeries: ShiftSeries includes field recurrence_code.
  - [backend_schema] ShiftSeriesCreate: ShiftSeriesCreate includes field recurrence_code.
  - [backend_schema] ShiftSeriesUpdate: ShiftSeriesUpdate includes field recurrence_code.
  - [backend_schema] ShiftSeriesListItem: ShiftSeriesListItem includes field recurrence_code.

## customer_order.requirement_lines

- canonical_name: requirement_lines
- module_key: customers
- page_id: C-02
- entity_type: CustomerOrder
- route_names: SicherPlanCustomerOrderWorkspace
- form_contexts: customer_order_workspace.order_scope_documents, customer_scoped_order_create, customer_plan_create, customer_contract_register_from_customer
- input_type: input
- required: False
- confidence: medium
- labels_de: Anforderungszeilen
- labels_en: Requirement lines
- definition_de: Feld Anforderungszeilen im Kontext von CustomerOrder.
- definition_en: Requirement lines field used in the CustomerOrder context.
- related_fields: none
- aliases: requirement_lines, Requirement lines, Anforderungszeilen, CustomerOrder
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.order_scope_documents includes field requirement_lines labeled Requirement lines.
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.order_scope_documents includes field requirement_lines labeled Anforderungszeilen.
  - [backend_schema] CustomerOrder: CustomerOrder includes field requirement_lines.
  - [backend_schema] CustomerOrderRead: CustomerOrderRead includes field requirement_lines.

## customer_order.requirement_type_id

- canonical_name: requirement_type_id
- module_key: customers
- page_id: C-02
- entity_type: CustomerOrder
- route_names: SicherPlanCustomerOrderWorkspace
- form_contexts: customer_order_workspace.order_details, customer_scoped_order_create, customer_plan_create, customer_contract_register_from_customer
- input_type: input
- required: False
- confidence: medium
- labels_de: Bedarfsart
- labels_en: Requirement type
- definition_de: Feld Bedarfsart im Kontext von CustomerOrder.
- definition_en: Requirement type field used in the CustomerOrder context.
- related_fields: none
- aliases: requirement_type_id, Requirement type, Bedarfsart, CustomerOrder
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.order_details includes field requirement_type_id labeled Requirement type.
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.order_details includes field requirement_type_id labeled Bedarfsart.
  - [typescript_api_interface] OrderRequirementLineRead: OrderRequirementLineRead includes field requirement_type_id.
  - [typescript_api_interface] CustomerOrderListItem: CustomerOrderListItem includes field requirement_type_id.
  - [backend_schema] CustomerOrder: CustomerOrder includes field requirement_type_id.
  - [backend_schema] OrderRequirementLine: OrderRequirementLine includes field requirement_type_id.
  - [backend_schema] OrderRequirementLineCreate: OrderRequirementLineCreate includes field requirement_type_id.
  - [backend_schema] OrderRequirementLineUpdate: OrderRequirementLineUpdate includes field requirement_type_id.

## customer_order.service_category_code

- canonical_name: service_category_code
- module_key: customers
- page_id: C-02
- entity_type: CustomerOrder
- route_names: SicherPlanCustomerOrderWorkspace
- form_contexts: customer_order_workspace.order_details, customer_scoped_order_create, customer_plan_create, customer_contract_register_from_customer
- input_type: input
- required: False
- confidence: medium
- labels_de: Leistungskategorie
- labels_en: Service category
- definition_de: Feld Leistungskategorie im Kontext von CustomerOrder.
- definition_en: Service category field used in the CustomerOrder context.
- related_fields: none
- aliases: service_category_code, Service category, Leistungskategorie, CustomerOrder
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.order_details includes field service_category_code labeled Service category.
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.order_details includes field service_category_code labeled Leistungskategorie.
  - [typescript_api_interface] CustomerOrderListItem: CustomerOrderListItem includes field service_category_code.
  - [backend_schema] CustomerOrder: CustomerOrder includes field service_category_code.
  - [backend_schema] CustomerOrderCreate: CustomerOrderCreate includes field service_category_code.
  - [backend_schema] CustomerOrderUpdate: CustomerOrderUpdate includes field service_category_code.
  - [backend_schema] CustomerOrderListItem: CustomerOrderListItem includes field service_category_code.

## customer_order.service_from

- canonical_name: service_from
- module_key: customers
- page_id: C-02
- entity_type: CustomerOrder
- route_names: SicherPlanCustomerOrderWorkspace
- form_contexts: customer_order_workspace.order_details, customer_scoped_order_create, customer_plan_create, customer_contract_register_from_customer
- input_type: input
- required: False
- confidence: medium
- labels_de: Leistung von
- labels_en: Service from
- definition_de: Feld Leistung von im Kontext von CustomerOrder.
- definition_en: Service from field used in the CustomerOrder context.
- related_fields: none
- aliases: service_from, Service from, Leistung von, CustomerOrder
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.order_details includes field service_from labeled Service from.
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.order_details includes field service_from labeled Leistung von.
  - [typescript_api_interface] CustomerPortalOrderListItemRead: CustomerPortalOrderListItemRead includes field service_from.
  - [typescript_api_interface] CustomerOrderListItem: CustomerOrderListItem includes field service_from.
  - [typescript_api_interface] CustomerOrderListFilters: CustomerOrderListFilters includes field service_from.
  - [backend_schema] CustomerPortalOrderListItemRead: CustomerPortalOrderListItemRead includes field service_from.
  - [backend_schema] CustomerOrder: CustomerOrder includes field service_from.
  - [backend_schema] CustomerOrderFilter: CustomerOrderFilter includes field service_from.

## customer_order.service_to

- canonical_name: service_to
- module_key: customers
- page_id: C-02
- entity_type: CustomerOrder
- route_names: SicherPlanCustomerOrderWorkspace
- form_contexts: customer_order_workspace.order_details, customer_scoped_order_create, customer_plan_create, customer_contract_register_from_customer
- input_type: input
- required: False
- confidence: medium
- labels_de: Leistung bis
- labels_en: Service to
- definition_de: Feld Leistung bis im Kontext von CustomerOrder.
- definition_en: Service to field used in the CustomerOrder context.
- related_fields: none
- aliases: service_to, Service to, Leistung bis, CustomerOrder
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.order_details includes field service_to labeled Service to.
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.order_details includes field service_to labeled Leistung bis.
  - [typescript_api_interface] CustomerPortalOrderListItemRead: CustomerPortalOrderListItemRead includes field service_to.
  - [typescript_api_interface] CustomerOrderListItem: CustomerOrderListItem includes field service_to.
  - [typescript_api_interface] CustomerOrderListFilters: CustomerOrderListFilters includes field service_to.
  - [backend_schema] CustomerPortalOrderListItemRead: CustomerPortalOrderListItemRead includes field service_to.
  - [backend_schema] CustomerOrder: CustomerOrder includes field service_to.
  - [backend_schema] CustomerOrderFilter: CustomerOrderFilter includes field service_to.

## customer_order.shift_template_id

- canonical_name: shift_template_id
- module_key: customers
- page_id: C-02
- entity_type: CustomerOrder
- route_names: SicherPlanCustomerOrderWorkspace
- form_contexts: customer_order_workspace.series_exceptions, customer_scoped_order_create, customer_plan_create, customer_contract_register_from_customer
- input_type: input
- required: False
- confidence: medium
- labels_de: Schichtvorlage
- labels_en: Shift template
- definition_de: Feld Schichtvorlage im Kontext von CustomerOrder.
- definition_en: Shift template field used in the CustomerOrder context.
- related_fields: none
- aliases: shift_template_id, Shift template, Schichtvorlage, CustomerOrder
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.series_exceptions includes field shift_template_id labeled Shift template.
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.series_exceptions includes field shift_template_id labeled Schichtvorlage.
  - [typescript_api_interface] ShiftSeriesListItem: ShiftSeriesListItem includes field shift_template_id.
  - [backend_schema] ShiftSeries: ShiftSeries includes field shift_template_id.
  - [backend_schema] ShiftSeriesCreate: ShiftSeriesCreate includes field shift_template_id.
  - [backend_schema] ShiftSeriesUpdate: ShiftSeriesUpdate includes field shift_template_id.
  - [backend_schema] ShiftSeriesListItem: ShiftSeriesListItem includes field shift_template_id.

## customer_order.title

- canonical_name: title
- module_key: customers
- page_id: C-02
- entity_type: CustomerOrder
- route_names: SicherPlanCustomerOrderWorkspace
- form_contexts: customer_order_workspace.order_details, customer_scoped_order_create, customer_plan_create, customer_contract_register_from_customer
- input_type: input
- required: False
- confidence: medium
- labels_de: Titel
- labels_en: Title
- definition_de: Feld Titel im Kontext von CustomerOrder.
- definition_en: Title field used in the CustomerOrder context.
- related_fields: none
- aliases: title, Title, Titel, CustomerOrder
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.order_details includes field title labeled Title.
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.order_details includes field title labeled Titel.
  - [typescript_api_interface] AssistantSourceBasisItem: AssistantSourceBasisItem includes field title.
  - [typescript_api_interface] AssistantConversation: AssistantConversation includes field title.
  - [typescript_api_interface] AssistantPageHelpFormSection: AssistantPageHelpFormSection includes field title.
  - [typescript_api_interface] CustomerPortalDocumentRefRead: CustomerPortalDocumentRefRead includes field title.
  - [typescript_api_interface] CustomerPortalHistoryEntryRead: CustomerPortalHistoryEntryRead includes field title.
  - [typescript_api_interface] CustomerPortalOrderListItemRead: CustomerPortalOrderListItemRead includes field title.

## customer_order.workforce_scope_code

- canonical_name: workforce_scope_code
- module_key: customers
- page_id: C-02
- entity_type: CustomerOrder
- route_names: SicherPlanCustomerOrderWorkspace
- form_contexts: customer_order_workspace.shift_plan, customer_scoped_order_create, customer_plan_create, customer_contract_register_from_customer
- input_type: input
- required: False
- confidence: medium
- labels_de: Workforce Scope
- labels_en: Workforce scope
- definition_de: Feld Workforce Scope im Kontext von CustomerOrder.
- definition_en: Workforce scope field used in the CustomerOrder context.
- related_fields: none
- aliases: workforce_scope_code, Workforce scope, Workforce Scope, CustomerOrder
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.shift_plan includes field workforce_scope_code labeled Workforce scope.
  - [page_help_manifest] Assistant Page Help Manifest: C-02 manifest section customer_order_workspace.shift_plan includes field workforce_scope_code labeled Workforce Scope.
  - [typescript_api_interface] ShiftPlanListItem: ShiftPlanListItem includes field workforce_scope_code.
  - [typescript_api_interface] PlanningBoardShiftListItem: PlanningBoardShiftListItem includes field workforce_scope_code.
  - [typescript_api_interface] CoverageShiftItem: CoverageShiftItem includes field workforce_scope_code.
  - [typescript_api_interface] CoverageFilterParams: CoverageFilterParams includes field workforce_scope_code.
  - [typescript_api_interface] StaffingBoardShiftItem: StaffingBoardShiftItem includes field workforce_scope_code.
  - [backend_schema] ShiftPlan: ShiftPlan includes field workforce_scope_code.

## dispatch.audience_code

- canonical_name: audience_code
- module_key: planning
- page_id: P-05
- entity_type: Dispatch
- route_names: SicherPlanPlanningStaffing
- form_contexts: planning_outputs.documents, shift_release_to_employee_app, employee_assign_to_shift
- input_type: input
- required: False
- confidence: medium
- labels_de: Zielgruppe
- labels_en: Audience
- definition_de: Feld Zielgruppe im Kontext von Dispatch.
- definition_en: Audience field used in the Dispatch context.
- related_fields: none
- aliases: audience_code, Audience, Zielgruppe, Dispatch
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-05 manifest section planning_outputs.documents includes field audience_code labeled Audience.
  - [page_help_manifest] Assistant Page Help Manifest: P-05 manifest section planning_outputs.documents includes field audience_code labeled Zielgruppe.
  - [typescript_api_interface] PlanningDispatchRecipientPreviewRead: PlanningDispatchRecipientPreviewRead includes field audience_code.
  - [typescript_api_interface] PlanningOutputDocumentRead: PlanningOutputDocumentRead includes field audience_code.
  - [typescript_api_interface] PlanningOutputGenerateRequest: PlanningOutputGenerateRequest includes field audience_code.
  - [backend_schema] PlanningOutputGenerateRequest: PlanningOutputGenerateRequest includes field audience_code.
  - [backend_schema] PlanningOutputDocumentRead: PlanningOutputDocumentRead includes field audience_code.
  - [backend_schema] PlanningDispatchRecipientPreviewRead: PlanningDispatchRecipientPreviewRead includes field audience_code.

## dispatch.dispatch_audience_employees

- canonical_name: dispatch_audience_employees
- module_key: planning
- page_id: P-05
- entity_type: Dispatch
- route_names: SicherPlanPlanningStaffing
- form_contexts: planning_outputs.dispatch, shift_release_to_employee_app, employee_assign_to_shift
- input_type: input
- required: False
- confidence: low
- labels_de: Zugewiesene Mitarbeiter
- labels_en: Assigned employees
- definition_de: Feld Zugewiesene Mitarbeiter im Kontext von Dispatch.
- definition_en: Assigned employees field used in the Dispatch context.
- related_fields: none
- aliases: dispatch_audience_employees, Assigned employees, Zugewiesene Mitarbeiter, Dispatch
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-05 manifest section planning_outputs.dispatch includes field dispatch_audience_employees labeled Assigned employees.
  - [page_help_manifest] Assistant Page Help Manifest: P-05 manifest section planning_outputs.dispatch includes field dispatch_audience_employees labeled Zugewiesene Mitarbeiter.

## dispatch.dispatch_audience_subcontractors

- canonical_name: dispatch_audience_subcontractors
- module_key: planning
- page_id: P-05
- entity_type: Dispatch
- route_names: SicherPlanPlanningStaffing
- form_contexts: planning_outputs.dispatch, shift_release_to_employee_app, employee_assign_to_shift
- input_type: input
- required: False
- confidence: low
- labels_de: Freigegebene Partner
- labels_en: Released subcontractors
- definition_de: Feld Freigegebene Partner im Kontext von Dispatch.
- definition_en: Released subcontractors field used in the Dispatch context.
- related_fields: none
- aliases: dispatch_audience_subcontractors, Released subcontractors, Freigegebene Partner, Dispatch
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-05 manifest section planning_outputs.dispatch includes field dispatch_audience_subcontractors labeled Released subcontractors.
  - [page_help_manifest] Assistant Page Help Manifest: P-05 manifest section planning_outputs.dispatch includes field dispatch_audience_subcontractors labeled Freigegebene Partner.

## dispatch.dispatch_recipients

- canonical_name: dispatch_recipients
- module_key: planning
- page_id: P-05
- entity_type: Dispatch
- route_names: SicherPlanPlanningStaffing
- form_contexts: planning_outputs.dispatch, shift_release_to_employee_app, employee_assign_to_shift
- input_type: input
- required: False
- confidence: low
- labels_de: Empfänger
- labels_en: Recipients
- definition_de: Feld Empfänger im Kontext von Dispatch.
- definition_en: Recipients field used in the Dispatch context.
- related_fields: none
- aliases: dispatch_recipients, Recipients, Empfänger, Dispatch
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-05 manifest section planning_outputs.dispatch includes field dispatch_recipients labeled Recipients.
  - [page_help_manifest] Assistant Page Help Manifest: P-05 manifest section planning_outputs.dispatch includes field dispatch_recipients labeled Empfänger.

## dispatch.file_name

- canonical_name: file_name
- module_key: planning
- page_id: P-05
- entity_type: Dispatch
- route_names: SicherPlanPlanningStaffing
- form_contexts: planning_outputs.documents, shift_release_to_employee_app, employee_assign_to_shift
- input_type: input
- required: False
- confidence: medium
- labels_de: Dateiname
- labels_en: File name
- definition_de: Feld Dateiname im Kontext von Dispatch.
- definition_en: File name field used in the Dispatch context.
- related_fields: none
- aliases: file_name, File name, Dateiname, Dispatch
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-05 manifest section planning_outputs.documents includes field file_name labeled File name.
  - [page_help_manifest] Assistant Page Help Manifest: P-05 manifest section planning_outputs.documents includes field file_name labeled Dateiname.
  - [typescript_api_interface] CustomerPortalDocumentRefRead: CustomerPortalDocumentRefRead includes field file_name.
  - [typescript_api_interface] CustomerHistoryAttachmentRead: CustomerHistoryAttachmentRead includes field file_name.
  - [typescript_api_interface] CustomerExportResult: CustomerExportResult includes field file_name.
  - [typescript_api_interface] CustomerVCardResult: CustomerVCardResult includes field file_name.
  - [typescript_api_interface] EmployeeDocumentListItemRead: EmployeeDocumentListItemRead includes field file_name.
  - [typescript_api_interface] EmployeeDocumentUploadPayload: EmployeeDocumentUploadPayload includes field file_name.

## dispatch.variant_code

- canonical_name: variant_code
- module_key: planning
- page_id: P-05
- entity_type: Dispatch
- route_names: SicherPlanPlanningStaffing
- form_contexts: planning_outputs.documents, shift_release_to_employee_app, employee_assign_to_shift
- input_type: input
- required: False
- confidence: medium
- labels_de: Variante
- labels_en: Variant
- definition_de: Feld Variante im Kontext von Dispatch.
- definition_en: Variant field used in the Dispatch context.
- related_fields: none
- aliases: variant_code, Variant, Variante, Dispatch
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-05 manifest section planning_outputs.documents includes field variant_code labeled Variant.
  - [page_help_manifest] Assistant Page Help Manifest: P-05 manifest section planning_outputs.documents includes field variant_code labeled Variante.
  - [typescript_api_interface] PlanningOutputDocumentRead: PlanningOutputDocumentRead includes field variant_code.
  - [typescript_api_interface] PlanningOutputGenerateRequest: PlanningOutputGenerateRequest includes field variant_code.
  - [backend_schema] PlanningOutputGenerateRequest: PlanningOutputGenerateRequest includes field variant_code.
  - [backend_schema] PlanningOutputDocumentRead: PlanningOutputDocumentRead includes field variant_code.

## document.document_title

- canonical_name: document_title
- module_key: platform_services
- page_id: PS-01
- entity_type: PlatformDocument
- route_names: SicherPlanPlatformServices
- form_contexts: platform_services.documents, contract_or_document_register
- input_type: input
- required: False
- confidence: medium
- labels_de: Dokumenttitel
- labels_en: Document title
- definition_de: Feld Dokumenttitel im Kontext von PlatformDocument.
- definition_en: Document title field used in the PlatformDocument context.
- related_fields: none
- aliases: document_title, Document title, Dokumenttitel, PlatformDocument
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: PS-01 manifest section platform_services.documents includes field document_title labeled Document title.
  - [page_help_manifest] Assistant Page Help Manifest: PS-01 manifest section platform_services.documents includes field document_title labeled Dokumenttitel.
  - [typescript_api_interface] ReportingDeliveryJob: ReportingDeliveryJob includes field document_title.
  - [backend_schema] ReportingDeliveryJobRead: ReportingDeliveryJobRead includes field document_title.

## document.document_version

- canonical_name: document_version
- module_key: platform_services
- page_id: PS-01
- entity_type: PlatformDocument
- route_names: SicherPlanPlatformServices
- form_contexts: platform_services.documents, contract_or_document_register
- input_type: input
- required: False
- confidence: low
- labels_de: Version
- labels_en: Version
- definition_de: Feld Version im Kontext von PlatformDocument.
- definition_en: Version field used in the PlatformDocument context.
- related_fields: none
- aliases: document_version, Version, PlatformDocument
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: PS-01 manifest section platform_services.documents includes field document_version labeled Version.
  - [page_help_manifest] Assistant Page Help Manifest: PS-01 manifest section platform_services.documents includes field document_version labeled Version.

## document.download

- canonical_name: download
- module_key: platform_services
- page_id: PS-01
- entity_type: PlatformDocument
- route_names: SicherPlanPlatformServices
- form_contexts: platform_services.links, contract_or_document_register
- input_type: input
- required: False
- confidence: low
- labels_de: Download
- labels_en: Download
- definition_de: Feld Download im Kontext von PlatformDocument.
- definition_en: Download field used in the PlatformDocument context.
- related_fields: none
- aliases: download, Download, PlatformDocument
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: PS-01 manifest section platform_services.links includes field download labeled Download.
  - [page_help_manifest] Assistant Page Help Manifest: PS-01 manifest section platform_services.links includes field download labeled Download.

## document.link_target

- canonical_name: link_target
- module_key: platform_services
- page_id: PS-01
- entity_type: PlatformDocument
- route_names: SicherPlanPlatformServices
- form_contexts: platform_services.links, contract_or_document_register
- input_type: input
- required: False
- confidence: low
- labels_de: Verknüpfungsziel
- labels_en: Link target
- definition_de: Feld Verknüpfungsziel im Kontext von PlatformDocument.
- definition_en: Link target field used in the PlatformDocument context.
- related_fields: none
- aliases: link_target, Link target, Verknüpfungsziel, PlatformDocument
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: PS-01 manifest section platform_services.links includes field link_target labeled Link target.
  - [page_help_manifest] Assistant Page Help Manifest: PS-01 manifest section platform_services.links includes field link_target labeled Verknüpfungsziel.

## document.owner_context

- canonical_name: owner_context
- module_key: platform_services
- page_id: PS-01
- entity_type: PlatformDocument
- route_names: SicherPlanPlatformServices
- form_contexts: platform_services.documents, contract_or_document_register
- input_type: input
- required: False
- confidence: low
- labels_de: Besitzender Fachkontext
- labels_en: Owning business context
- definition_de: Feld Besitzender Fachkontext im Kontext von PlatformDocument.
- definition_en: Owning business context field used in the PlatformDocument context.
- related_fields: none
- aliases: owner_context, Owning business context, Besitzender Fachkontext, PlatformDocument
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: PS-01 manifest section platform_services.documents includes field owner_context labeled Owning business context.
  - [page_help_manifest] Assistant Page Help Manifest: PS-01 manifest section platform_services.documents includes field owner_context labeled Besitzender Fachkontext.

## document.upload

- canonical_name: upload
- module_key: platform_services
- page_id: PS-01
- entity_type: PlatformDocument
- route_names: SicherPlanPlatformServices
- form_contexts: platform_services.links, contract_or_document_register
- input_type: input
- required: False
- confidence: low
- labels_de: Upload
- labels_en: Upload
- definition_de: Feld Upload im Kontext von PlatformDocument.
- definition_en: Upload field used in the PlatformDocument context.
- related_fields: none
- aliases: upload, Upload, PlatformDocument
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: PS-01 manifest section platform_services.links includes field upload labeled Upload.
  - [page_help_manifest] Assistant Page Help Manifest: PS-01 manifest section platform_services.links includes field upload labeled Upload.

## employee.absence_type

- canonical_name: absence_type
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Abwesenheitsart
- labels_en: Absence type
- definition_de: Feld Abwesenheitsart im Kontext von Employee.
- definition_en: Absence type field used in the Employee context.
- related_fields: none
- aliases: absence_type, employeeAdmin.fields.absenceType, absenceDraft.absence_type, Abwesenheitsart, Absence type, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.absenceType defines labels Absence type, Abwesenheitsart.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds absenceDraft.absence_type next to employeeAdmin.fields.absenceType.
  - [typescript_api_interface] EmployeeAbsenceRead: EmployeeAbsenceRead includes field absence_type.
  - [typescript_api_interface] EmployeeAbsenceCreatePayload: EmployeeAbsenceCreatePayload includes field absence_type.
  - [typescript_api_interface] EmployeeAbsenceUpdatePayload: EmployeeAbsenceUpdatePayload includes field absence_type.
  - [backend_schema] EmployeeAbsence: EmployeeAbsence includes field absence_type.
  - [backend_schema] EmployeeAbsenceFilter: EmployeeAbsenceFilter includes field absence_type.
  - [backend_schema] EmployeeAbsenceCreate: EmployeeAbsenceCreate includes field absence_type.

## employee.assign_group

- canonical_name: assign_group
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: medium
- labels_de: Gruppe zuordnen
- labels_en: Assign group
- definition_de: Feld Gruppe zuordnen im Kontext von Employee.
- definition_en: Assign group field used in the Employee context.
- related_fields: none
- aliases: assign_group, employeeAdmin.fields.assignGroup, membershipDraft.group_id, Gruppe zuordnen, Assign group, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.assignGroup defines labels Assign group, Gruppe zuordnen.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds membershipDraft.group_id next to employeeAdmin.fields.assignGroup.

## employee.bank_account_holder

- canonical_name: bank_account_holder
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Kontoinhaber
- labels_en: Bank account holder
- definition_de: Feld Kontoinhaber im Kontext von Employee.
- definition_en: Bank account holder field used in the Employee context.
- related_fields: none
- aliases: bank_account_holder, employeeAdmin.fields.bankAccountHolder, privateProfileDraft.bank_account_holder, Kontoinhaber, Bank account holder, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.bankAccountHolder defines labels Bank account holder, Kontoinhaber.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds privateProfileDraft.bank_account_holder next to employeeAdmin.fields.bankAccountHolder.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field bank_account_holder.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field bank_account_holder.
  - [typescript_api_interface] EmployeePrivateProfileRead: EmployeePrivateProfileRead includes field bank_account_holder.
  - [typescript_api_interface] EmployeePrivateProfileWritePayload: EmployeePrivateProfileWritePayload includes field bank_account_holder.
  - [typescript_api_interface] EmployeePrivateProfileUpdatePayload: EmployeePrivateProfileUpdatePayload includes field bank_account_holder.
  - [typescript_api_interface] SubcontractorFinanceProfileRead: SubcontractorFinanceProfileRead includes field bank_account_holder.

## employee.bank_bic

- canonical_name: bank_bic
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: BIC
- labels_en: Bank BIC
- definition_de: Feld BIC im Kontext von Employee.
- definition_en: Bank BIC field used in the Employee context.
- related_fields: none
- aliases: bank_bic, employeeAdmin.fields.bankBic, privateProfileDraft.bank_bic, BIC, Bank BIC, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.bankBic defines labels BIC, Bank BIC.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds privateProfileDraft.bank_bic next to employeeAdmin.fields.bankBic.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field bank_bic.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field bank_bic.
  - [typescript_api_interface] EmployeePrivateProfileRead: EmployeePrivateProfileRead includes field bank_bic.
  - [typescript_api_interface] EmployeePrivateProfileWritePayload: EmployeePrivateProfileWritePayload includes field bank_bic.
  - [typescript_api_interface] EmployeePrivateProfileUpdatePayload: EmployeePrivateProfileUpdatePayload includes field bank_bic.
  - [typescript_api_interface] SubcontractorFinanceProfileRead: SubcontractorFinanceProfileRead includes field bank_bic.

## employee.bank_iban

- canonical_name: bank_iban
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: IBAN
- labels_en: Bank IBAN
- definition_de: Feld IBAN im Kontext von Employee.
- definition_en: Bank IBAN field used in the Employee context.
- related_fields: none
- aliases: bank_iban, employeeAdmin.fields.bankIban, privateProfileDraft.bank_iban, IBAN, Bank IBAN, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.bankIban defines labels Bank IBAN, IBAN.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds privateProfileDraft.bank_iban next to employeeAdmin.fields.bankIban.
  - [typescript_api_interface] CustomerBillingProfileRead: CustomerBillingProfileRead includes field bank_iban.
  - [typescript_api_interface] CustomerBillingProfilePayload: CustomerBillingProfilePayload includes field bank_iban.
  - [typescript_api_interface] EmployeePrivateProfileRead: EmployeePrivateProfileRead includes field bank_iban.
  - [typescript_api_interface] EmployeePrivateProfileWritePayload: EmployeePrivateProfileWritePayload includes field bank_iban.
  - [typescript_api_interface] EmployeePrivateProfileUpdatePayload: EmployeePrivateProfileUpdatePayload includes field bank_iban.
  - [typescript_api_interface] SubcontractorFinanceProfileRead: SubcontractorFinanceProfileRead includes field bank_iban.

## employee.birth_date

- canonical_name: birth_date
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Geburtsdatum
- labels_en: Birth date
- definition_de: Feld Geburtsdatum im Kontext von Employee.
- definition_en: Birth date field used in the Employee context.
- related_fields: none
- aliases: birth_date, employeeAdmin.fields.birthDate, privateProfileDraft.birth_date, Geburtsdatum, Birth date, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.birthDate defines labels Birth date, Geburtsdatum.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds privateProfileDraft.birth_date next to employeeAdmin.fields.birthDate.
  - [typescript_api_interface] EmployeePrivateProfileRead: EmployeePrivateProfileRead includes field birth_date.
  - [typescript_api_interface] EmployeePrivateProfileWritePayload: EmployeePrivateProfileWritePayload includes field birth_date.
  - [typescript_api_interface] EmployeePrivateProfileUpdatePayload: EmployeePrivateProfileUpdatePayload includes field birth_date.
  - [typescript_api_interface] SubcontractorPortalWorkerCreate: SubcontractorPortalWorkerCreate includes field birth_date.
  - [typescript_api_interface] SubcontractorPortalWorkerUpdate: SubcontractorPortalWorkerUpdate includes field birth_date.
  - [typescript_api_interface] SubcontractorPortalWorkerRead: SubcontractorPortalWorkerRead includes field birth_date.

## employee.certificate_no

- canonical_name: certificate_no
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Zertifikatsnummer
- labels_en: Certificate number
- definition_de: Feld Zertifikatsnummer im Kontext von Employee.
- definition_en: Certificate number field used in the Employee context.
- related_fields: none
- aliases: certificate_no, employeeAdmin.fields.certificateNo, qualificationDraft.certificate_no, Zertifikatsnummer, Certificate number, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.certificateNo defines labels Certificate number, Zertifikatsnummer.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds qualificationDraft.certificate_no next to employeeAdmin.fields.certificateNo.
  - [typescript_api_interface] EmployeeQualificationRead: EmployeeQualificationRead includes field certificate_no.
  - [typescript_api_interface] EmployeeQualificationCreatePayload: EmployeeQualificationCreatePayload includes field certificate_no.
  - [typescript_api_interface] EmployeeQualificationUpdatePayload: EmployeeQualificationUpdatePayload includes field certificate_no.
  - [typescript_api_interface] SubcontractorPortalWorkerQualificationCreate: SubcontractorPortalWorkerQualificationCreate includes field certificate_no.
  - [typescript_api_interface] SubcontractorPortalWorkerQualificationUpdate: SubcontractorPortalWorkerQualificationUpdate includes field certificate_no.
  - [typescript_api_interface] SubcontractorWorkerQualificationRead: SubcontractorWorkerQualificationRead includes field certificate_no.

## employee.completed_at

- canonical_name: completed_at
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: textarea
- required: unknown
- confidence: high
- labels_de: Erledigt am
- labels_en: Completed on
- definition_de: Feld Erledigt am im Kontext von Employee.
- definition_en: Completed on field used in the Employee context.
- related_fields: none
- aliases: completed_at, employeeAdmin.fields.completedAt, noteDraft.completed_at, Erledigt am, Completed on, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.completedAt defines labels Completed on, Erledigt am.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds noteDraft.completed_at next to employeeAdmin.fields.completedAt.
  - [typescript_api_interface] EmployeeNoteRead: EmployeeNoteRead includes field completed_at.
  - [typescript_api_interface] ReportingDeliveryJob: ReportingDeliveryJob includes field completed_at.
  - [backend_schema] EmployeeNote: EmployeeNote includes field completed_at.
  - [backend_schema] EmployeeNoteUpdate: EmployeeNoteUpdate includes field completed_at.
  - [backend_schema] EmployeeNoteRead: EmployeeNoteRead includes field completed_at.
  - [backend_schema] PatrolRound: PatrolRound includes field completed_at.

## employee.credential_no

- canonical_name: credential_no
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Ausweisnummer
- labels_en: Credential number
- definition_de: Feld Ausweisnummer im Kontext von Employee.
- definition_en: Credential number field used in the Employee context.
- related_fields: none
- aliases: credential_no, employeeAdmin.fields.credentialNo, credentialDraft.credential_no, Ausweisnummer, Credential number, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.credentialNo defines labels Ausweisnummer, Credential number.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds credentialDraft.credential_no next to employeeAdmin.fields.credentialNo.
  - [typescript_api_interface] EmployeeCredentialRead: EmployeeCredentialRead includes field credential_no.
  - [typescript_api_interface] EmployeeCredentialCreatePayload: EmployeeCredentialCreatePayload includes field credential_no.
  - [typescript_api_interface] SubcontractorWorkerCredentialRead: SubcontractorWorkerCredentialRead includes field credential_no.
  - [backend_schema] EmployeeIdCredential: EmployeeIdCredential includes field credential_no.
  - [backend_schema] EmployeeCredentialCreate: EmployeeCredentialCreate includes field credential_no.
  - [backend_schema] EmployeeCredentialRead: EmployeeCredentialRead includes field credential_no.

## employee.credential_type

- canonical_name: credential_type
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Ausweistyp
- labels_en: Credential type
- definition_de: Feld Ausweistyp im Kontext von Employee.
- definition_en: Credential type field used in the Employee context.
- related_fields: none
- aliases: credential_type, employeeAdmin.fields.credentialType, credentialDraft.credential_type, Ausweistyp, Credential type, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.credentialType defines labels Ausweistyp, Credential type.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds credentialDraft.credential_type next to employeeAdmin.fields.credentialType.
  - [typescript_api_interface] EmployeeCredentialRead: EmployeeCredentialRead includes field credential_type.
  - [typescript_api_interface] EmployeeCredentialCreatePayload: EmployeeCredentialCreatePayload includes field credential_type.
  - [typescript_api_interface] SubcontractorWorkerCredentialRead: SubcontractorWorkerCredentialRead includes field credential_type.
  - [backend_schema] EmployeeIdCredential: EmployeeIdCredential includes field credential_type.
  - [backend_schema] EmployeeCredentialFilter: EmployeeCredentialFilter includes field credential_type.
  - [backend_schema] EmployeeCredentialCreate: EmployeeCredentialCreate includes field credential_type.

## employee.decision_note

- canonical_name: decision_note
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: textarea
- required: unknown
- confidence: high
- labels_de: Entscheidungsnotiz
- labels_en: Decision note
- definition_de: Feld Entscheidungsnotiz im Kontext von Employee.
- definition_en: Decision note field used in the Employee context.
- related_fields: none
- aliases: decision_note, employeeAdmin.fields.decisionNote, absenceDraft.decision_note, Entscheidungsnotiz, Decision note, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.decisionNote defines labels Decision note, Entscheidungsnotiz.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds absenceDraft.decision_note next to employeeAdmin.fields.decisionNote.
  - [typescript_api_interface] EmployeeAbsenceRead: EmployeeAbsenceRead includes field decision_note.
  - [typescript_api_interface] EmployeeAbsenceUpdatePayload: EmployeeAbsenceUpdatePayload includes field decision_note.
  - [backend_schema] EmployeeAbsence: EmployeeAbsence includes field decision_note.
  - [backend_schema] EmployeeEventApplication: EmployeeEventApplication includes field decision_note.
  - [backend_schema] EmployeeAbsenceUpdate: EmployeeAbsenceUpdate includes field decision_note.
  - [backend_schema] EmployeeAbsenceRead: EmployeeAbsenceRead includes field decision_note.

## employee.default_branch_id

- canonical_name: default_branch_id
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Standardniederlassung
- labels_en: Default branch
- definition_de: Feld Standardniederlassung im Kontext von Employee.
- definition_en: Default branch field used in the Employee context.
- related_fields: none
- aliases: default_branch_id, employeeAdmin.fields.defaultBranchId, advancedFilterDraft.default_branch_id, Standardniederlassung, Default branch, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.defaultBranchId defines labels Default branch, Standardniederlassung.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds advancedFilterDraft.default_branch_id next to employeeAdmin.fields.defaultBranchId.
  - [typescript_api_interface] CustomerListItem: CustomerListItem includes field default_branch_id.
  - [typescript_api_interface] CustomerFilterParams: CustomerFilterParams includes field default_branch_id.
  - [typescript_api_interface] CustomerCreatePayload: CustomerCreatePayload includes field default_branch_id.
  - [typescript_api_interface] EmployeeListItem: EmployeeListItem includes field default_branch_id.
  - [typescript_api_interface] EmployeeListFilters: EmployeeListFilters includes field default_branch_id.
  - [backend_schema] Customer: Customer includes field default_branch_id.

## employee.default_mandate_id

- canonical_name: default_mandate_id
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Standardmandat
- labels_en: Default mandate
- definition_de: Feld Standardmandat im Kontext von Employee.
- definition_en: Default mandate field used in the Employee context.
- related_fields: none
- aliases: default_mandate_id, employeeAdmin.fields.defaultMandateId, advancedFilterDraft.default_mandate_id, Standardmandat, Default mandate, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.defaultMandateId defines labels Default mandate, Standardmandat.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds advancedFilterDraft.default_mandate_id next to employeeAdmin.fields.defaultMandateId.
  - [typescript_api_interface] CustomerFilterParams: CustomerFilterParams includes field default_mandate_id.
  - [typescript_api_interface] CustomerCreatePayload: CustomerCreatePayload includes field default_mandate_id.
  - [typescript_api_interface] EmployeeListItem: EmployeeListItem includes field default_mandate_id.
  - [typescript_api_interface] EmployeeListFilters: EmployeeListFilters includes field default_mandate_id.
  - [backend_schema] Customer: Customer includes field default_mandate_id.
  - [backend_schema] CustomerFilter: CustomerFilter includes field default_mandate_id.

## employee.document_file

- canonical_name: document_file
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: unknown
- required: unknown
- confidence: low
- labels_de: Datei
- labels_en: File
- definition_de: Feld Datei im Kontext von Employee.
- definition_en: File field used in the Employee context.
- related_fields: none
- aliases: document_file, employeeAdmin.fields.documentFile, Datei, File, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.documentFile defines labels Datei, File.

## employee.document_id

- canonical_name: document_id
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: True
- confidence: high
- labels_de: Dokument-ID
- labels_en: Document ID
- definition_de: Feld Dokument-ID im Kontext von Employee.
- definition_en: Document ID field used in the Employee context.
- related_fields: none
- aliases: document_id, employeeAdmin.fields.documentId, documentLinkDraft.document_id, Dokument-ID, Document ID, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.documentId defines labels Document ID, Dokument-ID.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds documentLinkDraft.document_id next to employeeAdmin.fields.documentId.
  - [typescript_api_interface] CustomerPortalDocumentRefRead: CustomerPortalDocumentRefRead includes field document_id.
  - [typescript_api_interface] CustomerHistoryAttachmentRead: CustomerHistoryAttachmentRead includes field document_id.
  - [typescript_api_interface] CustomerHistoryAttachmentLinkPayload: CustomerHistoryAttachmentLinkPayload includes field document_id.
  - [typescript_api_interface] CustomerExportResult: CustomerExportResult includes field document_id.
  - [typescript_api_interface] CustomerVCardResult: CustomerVCardResult includes field document_id.
  - [typescript_api_interface] EmployeeDocumentListItemRead: EmployeeDocumentListItemRead includes field document_id.

## employee.document_label

- canonical_name: document_label
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: medium
- labels_de: Bezeichnung
- labels_en: Label
- definition_de: Feld Bezeichnung im Kontext von Employee.
- definition_en: Label field used in the Employee context.
- related_fields: none
- aliases: document_label, employeeAdmin.fields.documentLabel, documentUploadDraft.label, Bezeichnung, Label, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.documentLabel defines labels Bezeichnung, Label.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds documentUploadDraft.label next to employeeAdmin.fields.documentLabel.

## employee.document_relation_type

- canonical_name: document_relation_type
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: medium
- labels_de: Dokumentrelation
- labels_en: Document relation
- definition_de: Feld Dokumentrelation im Kontext von Employee.
- definition_en: Document relation field used in the Employee context.
- related_fields: none
- aliases: document_relation_type, employeeAdmin.fields.documentRelationType, documentUploadDraft.relation_type, Dokumentrelation, Document relation, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.documentRelationType defines labels Document relation, Dokumentrelation.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds documentUploadDraft.relation_type next to employeeAdmin.fields.documentRelationType.

## employee.document_title

- canonical_name: document_title
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Dokumenttitel
- labels_en: Document title
- definition_de: Feld Dokumenttitel im Kontext von Employee.
- definition_en: Document title field used in the Employee context.
- related_fields: none
- aliases: document_title, employeeAdmin.fields.documentTitle, qualificationProofDraft.title, Dokumenttitel, Document title, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.documentTitle defines labels Document title, Dokumenttitel.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds qualificationProofDraft.title next to employeeAdmin.fields.documentTitle.
  - [typescript_api_interface] ReportingDeliveryJob: ReportingDeliveryJob includes field document_title.
  - [backend_schema] ReportingDeliveryJobRead: ReportingDeliveryJobRead includes field document_title.

## employee.document_type_key

- canonical_name: document_type_key
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Dokumenttyp
- labels_en: Document type
- definition_de: Feld Dokumenttyp im Kontext von Employee.
- definition_en: Document type field used in the Employee context.
- related_fields: none
- aliases: document_type_key, employeeAdmin.fields.documentTypeKey, documentUploadDraft.document_type_key, Dokumenttyp, Document type, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.documentTypeKey defines labels Document type, Dokumenttyp.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds documentUploadDraft.document_type_key next to employeeAdmin.fields.documentTypeKey.
  - [typescript_api_interface] CustomerPortalDocumentRefRead: CustomerPortalDocumentRefRead includes field document_type_key.
  - [typescript_api_interface] CustomerHistoryAttachmentRead: CustomerHistoryAttachmentRead includes field document_type_key.
  - [typescript_api_interface] EmployeeDocumentListItemRead: EmployeeDocumentListItemRead includes field document_type_key.
  - [typescript_api_interface] EmployeeDocumentUploadPayload: EmployeeDocumentUploadPayload includes field document_type_key.
  - [typescript_api_interface] ApplicantAttachmentRead: ApplicantAttachmentRead includes field document_type_key.
  - [typescript_api_interface] SubcontractorWorkerQualificationProofRead: SubcontractorWorkerQualificationProofRead includes field document_type_key.

## employee.document_version_target

- canonical_name: document_version_target
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: medium
- labels_de: Version zu Dokument
- labels_en: Version target document
- definition_de: Feld Version zu Dokument im Kontext von Employee.
- definition_en: Version target document field used in the Employee context.
- related_fields: none
- aliases: document_version_target, employeeAdmin.fields.documentVersionTarget, selectedEmployeeDocumentId, Version zu Dokument, Version target document, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.documentVersionTarget defines labels Version target document, Version zu Dokument.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds selectedEmployeeDocumentId next to employeeAdmin.fields.documentVersionTarget.

## employee.emergency_contact_name

- canonical_name: emergency_contact_name
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Notfallkontakt
- labels_en: Emergency contact name
- definition_de: Feld Notfallkontakt im Kontext von Employee.
- definition_en: Emergency contact name field used in the Employee context.
- related_fields: none
- aliases: emergency_contact_name, employeeAdmin.fields.emergencyContactName, privateProfileDraft.emergency_contact_name, Notfallkontakt, Emergency contact name, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.emergencyContactName defines labels Emergency contact name, Notfallkontakt.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds privateProfileDraft.emergency_contact_name next to employeeAdmin.fields.emergencyContactName.
  - [typescript_api_interface] EmployeePrivateProfileRead: EmployeePrivateProfileRead includes field emergency_contact_name.
  - [typescript_api_interface] EmployeePrivateProfileWritePayload: EmployeePrivateProfileWritePayload includes field emergency_contact_name.
  - [typescript_api_interface] EmployeePrivateProfileUpdatePayload: EmployeePrivateProfileUpdatePayload includes field emergency_contact_name.
  - [backend_schema] EmployeePrivateProfile: EmployeePrivateProfile includes field emergency_contact_name.
  - [backend_schema] EmployeePrivateProfileCreate: EmployeePrivateProfileCreate includes field emergency_contact_name.
  - [backend_schema] EmployeePrivateProfileUpdate: EmployeePrivateProfileUpdate includes field emergency_contact_name.

## employee.emergency_contact_phone

- canonical_name: emergency_contact_phone
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Telefon Notfallkontakt
- labels_en: Emergency contact phone
- definition_de: Feld Telefon Notfallkontakt im Kontext von Employee.
- definition_en: Emergency contact phone field used in the Employee context.
- related_fields: none
- aliases: emergency_contact_phone, employeeAdmin.fields.emergencyContactPhone, privateProfileDraft.emergency_contact_phone, Telefon Notfallkontakt, Emergency contact phone, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.emergencyContactPhone defines labels Emergency contact phone, Telefon Notfallkontakt.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds privateProfileDraft.emergency_contact_phone next to employeeAdmin.fields.emergencyContactPhone.
  - [typescript_api_interface] EmployeePrivateProfileRead: EmployeePrivateProfileRead includes field emergency_contact_phone.
  - [typescript_api_interface] EmployeePrivateProfileWritePayload: EmployeePrivateProfileWritePayload includes field emergency_contact_phone.
  - [typescript_api_interface] EmployeePrivateProfileUpdatePayload: EmployeePrivateProfileUpdatePayload includes field emergency_contact_phone.
  - [backend_schema] EmployeePrivateProfile: EmployeePrivateProfile includes field emergency_contact_phone.
  - [backend_schema] EmployeePrivateProfileCreate: EmployeePrivateProfileCreate includes field emergency_contact_phone.
  - [backend_schema] EmployeePrivateProfileUpdate: EmployeePrivateProfileUpdate includes field emergency_contact_phone.

## employee.employment_type_code

- canonical_name: employment_type_code
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Beschäftigungsart
- labels_en: Employment type
- definition_de: Feld Beschäftigungsart im Kontext von Employee.
- definition_en: Employment type field used in the Employee context.
- related_fields: none
- aliases: employment_type_code, employeeAdmin.fields.employmentTypeCode, employeeDraft.employment_type_code, Beschäftigungsart, Employment type, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.employmentTypeCode defines labels Beschäftigungsart, Employment type.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds employeeDraft.employment_type_code next to employeeAdmin.fields.employmentTypeCode.
  - [typescript_api_interface] PayrollTariffRateRead: PayrollTariffRateRead includes field employment_type_code.
  - [typescript_api_interface] PayrollSurchargeRuleRead: PayrollSurchargeRuleRead includes field employment_type_code.
  - [typescript_api_interface] EmployeePayProfileRead: EmployeePayProfileRead includes field employment_type_code.
  - [backend_schema] Employee: Employee includes field employment_type_code.
  - [backend_schema] EmployeeOperationalCreate: EmployeeOperationalCreate includes field employment_type_code.
  - [backend_schema] EmployeeOperationalUpdate: EmployeeOperationalUpdate includes field employment_type_code.

## employee.encoded_value

- canonical_name: encoded_value
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Kodierter Wert
- labels_en: Encoded value
- definition_de: Feld Kodierter Wert im Kontext von Employee.
- definition_en: Encoded value field used in the Employee context.
- related_fields: none
- aliases: encoded_value, employeeAdmin.fields.encodedValue, credentialDraft.encoded_value, Kodierter Wert, Encoded value, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.encodedValue defines labels Encoded value, Kodierter Wert.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds credentialDraft.encoded_value next to employeeAdmin.fields.encodedValue.
  - [typescript_api_interface] EmployeeCredentialRead: EmployeeCredentialRead includes field encoded_value.
  - [typescript_api_interface] EmployeeCredentialCreatePayload: EmployeeCredentialCreatePayload includes field encoded_value.
  - [typescript_api_interface] EmployeeCredentialUpdatePayload: EmployeeCredentialUpdatePayload includes field encoded_value.
  - [typescript_api_interface] SubcontractorWorkerCredentialRead: SubcontractorWorkerCredentialRead includes field encoded_value.
  - [backend_schema] EmployeeIdCredential: EmployeeIdCredential includes field encoded_value.
  - [backend_schema] EmployeeCredentialCreate: EmployeeCredentialCreate includes field encoded_value.

## employee.ends_at

- canonical_name: ends_at
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Endet am
- labels_en: Ends at
- definition_de: Feld Endet am im Kontext von Employee.
- definition_en: Ends at field used in the Employee context.
- related_fields: none
- aliases: ends_at, employeeAdmin.fields.endsAt, availabilityDraft.ends_at, Endet am, Ends at, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.endsAt defines labels Endet am, Ends at.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds availabilityDraft.ends_at next to employeeAdmin.fields.endsAt.
  - [typescript_api_interface] CustomerDashboardCalendarItemRead: CustomerDashboardCalendarItemRead includes field ends_at.
  - [typescript_api_interface] EmployeeAvailabilityRuleRead: EmployeeAvailabilityRuleRead includes field ends_at.
  - [typescript_api_interface] EmployeeAvailabilityRuleCreatePayload: EmployeeAvailabilityRuleCreatePayload includes field ends_at.
  - [typescript_api_interface] EmployeeAvailabilityRuleUpdatePayload: EmployeeAvailabilityRuleUpdatePayload includes field ends_at.
  - [typescript_api_interface] ShiftListItem: ShiftListItem includes field ends_at.
  - [typescript_api_interface] PlanningBoardShiftListItem: PlanningBoardShiftListItem includes field ends_at.

## employee.ends_on

- canonical_name: ends_on
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Endet am
- labels_en: Ends on
- definition_de: Feld Endet am im Kontext von Employee.
- definition_en: Ends on field used in the Employee context.
- related_fields: none
- aliases: ends_on, employeeAdmin.fields.endsOn, absenceDraft.ends_on, Endet am, Ends on, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.endsOn defines labels Endet am, Ends on.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds absenceDraft.ends_on next to employeeAdmin.fields.endsOn.
  - [typescript_api_interface] EmployeeAbsenceRead: EmployeeAbsenceRead includes field ends_on.
  - [typescript_api_interface] EmployeeAbsenceCreatePayload: EmployeeAbsenceCreatePayload includes field ends_on.
  - [typescript_api_interface] EmployeeAbsenceUpdatePayload: EmployeeAbsenceUpdatePayload includes field ends_on.
  - [backend_schema] EmployeeAbsence: EmployeeAbsence includes field ends_on.
  - [backend_schema] EmployeeAbsenceCreate: EmployeeAbsenceCreate includes field ends_on.
  - [backend_schema] EmployeeAbsenceUpdate: EmployeeAbsenceUpdate includes field ends_on.

## employee.first_name

- canonical_name: first_name
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: SicherPlanEmployees
- form_contexts: employee.identity
- input_type: input
- required: True
- confidence: high
- labels_de: Vorname
- labels_en: First name
- definition_de: Feld Vorname im Kontext von Employee.
- definition_en: First name field used in the Employee context.
- related_fields: none
- aliases: first_name, First name, Vorname, employeeAdmin.fields.firstName, employeeDraft.first_name, Employee
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: E-01 manifest section employee.identity includes field first_name labeled First name.
  - [page_help_manifest] Assistant Page Help Manifest: E-01 manifest section employee.identity includes field first_name labeled Vorname.
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.firstName defines labels First name, Vorname.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds employeeDraft.first_name next to employeeAdmin.fields.firstName.
  - [typescript_api_interface] EmployeeListItem: EmployeeListItem includes field first_name.
  - [typescript_api_interface] ApplicantListItem: ApplicantListItem includes field first_name.
  - [typescript_api_interface] RecruitingApplicantSubmissionPayload: RecruitingApplicantSubmissionPayload includes field first_name.
  - [typescript_api_interface] SubcontractorWorkerListItem: SubcontractorWorkerListItem includes field first_name.

## employee.function_type

- canonical_name: function_type
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Funktionstyp
- labels_en: Function type
- definition_de: Feld Funktionstyp im Kontext von Employee.
- definition_en: Function type field used in the Employee context.
- related_fields: none
- aliases: function_type, employeeAdmin.fields.functionType, qualificationDraft.function_type_id, Funktionstyp, Function type, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.functionType defines labels Function type, Funktionstyp.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds qualificationDraft.function_type_id next to employeeAdmin.fields.functionType.
  - [typescript_api_interface] CustomerRateLineRead: CustomerRateLineRead includes field function_type.
  - [typescript_api_interface] EmployeeQualificationRead: EmployeeQualificationRead includes field function_type.
  - [backend_schema] CustomerRateLine: CustomerRateLine includes field function_type.
  - [backend_schema] CustomerRateLineRead: CustomerRateLineRead includes field function_type.
  - [backend_schema] EmployeeQualification: EmployeeQualification includes field function_type.
  - [backend_schema] EmployeeAllowance: EmployeeAllowance includes field function_type.

## employee.granted_internally

- canonical_name: granted_internally
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: unknown
- required: unknown
- confidence: medium
- labels_de: Intern vergeben
- labels_en: Granted internally
- definition_de: Feld Intern vergeben im Kontext von Employee.
- definition_en: Granted internally field used in the Employee context.
- related_fields: none
- aliases: granted_internally, employeeAdmin.fields.grantedInternally, Intern vergeben, Granted internally, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.grantedInternally defines labels Granted internally, Intern vergeben.
  - [typescript_api_interface] EmployeeQualificationRead: EmployeeQualificationRead includes field granted_internally.
  - [typescript_api_interface] EmployeeQualificationCreatePayload: EmployeeQualificationCreatePayload includes field granted_internally.
  - [typescript_api_interface] EmployeeQualificationUpdatePayload: EmployeeQualificationUpdatePayload includes field granted_internally.
  - [backend_schema] EmployeeQualification: EmployeeQualification includes field granted_internally.
  - [backend_schema] EmployeeQualificationCreate: EmployeeQualificationCreate includes field granted_internally.
  - [backend_schema] EmployeeQualificationUpdate: EmployeeQualificationUpdate includes field granted_internally.
  - [backend_schema] EmployeeQualificationRead: EmployeeQualificationRead includes field granted_internally.

## employee.group_code

- canonical_name: group_code
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: medium
- labels_de: Gruppencode
- labels_en: Group code
- definition_de: Feld Gruppencode im Kontext von Employee.
- definition_en: Group code field used in the Employee context.
- related_fields: none
- aliases: group_code, employeeAdmin.fields.groupCode, groupDraft.code, Gruppencode, Group code, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.groupCode defines labels Group code, Gruppencode.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds groupDraft.code next to employeeAdmin.fields.groupCode.

## employee.group_description

- canonical_name: group_description
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: medium
- labels_de: Gruppenbeschreibung
- labels_en: Group description
- definition_de: Feld Gruppenbeschreibung im Kontext von Employee.
- definition_en: Group description field used in the Employee context.
- related_fields: none
- aliases: group_description, employeeAdmin.fields.groupDescription, groupDraft.description, Gruppenbeschreibung, Group description, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.groupDescription defines labels Group description, Gruppenbeschreibung.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds groupDraft.description next to employeeAdmin.fields.groupDescription.

## employee.group_name

- canonical_name: group_name
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: medium
- labels_de: Gruppenname
- labels_en: Group name
- definition_de: Feld Gruppenname im Kontext von Employee.
- definition_en: Group name field used in the Employee context.
- related_fields: none
- aliases: group_name, employeeAdmin.fields.groupName, groupDraft.name, Gruppenname, Group name, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.groupName defines labels Group name, Gruppenname.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds groupDraft.name next to employeeAdmin.fields.groupName.

## employee.hire_date

- canonical_name: hire_date
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Eintrittsdatum
- labels_en: Hire date
- definition_de: Feld Eintrittsdatum im Kontext von Employee.
- definition_en: Hire date field used in the Employee context.
- related_fields: none
- aliases: hire_date, employeeAdmin.fields.hireDate, employeeDraft.hire_date, Eintrittsdatum, Hire date, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.hireDate defines labels Eintrittsdatum, Hire date.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds employeeDraft.hire_date next to employeeAdmin.fields.hireDate.
  - [typescript_api_interface] EmployeeListItem: EmployeeListItem includes field hire_date.
  - [backend_schema] Employee: Employee includes field hire_date.
  - [backend_schema] EmployeeOperationalCreate: EmployeeOperationalCreate includes field hire_date.
  - [backend_schema] EmployeeOperationalUpdate: EmployeeOperationalUpdate includes field hire_date.
  - [backend_schema] EmployeeListItem: EmployeeListItem includes field hire_date.
  - [backend_schema] EmployeeActivityReportRow: EmployeeActivityReportRow includes field hire_date.

## employee.issued_at

- canonical_name: issued_at
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Ausgestellt am
- labels_en: Issued on
- definition_de: Feld Ausgestellt am im Kontext von Employee.
- definition_en: Issued on field used in the Employee context.
- related_fields: none
- aliases: issued_at, employeeAdmin.fields.issuedAt, qualificationDraft.issued_at, Ausgestellt am, Issued on, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.issuedAt defines labels Ausgestellt am, Issued on.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds qualificationDraft.issued_at next to employeeAdmin.fields.issuedAt.
  - [typescript_api_interface] CurrentSessionResponse: CurrentSessionResponse includes field issued_at.
  - [typescript_api_interface] EmployeeQualificationRead: EmployeeQualificationRead includes field issued_at.
  - [typescript_api_interface] EmployeeQualificationCreatePayload: EmployeeQualificationCreatePayload includes field issued_at.
  - [typescript_api_interface] EmployeeQualificationUpdatePayload: EmployeeQualificationUpdatePayload includes field issued_at.
  - [typescript_api_interface] EmployeeCredentialRead: EmployeeCredentialRead includes field issued_at.
  - [typescript_api_interface] FinanceBillingInvoiceRead: FinanceBillingInvoiceRead includes field issued_at.

## employee.issuing_authority

- canonical_name: issuing_authority
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: textarea
- required: unknown
- confidence: high
- labels_de: Ausstellende Stelle
- labels_en: Issuing authority
- definition_de: Feld Ausstellende Stelle im Kontext von Employee.
- definition_en: Issuing authority field used in the Employee context.
- related_fields: none
- aliases: issuing_authority, employeeAdmin.fields.issuingAuthority, qualificationDraft.issuing_authority, Ausstellende Stelle, Issuing authority, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.issuingAuthority defines labels Ausstellende Stelle, Issuing authority.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds qualificationDraft.issuing_authority next to employeeAdmin.fields.issuingAuthority.
  - [typescript_api_interface] EmployeeQualificationRead: EmployeeQualificationRead includes field issuing_authority.
  - [typescript_api_interface] EmployeeQualificationCreatePayload: EmployeeQualificationCreatePayload includes field issuing_authority.
  - [typescript_api_interface] EmployeeQualificationUpdatePayload: EmployeeQualificationUpdatePayload includes field issuing_authority.
  - [typescript_api_interface] SubcontractorPortalWorkerQualificationCreate: SubcontractorPortalWorkerQualificationCreate includes field issuing_authority.
  - [typescript_api_interface] SubcontractorPortalWorkerQualificationUpdate: SubcontractorPortalWorkerQualificationUpdate includes field issuing_authority.
  - [typescript_api_interface] SubcontractorWorkerQualificationRead: SubcontractorWorkerQualificationRead includes field issuing_authority.

## employee.last_name

- canonical_name: last_name
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: SicherPlanEmployees
- form_contexts: employee.identity
- input_type: input
- required: True
- confidence: high
- labels_de: Nachname
- labels_en: Last name
- definition_de: Feld Nachname im Kontext von Employee.
- definition_en: Last name field used in the Employee context.
- related_fields: none
- aliases: last_name, Last name, Nachname, employeeAdmin.fields.lastName, employeeDraft.last_name, Employee
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: E-01 manifest section employee.identity includes field last_name labeled Last name.
  - [page_help_manifest] Assistant Page Help Manifest: E-01 manifest section employee.identity includes field last_name labeled Nachname.
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.lastName defines labels Last name, Nachname.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds employeeDraft.last_name next to employeeAdmin.fields.lastName.
  - [typescript_api_interface] EmployeeListItem: EmployeeListItem includes field last_name.
  - [typescript_api_interface] ApplicantListItem: ApplicantListItem includes field last_name.
  - [typescript_api_interface] RecruitingApplicantSubmissionPayload: RecruitingApplicantSubmissionPayload includes field last_name.
  - [typescript_api_interface] SubcontractorWorkerListItem: SubcontractorWorkerListItem includes field last_name.

## employee.marital_status

- canonical_name: marital_status
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: medium
- labels_de: Familienstand
- labels_en: Marital status
- definition_de: Feld Familienstand im Kontext von Employee.
- definition_en: Marital status field used in the Employee context.
- related_fields: none
- aliases: marital_status, employeeAdmin.fields.maritalStatus, privateProfileDraft.marital_status_code, Familienstand, Marital status, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.maritalStatus defines labels Familienstand, Marital status.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds privateProfileDraft.marital_status_code next to employeeAdmin.fields.maritalStatus.

## employee.membership_notes

- canonical_name: membership_notes
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: medium
- labels_de: Zuordnungsnotiz
- labels_en: Assignment notes
- definition_de: Feld Zuordnungsnotiz im Kontext von Employee.
- definition_en: Assignment notes field used in the Employee context.
- related_fields: none
- aliases: membership_notes, employeeAdmin.fields.membershipNotes, membershipDraft.notes, Zuordnungsnotiz, Assignment notes, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.membershipNotes defines labels Assignment notes, Zuordnungsnotiz.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds membershipDraft.notes next to employeeAdmin.fields.membershipNotes.

## employee.mobile_phone

- canonical_name: mobile_phone
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Mobilnummer
- labels_en: Mobile phone
- definition_de: Feld Mobilnummer im Kontext von Employee.
- definition_en: Mobile phone field used in the Employee context.
- related_fields: none
- aliases: mobile_phone, employeeAdmin.fields.mobilePhone, employeeDraft.mobile_phone, Mobilnummer, Mobile phone, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.mobilePhone defines labels Mobile phone, Mobilnummer.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds employeeDraft.mobile_phone next to employeeAdmin.fields.mobilePhone.
  - [typescript_api_interface] EmployeeListItem: EmployeeListItem includes field mobile_phone.
  - [backend_schema] Employee: Employee includes field mobile_phone.
  - [backend_schema] EmployeeOperationalCreate: EmployeeOperationalCreate includes field mobile_phone.
  - [backend_schema] EmployeeOperationalUpdate: EmployeeOperationalUpdate includes field mobile_phone.
  - [backend_schema] EmployeeListItem: EmployeeListItem includes field mobile_phone.
  - [backend_schema] EmployeeSelfServiceProfileRead: EmployeeSelfServiceProfileRead includes field mobile_phone.

## employee.nationality_country_code

- canonical_name: nationality_country_code
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Nationalität-Ländercode
- labels_en: Nationality country code
- definition_de: Feld Nationalität-Ländercode im Kontext von Employee.
- definition_en: Nationality country code field used in the Employee context.
- related_fields: none
- aliases: nationality_country_code, employeeAdmin.fields.nationalityCountryCode, privateProfileDraft.nationality_country_code, Nationalität-Ländercode, Nationality country code, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.nationalityCountryCode defines labels Nationality country code, Nationalität-Ländercode.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds privateProfileDraft.nationality_country_code next to employeeAdmin.fields.nationalityCountryCode.
  - [typescript_api_interface] EmployeePrivateProfileRead: EmployeePrivateProfileRead includes field nationality_country_code.
  - [typescript_api_interface] EmployeePrivateProfileWritePayload: EmployeePrivateProfileWritePayload includes field nationality_country_code.
  - [typescript_api_interface] EmployeePrivateProfileUpdatePayload: EmployeePrivateProfileUpdatePayload includes field nationality_country_code.
  - [backend_schema] EmployeePrivateProfile: EmployeePrivateProfile includes field nationality_country_code.
  - [backend_schema] EmployeePrivateProfileCreate: EmployeePrivateProfileCreate includes field nationality_country_code.
  - [backend_schema] EmployeePrivateProfileUpdate: EmployeePrivateProfileUpdate includes field nationality_country_code.

## employee.note_body

- canonical_name: note_body
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: textarea
- required: unknown
- confidence: medium
- labels_de: Inhalt
- labels_en: Content
- definition_de: Feld Inhalt im Kontext von Employee.
- definition_en: Content field used in the Employee context.
- related_fields: none
- aliases: note_body, employeeAdmin.fields.noteBody, noteDraft.body, Inhalt, Content, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.noteBody defines labels Content, Inhalt.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds noteDraft.body next to employeeAdmin.fields.noteBody.

## employee.note_title

- canonical_name: note_title
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: True
- confidence: medium
- labels_de: Notiztitel
- labels_en: Note title
- definition_de: Feld Notiztitel im Kontext von Employee.
- definition_en: Note title field used in the Employee context.
- related_fields: none
- aliases: note_title, employeeAdmin.fields.noteTitle, noteDraft.title, Notiztitel, Note title, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.noteTitle defines labels Note title, Notiztitel.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds noteDraft.title next to employeeAdmin.fields.noteTitle.

## employee.note_type

- canonical_name: note_type
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Notiztyp
- labels_en: Note type
- definition_de: Feld Notiztyp im Kontext von Employee.
- definition_en: Note type field used in the Employee context.
- related_fields: none
- aliases: note_type, employeeAdmin.fields.noteType, noteDraft.note_type, Notiztyp, Note type, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.noteType defines labels Note type, Notiztyp.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds noteDraft.note_type next to employeeAdmin.fields.noteType.
  - [typescript_api_interface] EmployeeNoteRead: EmployeeNoteRead includes field note_type.
  - [backend_schema] EmployeeNote: EmployeeNote includes field note_type.
  - [backend_schema] EmployeeNoteCreate: EmployeeNoteCreate includes field note_type.
  - [backend_schema] EmployeeNoteRead: EmployeeNoteRead includes field note_type.

## employee.notes

- canonical_name: notes
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: textarea
- required: unknown
- confidence: high
- labels_de: Operative Notizen
- labels_en: Operational notes
- definition_de: Feld Operative Notizen im Kontext von Employee.
- definition_en: Operational notes field used in the Employee context.
- related_fields: none
- aliases: notes, employeeAdmin.fields.notes, employeeDraft.notes, Operative Notizen, Operational notes, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.notes defines labels Operational notes, Operative Notizen.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds employeeDraft.notes next to employeeAdmin.fields.notes.
  - [typescript_api_interface] MandateRead: MandateRead includes field notes.
  - [typescript_api_interface] TenantOnboardingPayload: TenantOnboardingPayload includes field notes.
  - [typescript_api_interface] MandateCreatePayload: MandateCreatePayload includes field notes.
  - [typescript_api_interface] MandateUpdatePayload: MandateUpdatePayload includes field notes.
  - [typescript_api_interface] CustomerContactRead: CustomerContactRead includes field notes.
  - [typescript_api_interface] CustomerRateLineRead: CustomerRateLineRead includes field notes.

## employee.personnel_no

- canonical_name: personnel_no
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: SicherPlanEmployees
- form_contexts: employee.identity
- input_type: input
- required: True
- confidence: high
- labels_de: Personalnummer
- labels_en: Personnel number
- definition_de: Feld Personalnummer im Kontext von Employee.
- definition_en: Personnel number field used in the Employee context.
- related_fields: none
- aliases: personnel_no, Personnel number, Personalnummer, employeeAdmin.fields.personnelNo, employeeDraft.personnel_no, Employee
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: E-01 manifest section employee.identity includes field personnel_no labeled Personnel number.
  - [page_help_manifest] Assistant Page Help Manifest: E-01 manifest section employee.identity includes field personnel_no labeled Personalnummer.
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.personnelNo defines labels Personalnummer, Personnel number.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds employeeDraft.personnel_no next to employeeAdmin.fields.personnelNo.
  - [typescript_api_interface] EmployeeListItem: EmployeeListItem includes field personnel_no.
  - [typescript_api_interface] EmployeeImportRowResult: EmployeeImportRowResult includes field personnel_no.
  - [backend_schema] AssistantEmployeeSearchMatchRead: AssistantEmployeeSearchMatchRead includes field personnel_no.
  - [backend_schema] AssistantEmployeeOperationalProfileItemRead: AssistantEmployeeOperationalProfileItemRead includes field personnel_no.

## employee.place_of_birth

- canonical_name: place_of_birth
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Geburtsort
- labels_en: Place of birth
- definition_de: Feld Geburtsort im Kontext von Employee.
- definition_en: Place of birth field used in the Employee context.
- related_fields: none
- aliases: place_of_birth, employeeAdmin.fields.placeOfBirth, privateProfileDraft.place_of_birth, Geburtsort, Place of birth, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.placeOfBirth defines labels Geburtsort, Place of birth.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds privateProfileDraft.place_of_birth next to employeeAdmin.fields.placeOfBirth.
  - [typescript_api_interface] EmployeePrivateProfileRead: EmployeePrivateProfileRead includes field place_of_birth.
  - [typescript_api_interface] EmployeePrivateProfileWritePayload: EmployeePrivateProfileWritePayload includes field place_of_birth.
  - [typescript_api_interface] EmployeePrivateProfileUpdatePayload: EmployeePrivateProfileUpdatePayload includes field place_of_birth.
  - [backend_schema] EmployeePrivateProfile: EmployeePrivateProfile includes field place_of_birth.
  - [backend_schema] EmployeePrivateProfileCreate: EmployeePrivateProfileCreate includes field place_of_birth.
  - [backend_schema] EmployeePrivateProfileUpdate: EmployeePrivateProfileUpdate includes field place_of_birth.

## employee.preferred_name

- canonical_name: preferred_name
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: True
- confidence: high
- labels_de: Rufname
- labels_en: Preferred name
- definition_de: Feld Rufname im Kontext von Employee.
- definition_en: Preferred name field used in the Employee context.
- related_fields: none
- aliases: preferred_name, employeeAdmin.fields.preferredName, employeeDraft.preferred_name, Rufname, Preferred name, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.preferredName defines labels Preferred name, Rufname.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds employeeDraft.preferred_name next to employeeAdmin.fields.preferredName.
  - [typescript_api_interface] EmployeeListItem: EmployeeListItem includes field preferred_name.
  - [typescript_api_interface] SubcontractorWorkerListItem: SubcontractorWorkerListItem includes field preferred_name.
  - [typescript_api_interface] SubcontractorPortalWorkerCreate: SubcontractorPortalWorkerCreate includes field preferred_name.
  - [typescript_api_interface] SubcontractorPortalWorkerUpdate: SubcontractorPortalWorkerUpdate includes field preferred_name.
  - [typescript_api_interface] SubcontractorPortalWorkerRead: SubcontractorPortalWorkerRead includes field preferred_name.
  - [typescript_api_interface] SubcontractorWorkerReadinessListItem: SubcontractorWorkerReadinessListItem includes field preferred_name.

## employee.private_email

- canonical_name: private_email
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Private E-Mail
- labels_en: Private email
- definition_de: Feld Private E-Mail im Kontext von Employee.
- definition_en: Private email field used in the Employee context.
- related_fields: none
- aliases: private_email, employeeAdmin.fields.privateEmail, privateProfileDraft.private_email, Private E-Mail, Private email, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.privateEmail defines labels Private E-Mail, Private email.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds privateProfileDraft.private_email next to employeeAdmin.fields.privateEmail.
  - [typescript_api_interface] EmployeePrivateProfileRead: EmployeePrivateProfileRead includes field private_email.
  - [typescript_api_interface] EmployeePrivateProfileWritePayload: EmployeePrivateProfileWritePayload includes field private_email.
  - [typescript_api_interface] EmployeePrivateProfileUpdatePayload: EmployeePrivateProfileUpdatePayload includes field private_email.
  - [backend_schema] EmployeePrivateProfile: EmployeePrivateProfile includes field private_email.
  - [backend_schema] EmployeePrivateProfileCreate: EmployeePrivateProfileCreate includes field private_email.
  - [backend_schema] EmployeePrivateProfileUpdate: EmployeePrivateProfileUpdate includes field private_email.

## employee.private_phone

- canonical_name: private_phone
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Privattelefon
- labels_en: Private phone
- definition_de: Feld Privattelefon im Kontext von Employee.
- definition_en: Private phone field used in the Employee context.
- related_fields: none
- aliases: private_phone, employeeAdmin.fields.privatePhone, privateProfileDraft.private_phone, Privattelefon, Private phone, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.privatePhone defines labels Private phone, Privattelefon.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds privateProfileDraft.private_phone next to employeeAdmin.fields.privatePhone.
  - [typescript_api_interface] EmployeePrivateProfileRead: EmployeePrivateProfileRead includes field private_phone.
  - [typescript_api_interface] EmployeePrivateProfileWritePayload: EmployeePrivateProfileWritePayload includes field private_phone.
  - [typescript_api_interface] EmployeePrivateProfileUpdatePayload: EmployeePrivateProfileUpdatePayload includes field private_phone.
  - [backend_schema] EmployeePrivateProfile: EmployeePrivateProfile includes field private_phone.
  - [backend_schema] EmployeePrivateProfileCreate: EmployeePrivateProfileCreate includes field private_phone.
  - [backend_schema] EmployeePrivateProfileUpdate: EmployeePrivateProfileUpdate includes field private_phone.

## employee.proof_file

- canonical_name: proof_file
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: unknown
- required: unknown
- confidence: low
- labels_de: Nachweisdatei
- labels_en: Proof file
- definition_de: Feld Nachweisdatei im Kontext von Employee.
- definition_en: Proof file field used in the Employee context.
- related_fields: none
- aliases: proof_file, employeeAdmin.fields.proofFile, Nachweisdatei, Proof file, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.proofFile defines labels Nachweisdatei, Proof file.

## employee.qualification_type

- canonical_name: qualification_type
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Qualifikationstyp
- labels_en: Qualification type
- definition_de: Feld Qualifikationstyp im Kontext von Employee.
- definition_en: Qualification type field used in the Employee context.
- related_fields: none
- aliases: qualification_type, employeeAdmin.fields.qualificationType, qualificationDraft.qualification_type_id, Qualifikationstyp, Qualification type, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.qualificationType defines labels Qualification type, Qualifikationstyp.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds qualificationDraft.qualification_type_id next to employeeAdmin.fields.qualificationType.
  - [typescript_api_interface] CustomerRateLineRead: CustomerRateLineRead includes field qualification_type.
  - [typescript_api_interface] EmployeeQualificationRead: EmployeeQualificationRead includes field qualification_type.
  - [backend_schema] CustomerRateLine: CustomerRateLine includes field qualification_type.
  - [backend_schema] CustomerRateLineRead: CustomerRateLineRead includes field qualification_type.
  - [backend_schema] EmployeeQualification: EmployeeQualification includes field qualification_type.
  - [backend_schema] EmployeeAllowance: EmployeeAllowance includes field qualification_type.

## employee.record_kind

- canonical_name: record_kind
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Eintragstyp
- labels_en: Record kind
- definition_de: Feld Eintragstyp im Kontext von Employee.
- definition_en: Record kind field used in the Employee context.
- related_fields: none
- aliases: record_kind, employeeAdmin.fields.recordKind, qualificationDraft.record_kind, Eintragstyp, Record kind, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.recordKind defines labels Eintragstyp, Record kind.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds qualificationDraft.record_kind next to employeeAdmin.fields.recordKind.
  - [typescript_api_interface] EmployeeQualificationRead: EmployeeQualificationRead includes field record_kind.
  - [typescript_api_interface] EmployeeQualificationCreatePayload: EmployeeQualificationCreatePayload includes field record_kind.
  - [backend_schema] EmployeeQualification: EmployeeQualification includes field record_kind.
  - [backend_schema] EmployeeQualificationFilter: EmployeeQualificationFilter includes field record_kind.
  - [backend_schema] EmployeeQualificationCreate: EmployeeQualificationCreate includes field record_kind.
  - [backend_schema] EmployeeQualificationRead: EmployeeQualificationRead includes field record_kind.

## employee.recurrence_type

- canonical_name: recurrence_type
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Wiederholung
- labels_en: Recurrence
- definition_de: Feld Wiederholung im Kontext von Employee.
- definition_en: Recurrence field used in the Employee context.
- related_fields: none
- aliases: recurrence_type, employeeAdmin.fields.recurrenceType, availabilityDraft.recurrence_type, Wiederholung, Recurrence, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.recurrenceType defines labels Recurrence, Wiederholung.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds availabilityDraft.recurrence_type next to employeeAdmin.fields.recurrenceType.
  - [typescript_api_interface] EmployeeAvailabilityRuleRead: EmployeeAvailabilityRuleRead includes field recurrence_type.
  - [typescript_api_interface] EmployeeAvailabilityRuleCreatePayload: EmployeeAvailabilityRuleCreatePayload includes field recurrence_type.
  - [typescript_api_interface] EmployeeAvailabilityRuleUpdatePayload: EmployeeAvailabilityRuleUpdatePayload includes field recurrence_type.
  - [backend_schema] EmployeeAvailabilityRule: EmployeeAvailabilityRule includes field recurrence_type.
  - [backend_schema] EmployeeAvailabilityRuleCreate: EmployeeAvailabilityRuleCreate includes field recurrence_type.
  - [backend_schema] EmployeeAvailabilityRuleUpdate: EmployeeAvailabilityRuleUpdate includes field recurrence_type.

## employee.reminder_at

- canonical_name: reminder_at
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Erinnerungsdatum
- labels_en: Reminder date
- definition_de: Feld Erinnerungsdatum im Kontext von Employee.
- definition_en: Reminder date field used in the Employee context.
- related_fields: none
- aliases: reminder_at, employeeAdmin.fields.reminderAt, noteDraft.reminder_at, Erinnerungsdatum, Reminder date, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.reminderAt defines labels Erinnerungsdatum, Reminder date.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds noteDraft.reminder_at next to employeeAdmin.fields.reminderAt.
  - [typescript_api_interface] EmployeeNoteRead: EmployeeNoteRead includes field reminder_at.
  - [backend_schema] EmployeeNote: EmployeeNote includes field reminder_at.
  - [backend_schema] EmployeeNoteCreate: EmployeeNoteCreate includes field reminder_at.
  - [backend_schema] EmployeeNoteUpdate: EmployeeNoteUpdate includes field reminder_at.
  - [backend_schema] EmployeeNoteRead: EmployeeNoteRead includes field reminder_at.

## employee.rule_kind

- canonical_name: rule_kind
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Regelart
- labels_en: Rule kind
- definition_de: Feld Regelart im Kontext von Employee.
- definition_en: Rule kind field used in the Employee context.
- related_fields: none
- aliases: rule_kind, employeeAdmin.fields.ruleKind, availabilityDraft.rule_kind, Regelart, Rule kind, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.ruleKind defines labels Regelart, Rule kind.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds availabilityDraft.rule_kind next to employeeAdmin.fields.ruleKind.
  - [typescript_api_interface] EmployeeAvailabilityRuleRead: EmployeeAvailabilityRuleRead includes field rule_kind.
  - [typescript_api_interface] EmployeeAvailabilityRuleCreatePayload: EmployeeAvailabilityRuleCreatePayload includes field rule_kind.
  - [typescript_api_interface] EmployeeAvailabilityRuleUpdatePayload: EmployeeAvailabilityRuleUpdatePayload includes field rule_kind.
  - [backend_schema] EmployeeAvailabilityRule: EmployeeAvailabilityRule includes field rule_kind.
  - [backend_schema] EmployeeAvailabilityRuleFilter: EmployeeAvailabilityRuleFilter includes field rule_kind.
  - [backend_schema] EmployeeAvailabilityRuleCreate: EmployeeAvailabilityRuleCreate includes field rule_kind.

## employee.social_security_no

- canonical_name: social_security_no
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Sozialversicherungsnummer
- labels_en: Social security number
- definition_de: Feld Sozialversicherungsnummer im Kontext von Employee.
- definition_en: Social security number field used in the Employee context.
- related_fields: none
- aliases: social_security_no, employeeAdmin.fields.socialSecurityNo, privateProfileDraft.social_security_no, Sozialversicherungsnummer, Social security number, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.socialSecurityNo defines labels Social security number, Sozialversicherungsnummer.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds privateProfileDraft.social_security_no next to employeeAdmin.fields.socialSecurityNo.
  - [typescript_api_interface] EmployeePrivateProfileRead: EmployeePrivateProfileRead includes field social_security_no.
  - [typescript_api_interface] EmployeePrivateProfileWritePayload: EmployeePrivateProfileWritePayload includes field social_security_no.
  - [typescript_api_interface] EmployeePrivateProfileUpdatePayload: EmployeePrivateProfileUpdatePayload includes field social_security_no.
  - [backend_schema] EmployeePrivateProfile: EmployeePrivateProfile includes field social_security_no.
  - [backend_schema] EmployeePrivateProfileCreate: EmployeePrivateProfileCreate includes field social_security_no.
  - [backend_schema] EmployeePrivateProfileUpdate: EmployeePrivateProfileUpdate includes field social_security_no.

## employee.starts_at

- canonical_name: starts_at
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Beginnt am
- labels_en: Starts at
- definition_de: Feld Beginnt am im Kontext von Employee.
- definition_en: Starts at field used in the Employee context.
- related_fields: none
- aliases: starts_at, employeeAdmin.fields.startsAt, availabilityDraft.starts_at, Beginnt am, Starts at, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.startsAt defines labels Beginnt am, Starts at.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds availabilityDraft.starts_at next to employeeAdmin.fields.startsAt.
  - [typescript_api_interface] CustomerDashboardCalendarItemRead: CustomerDashboardCalendarItemRead includes field starts_at.
  - [typescript_api_interface] EmployeeAvailabilityRuleRead: EmployeeAvailabilityRuleRead includes field starts_at.
  - [typescript_api_interface] EmployeeAvailabilityRuleCreatePayload: EmployeeAvailabilityRuleCreatePayload includes field starts_at.
  - [typescript_api_interface] EmployeeAvailabilityRuleUpdatePayload: EmployeeAvailabilityRuleUpdatePayload includes field starts_at.
  - [typescript_api_interface] ShiftListItem: ShiftListItem includes field starts_at.
  - [typescript_api_interface] PlanningBoardShiftListItem: PlanningBoardShiftListItem includes field starts_at.

## employee.starts_on

- canonical_name: starts_on
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Beginnt am
- labels_en: Starts on
- definition_de: Feld Beginnt am im Kontext von Employee.
- definition_en: Starts on field used in the Employee context.
- related_fields: none
- aliases: starts_on, employeeAdmin.fields.startsOn, absenceDraft.starts_on, Beginnt am, Starts on, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.startsOn defines labels Beginnt am, Starts on.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds absenceDraft.starts_on next to employeeAdmin.fields.startsOn.
  - [typescript_api_interface] EmployeeAbsenceRead: EmployeeAbsenceRead includes field starts_on.
  - [typescript_api_interface] EmployeeAbsenceCreatePayload: EmployeeAbsenceCreatePayload includes field starts_on.
  - [typescript_api_interface] EmployeeAbsenceUpdatePayload: EmployeeAbsenceUpdatePayload includes field starts_on.
  - [backend_schema] EmployeeAbsence: EmployeeAbsence includes field starts_on.
  - [backend_schema] EmployeeAbsenceCreate: EmployeeAbsenceCreate includes field starts_on.
  - [backend_schema] EmployeeAbsenceUpdate: EmployeeAbsenceUpdate includes field starts_on.

## employee.status

- canonical_name: status
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Status
- labels_en: Status
- definition_de: Feld Status im Kontext von Employee.
- definition_en: Status field used in the Employee context.
- related_fields: none
- aliases: status, employeeAdmin.fields.status, employeeDraft.status, Status, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.status defines labels Status, Status.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds employeeDraft.status next to employeeAdmin.fields.status.
  - [typescript_api_interface] AssistantConversation: AssistantConversation includes field status.
  - [typescript_api_interface] CustomerPortalAccessListItem: CustomerPortalAccessListItem includes field status.
  - [typescript_api_interface] CustomerPortalAccessCreatePayload: CustomerPortalAccessCreatePayload includes field status.
  - [typescript_api_interface] CustomerPortalAccessStatusPayload: CustomerPortalAccessStatusPayload includes field status.
  - [typescript_api_interface] TenantListItem: TenantListItem includes field status.
  - [typescript_api_interface] TenantAdminUserListItem: TenantAdminUserListItem includes field status.

## employee.target_monthly_hours

- canonical_name: target_monthly_hours
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: number
- required: unknown
- confidence: high
- labels_de: Monats-Sollstunden
- labels_en: Target monthly hours
- definition_de: Feld Monats-Sollstunden im Kontext von Employee.
- definition_en: Target monthly hours field used in the Employee context.
- related_fields: none
- aliases: target_monthly_hours, employeeAdmin.fields.targetMonthlyHours, employeeDraft.target_monthly_hours, Monats-Sollstunden, Target monthly hours, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.targetMonthlyHours defines labels Monats-Sollstunden, Target monthly hours.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds employeeDraft.target_monthly_hours next to employeeAdmin.fields.targetMonthlyHours.
  - [backend_schema] Employee: Employee includes field target_monthly_hours.
  - [backend_schema] EmployeeOperationalCreate: EmployeeOperationalCreate includes field target_monthly_hours.
  - [backend_schema] EmployeeOperationalUpdate: EmployeeOperationalUpdate includes field target_monthly_hours.
  - [backend_schema] EmployeeOperationalRead: EmployeeOperationalRead includes field target_monthly_hours.

## employee.target_weekly_hours

- canonical_name: target_weekly_hours
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: number
- required: unknown
- confidence: high
- labels_de: Wochen-Sollstunden
- labels_en: Target weekly hours
- definition_de: Feld Wochen-Sollstunden im Kontext von Employee.
- definition_en: Target weekly hours field used in the Employee context.
- related_fields: none
- aliases: target_weekly_hours, employeeAdmin.fields.targetWeeklyHours, employeeDraft.target_weekly_hours, Wochen-Sollstunden, Target weekly hours, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.targetWeeklyHours defines labels Target weekly hours, Wochen-Sollstunden.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds employeeDraft.target_weekly_hours next to employeeAdmin.fields.targetWeeklyHours.
  - [backend_schema] Employee: Employee includes field target_weekly_hours.
  - [backend_schema] EmployeeOperationalCreate: EmployeeOperationalCreate includes field target_weekly_hours.
  - [backend_schema] EmployeeOperationalUpdate: EmployeeOperationalUpdate includes field target_weekly_hours.
  - [backend_schema] EmployeeOperationalRead: EmployeeOperationalRead includes field target_weekly_hours.

## employee.tax_id

- canonical_name: tax_id
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Steuer-ID
- labels_en: Tax ID
- definition_de: Feld Steuer-ID im Kontext von Employee.
- definition_en: Tax ID field used in the Employee context.
- related_fields: none
- aliases: tax_id, employeeAdmin.fields.taxId, privateProfileDraft.tax_id, Steuer-ID, Tax ID, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.taxId defines labels Steuer-ID, Tax ID.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds privateProfileDraft.tax_id next to employeeAdmin.fields.taxId.
  - [typescript_api_interface] EmployeePrivateProfileRead: EmployeePrivateProfileRead includes field tax_id.
  - [typescript_api_interface] EmployeePrivateProfileWritePayload: EmployeePrivateProfileWritePayload includes field tax_id.
  - [typescript_api_interface] EmployeePrivateProfileUpdatePayload: EmployeePrivateProfileUpdatePayload includes field tax_id.
  - [backend_schema] EmployeePrivateProfile: EmployeePrivateProfile includes field tax_id.
  - [backend_schema] EmployeePrivateProfileCreate: EmployeePrivateProfileCreate includes field tax_id.
  - [backend_schema] EmployeePrivateProfileUpdate: EmployeePrivateProfileUpdate includes field tax_id.

## employee.termination_date

- canonical_name: termination_date
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: select
- required: unknown
- confidence: high
- labels_de: Austrittsdatum
- labels_en: Termination date
- definition_de: Feld Austrittsdatum im Kontext von Employee.
- definition_en: Termination date field used in the Employee context.
- related_fields: none
- aliases: termination_date, employeeAdmin.fields.terminationDate, employeeDraft.termination_date, Austrittsdatum, Termination date, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.terminationDate defines labels Austrittsdatum, Termination date.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds employeeDraft.termination_date next to employeeAdmin.fields.terminationDate.
  - [typescript_api_interface] EmployeeListItem: EmployeeListItem includes field termination_date.
  - [backend_schema] Employee: Employee includes field termination_date.
  - [backend_schema] EmployeeOperationalCreate: EmployeeOperationalCreate includes field termination_date.
  - [backend_schema] EmployeeOperationalUpdate: EmployeeOperationalUpdate includes field termination_date.
  - [backend_schema] EmployeeListItem: EmployeeListItem includes field termination_date.
  - [backend_schema] EmployeeActivityReportRow: EmployeeActivityReportRow includes field termination_date.

## employee.user_id

- canonical_name: user_id
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: unknown
- required: unknown
- confidence: medium
- labels_de: Benutzerkonto-ID
- labels_en: User account ID
- definition_de: Feld Benutzerkonto-ID im Kontext von Employee.
- definition_en: User account ID field used in the Employee context.
- related_fields: none
- aliases: user_id, employeeAdmin.fields.userId, Benutzerkonto-ID, User account ID, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.userId defines labels Benutzerkonto-ID, User account ID.
  - [typescript_api_interface] CustomerPortalAccessListItem: CustomerPortalAccessListItem includes field user_id.
  - [typescript_api_interface] CustomerPortalContextRead: CustomerPortalContextRead includes field user_id.
  - [typescript_api_interface] SubcontractorPortalContextRead: SubcontractorPortalContextRead includes field user_id.
  - [typescript_api_interface] CustomerContactRead: CustomerContactRead includes field user_id.
  - [typescript_api_interface] CustomerContactPayload: CustomerContactPayload includes field user_id.
  - [typescript_api_interface] EmployeeAccessLinkRead: EmployeeAccessLinkRead includes field user_id.
  - [typescript_api_interface] SubcontractorContactRead: SubcontractorContactRead includes field user_id.

## employee.valid_from

- canonical_name: valid_from
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Gültig ab
- labels_en: Valid from
- definition_de: Feld Gültig ab im Kontext von Employee.
- definition_en: Valid from field used in the Employee context.
- related_fields: none
- aliases: valid_from, employeeAdmin.fields.validFrom, credentialDraft.valid_from, Gültig ab, Valid from, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.validFrom defines labels Gültig ab, Valid from.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds credentialDraft.valid_from next to employeeAdmin.fields.validFrom.
  - [typescript_api_interface] EmployeeGroupMembershipRead: EmployeeGroupMembershipRead includes field valid_from.
  - [typescript_api_interface] EmployeeAddressHistoryRead: EmployeeAddressHistoryRead includes field valid_from.
  - [typescript_api_interface] EmployeeAddressHistoryCreatePayload: EmployeeAddressHistoryCreatePayload includes field valid_from.
  - [typescript_api_interface] EmployeeAddressHistoryUpdatePayload: EmployeeAddressHistoryUpdatePayload includes field valid_from.
  - [typescript_api_interface] EmployeeCredentialRead: EmployeeCredentialRead includes field valid_from.
  - [typescript_api_interface] EmployeeCredentialCreatePayload: EmployeeCredentialCreatePayload includes field valid_from.

## employee.valid_until

- canonical_name: valid_until
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Gültig bis
- labels_en: Valid until
- definition_de: Feld Gültig bis im Kontext von Employee.
- definition_en: Valid until field used in the Employee context.
- related_fields: none
- aliases: valid_until, employeeAdmin.fields.validUntil, qualificationDraft.valid_until, Gültig bis, Valid until, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.validUntil defines labels Gültig bis, Valid until.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds qualificationDraft.valid_until next to employeeAdmin.fields.validUntil.
  - [typescript_api_interface] EmployeeGroupMembershipRead: EmployeeGroupMembershipRead includes field valid_until.
  - [typescript_api_interface] EmployeeQualificationRead: EmployeeQualificationRead includes field valid_until.
  - [typescript_api_interface] EmployeeQualificationCreatePayload: EmployeeQualificationCreatePayload includes field valid_until.
  - [typescript_api_interface] EmployeeQualificationUpdatePayload: EmployeeQualificationUpdatePayload includes field valid_until.
  - [typescript_api_interface] EmployeeCredentialRead: EmployeeCredentialRead includes field valid_until.
  - [typescript_api_interface] EmployeeCredentialCreatePayload: EmployeeCredentialCreatePayload includes field valid_until.

## employee.weekdays

- canonical_name: weekdays
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: unknown
- required: unknown
- confidence: low
- labels_de: Wochentage
- labels_en: Weekdays
- definition_de: Feld Wochentage im Kontext von Employee.
- definition_en: Weekdays field used in the Employee context.
- related_fields: none
- aliases: weekdays, employeeAdmin.fields.weekdays, Wochentage, Weekdays, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.weekdays defines labels Weekdays, Wochentage.

## employee.work_email

- canonical_name: work_email
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Dienst-E-Mail
- labels_en: Work email
- definition_de: Feld Dienst-E-Mail im Kontext von Employee.
- definition_en: Work email field used in the Employee context.
- related_fields: none
- aliases: work_email, employeeAdmin.fields.workEmail, employeeDraft.work_email, Dienst-E-Mail, Work email, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.workEmail defines labels Dienst-E-Mail, Work email.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds employeeDraft.work_email next to employeeAdmin.fields.workEmail.
  - [typescript_api_interface] EmployeeListItem: EmployeeListItem includes field work_email.
  - [backend_schema] Employee: Employee includes field work_email.
  - [backend_schema] EmployeeOperationalCreate: EmployeeOperationalCreate includes field work_email.
  - [backend_schema] EmployeeOperationalUpdate: EmployeeOperationalUpdate includes field work_email.
  - [backend_schema] EmployeeListItem: EmployeeListItem includes field work_email.
  - [backend_schema] EmployeeSelfServiceProfileRead: EmployeeSelfServiceProfileRead includes field work_email.

## employee.work_phone

- canonical_name: work_phone
- module_key: employees
- page_id: E-01
- entity_type: Employee
- route_names: none
- form_contexts: none
- input_type: text
- required: unknown
- confidence: high
- labels_de: Diensttelefon
- labels_en: Work phone
- definition_de: Feld Diensttelefon im Kontext von Employee.
- definition_en: Work phone field used in the Employee context.
- related_fields: none
- aliases: work_phone, employeeAdmin.fields.workPhone, employeeDraft.work_phone, Diensttelefon, Work phone, Employee
- source_basis:
  - [frontend_locale] messages.ts / sicherplan.json: employeeAdmin.fields.workPhone defines labels Diensttelefon, Work phone.
  - [frontend_component] EmployeeAdminView.vue: EmployeeAdminView.vue binds employeeDraft.work_phone next to employeeAdmin.fields.workPhone.
  - [backend_schema] Employee: Employee includes field work_phone.
  - [backend_schema] EmployeeOperationalCreate: EmployeeOperationalCreate includes field work_phone.
  - [backend_schema] EmployeeOperationalUpdate: EmployeeOperationalUpdate includes field work_phone.
  - [backend_schema] EmployeeOperationalRead: EmployeeOperationalRead includes field work_phone.

## planning_record.customer

- canonical_name: customer
- module_key: planning
- page_id: P-02
- entity_type: PlanningRecord
- route_names: SicherPlanPlanningOrders
- form_contexts: planning_orders.order_scope, customer_order_create, customer_plan_create, contract_or_document_register
- input_type: input
- required: True
- confidence: medium
- labels_de: Kunde
- labels_en: Customer
- definition_de: Feld Kunde im Kontext von PlanningRecord.
- definition_en: Customer field used in the PlanningRecord context.
- related_fields: none
- aliases: customer, Customer, Kunde, PlanningRecord
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-02 manifest section planning_orders.order_scope includes field customer labeled Customer.
  - [page_help_manifest] Assistant Page Help Manifest: P-02 manifest section planning_orders.order_scope includes field customer labeled Kunde.
  - [backend_schema] CustomerContact: CustomerContact includes field customer.
  - [backend_schema] CustomerBillingProfile: CustomerBillingProfile includes field customer.
  - [backend_schema] CustomerInvoiceParty: CustomerInvoiceParty includes field customer.
  - [backend_schema] CustomerAddressLink: CustomerAddressLink includes field customer.
  - [backend_schema] CustomerRateCard: CustomerRateCard includes field customer.
  - [backend_schema] CustomerHistoryEntry: CustomerHistoryEntry includes field customer.

## planning_record.date_window

- canonical_name: date_window
- module_key: planning
- page_id: P-02
- entity_type: PlanningRecord
- route_names: SicherPlanPlanningOrders
- form_contexts: planning_orders.order_scope, customer_order_create, customer_plan_create, contract_or_document_register
- input_type: input
- required: False
- confidence: low
- labels_de: Datumsfenster
- labels_en: Date window
- definition_de: Feld Datumsfenster im Kontext von PlanningRecord.
- definition_en: Date window field used in the PlanningRecord context.
- related_fields: none
- aliases: date_window, Date window, Datumsfenster, PlanningRecord
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-02 manifest section planning_orders.order_scope includes field date_window labeled Date window.
  - [page_help_manifest] Assistant Page Help Manifest: P-02 manifest section planning_orders.order_scope includes field date_window labeled Datumsfenster.

## planning_record.equipment_lines

- canonical_name: equipment_lines
- module_key: planning
- page_id: P-02
- entity_type: PlanningRecord
- route_names: SicherPlanPlanningOrders
- form_contexts: planning_orders.requirements, customer_order_create, customer_plan_create, contract_or_document_register
- input_type: input
- required: False
- confidence: medium
- labels_de: Equipment-Zeilen
- labels_en: Equipment lines
- definition_de: Feld Equipment-Zeilen im Kontext von PlanningRecord.
- definition_en: Equipment lines field used in the PlanningRecord context.
- related_fields: none
- aliases: equipment_lines, Equipment lines, Equipment-Zeilen, PlanningRecord
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-02 manifest section planning_orders.requirements includes field equipment_lines labeled Equipment lines.
  - [page_help_manifest] Assistant Page Help Manifest: P-02 manifest section planning_orders.requirements includes field equipment_lines labeled Equipment-Zeilen.
  - [backend_schema] CustomerOrder: CustomerOrder includes field equipment_lines.
  - [backend_schema] CustomerOrderRead: CustomerOrderRead includes field equipment_lines.

## planning_record.order_documents

- canonical_name: order_documents
- module_key: planning
- page_id: P-02
- entity_type: PlanningRecord
- route_names: SicherPlanPlanningOrders
- form_contexts: planning_orders.requirements, customer_order_create, customer_plan_create, contract_or_document_register
- input_type: input
- required: False
- confidence: low
- labels_de: Auftragsdokumente
- labels_en: Order documents
- definition_de: Feld Auftragsdokumente im Kontext von PlanningRecord.
- definition_en: Order documents field used in the PlanningRecord context.
- related_fields: none
- aliases: order_documents, Order documents, Auftragsdokumente, PlanningRecord
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-02 manifest section planning_orders.requirements includes field order_documents labeled Order documents.
  - [page_help_manifest] Assistant Page Help Manifest: P-02 manifest section planning_orders.requirements includes field order_documents labeled Auftragsdokumente.

## planning_record.planning_documents

- canonical_name: planning_documents
- module_key: planning
- page_id: P-02
- entity_type: PlanningRecord
- route_names: SicherPlanPlanningOrders
- form_contexts: planning_orders.requirements, customer_order_create, customer_plan_create, contract_or_document_register
- input_type: input
- required: False
- confidence: low
- labels_de: Planungsdokumente
- labels_en: Planning documents
- definition_de: Feld Planungsdokumente im Kontext von PlanningRecord.
- definition_en: Planning documents field used in the PlanningRecord context.
- related_fields: none
- aliases: planning_documents, Planning documents, Planungsdokumente, PlanningRecord
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-02 manifest section planning_orders.requirements includes field planning_documents labeled Planning documents.
  - [page_help_manifest] Assistant Page Help Manifest: P-02 manifest section planning_orders.requirements includes field planning_documents labeled Planungsdokumente.

## planning_record.requirement_lines

- canonical_name: requirement_lines
- module_key: planning
- page_id: P-02
- entity_type: PlanningRecord
- route_names: SicherPlanPlanningOrders
- form_contexts: planning_orders.requirements, customer_order_create, customer_plan_create, contract_or_document_register
- input_type: input
- required: False
- confidence: medium
- labels_de: Anforderungszeilen
- labels_en: Requirement lines
- definition_de: Feld Anforderungszeilen im Kontext von PlanningRecord.
- definition_en: Requirement lines field used in the PlanningRecord context.
- related_fields: none
- aliases: requirement_lines, Requirement lines, Anforderungszeilen, PlanningRecord
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-02 manifest section planning_orders.requirements includes field requirement_lines labeled Requirement lines.
  - [page_help_manifest] Assistant Page Help Manifest: P-02 manifest section planning_orders.requirements includes field requirement_lines labeled Anforderungszeilen.
  - [backend_schema] CustomerOrder: CustomerOrder includes field requirement_lines.
  - [backend_schema] CustomerOrderRead: CustomerOrderRead includes field requirement_lines.

## planning_record.service_category

- canonical_name: service_category
- module_key: planning
- page_id: P-02
- entity_type: PlanningRecord
- route_names: SicherPlanPlanningOrders
- form_contexts: planning_orders.order_scope, customer_order_create, customer_plan_create, contract_or_document_register
- input_type: input
- required: False
- confidence: low
- labels_de: Leistungskategorie
- labels_en: Service category
- definition_de: Feld Leistungskategorie im Kontext von PlanningRecord.
- definition_en: Service category field used in the PlanningRecord context.
- related_fields: none
- aliases: service_category, Service category, Leistungskategorie, PlanningRecord
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-02 manifest section planning_orders.order_scope includes field service_category labeled Service category.
  - [page_help_manifest] Assistant Page Help Manifest: P-02 manifest section planning_orders.order_scope includes field service_category labeled Leistungskategorie.

## shift.shift_type_code

- canonical_name: shift_type_code
- module_key: planning
- page_id: P-03
- entity_type: Shift
- route_names: SicherPlanPlanningShifts
- form_contexts: planning.shift, planning_shifts.concrete_shift_and_release
- input_type: select
- required: False
- confidence: high
- labels_de: Schichttyp
- labels_en: Shift type
- definition_de: Der Schichttyp beschreibt, welche Art von Schicht geplant oder freigegeben wird, und wird in Vorlagen, Serien und konkreten Schichten verwendet.
- definition_en: Shift type identifies what kind of shift is being planned or released and is used across templates, series, and concrete shifts.
- related_fields: none
- aliases: Schichttyp, shift type, shift_type_code, نوع شیفت
- source_basis:
  - [frontend_locale] planningShifts.messages.ts: planningShifts.messages.ts defines the verified field label Schichttyp / Shift type for the planning shifts workspace.
  - [backend_schema] Planning schemas: Planning schemas persist shift_type_code across templates, series, and concrete shifts.

## shift_plan.code

- canonical_name: code
- module_key: planning
- page_id: P-03
- entity_type: ShiftPlan
- route_names: SicherPlanPlanningShifts
- form_contexts: planning_shifts.templates, customer_plan_create, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: True
- confidence: medium
- labels_de: Code
- labels_en: Code
- definition_de: Feld Code im Kontext von ShiftPlan.
- definition_en: Code field used in the ShiftPlan context.
- related_fields: none
- aliases: code, Code, ShiftPlan
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.templates includes field code labeled Code.
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.templates includes field code labeled Code.
  - [typescript_api_interface] TenantListItem: TenantListItem includes field code.
  - [typescript_api_interface] BranchRead: BranchRead includes field code.
  - [typescript_api_interface] MandateRead: MandateRead includes field code.
  - [typescript_api_interface] LookupValueRead: LookupValueRead includes field code.
  - [typescript_api_interface] TenantOnboardingPayload: TenantOnboardingPayload includes field code.
  - [typescript_api_interface] BranchCreatePayload: BranchCreatePayload includes field code.

## shift_plan.customer_visible_flag

- canonical_name: customer_visible_flag
- module_key: planning
- page_id: P-03
- entity_type: ShiftPlan
- route_names: SicherPlanPlanningShifts
- form_contexts: planning_shifts.concrete_shift_and_release, customer_plan_create, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: False
- confidence: medium
- labels_de: Kundensichtbarkeit
- labels_en: Customer visibility
- definition_de: Feld Kundensichtbarkeit im Kontext von ShiftPlan.
- definition_en: Customer visibility field used in the ShiftPlan context.
- related_fields: none
- aliases: customer_visible_flag, Customer visibility, Kundensichtbarkeit, ShiftPlan
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.concrete_shift_and_release includes field customer_visible_flag labeled Customer visibility.
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.concrete_shift_and_release includes field customer_visible_flag labeled Kundensichtbarkeit.
  - [typescript_api_interface] FinanceBillingTimesheetRead: FinanceBillingTimesheetRead includes field customer_visible_flag.
  - [typescript_api_interface] FinanceBillingInvoiceRead: FinanceBillingInvoiceRead includes field customer_visible_flag.
  - [typescript_api_interface] ShiftSeriesExceptionRead: ShiftSeriesExceptionRead includes field customer_visible_flag.
  - [typescript_api_interface] ShiftSeriesListItem: ShiftSeriesListItem includes field customer_visible_flag.
  - [typescript_api_interface] ShiftListItem: ShiftListItem includes field customer_visible_flag.
  - [typescript_api_interface] ShiftReleaseDiagnosticsRead: ShiftReleaseDiagnosticsRead includes field customer_visible_flag.

## shift_plan.ends_at

- canonical_name: ends_at
- module_key: planning
- page_id: P-03
- entity_type: ShiftPlan
- route_names: SicherPlanPlanningShifts
- form_contexts: planning_shifts.concrete_shift_and_release, customer_plan_create, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: True
- confidence: medium
- labels_de: Endet um
- labels_en: Ends at
- definition_de: Feld Endet um im Kontext von ShiftPlan.
- definition_en: Ends at field used in the ShiftPlan context.
- related_fields: none
- aliases: ends_at, Ends at, Endet um, ShiftPlan
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.concrete_shift_and_release includes field ends_at labeled Ends at.
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.concrete_shift_and_release includes field ends_at labeled Endet um.
  - [typescript_api_interface] CustomerDashboardCalendarItemRead: CustomerDashboardCalendarItemRead includes field ends_at.
  - [typescript_api_interface] EmployeeAvailabilityRuleRead: EmployeeAvailabilityRuleRead includes field ends_at.
  - [typescript_api_interface] EmployeeAvailabilityRuleCreatePayload: EmployeeAvailabilityRuleCreatePayload includes field ends_at.
  - [typescript_api_interface] EmployeeAvailabilityRuleUpdatePayload: EmployeeAvailabilityRuleUpdatePayload includes field ends_at.
  - [typescript_api_interface] ShiftListItem: ShiftListItem includes field ends_at.
  - [typescript_api_interface] PlanningBoardShiftListItem: PlanningBoardShiftListItem includes field ends_at.

## shift_plan.label

- canonical_name: label
- module_key: planning
- page_id: P-03
- entity_type: ShiftPlan
- route_names: SicherPlanPlanningShifts
- form_contexts: planning_shifts.templates, customer_plan_create, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: True
- confidence: medium
- labels_de: Bezeichnung
- labels_en: Label
- definition_de: Feld Bezeichnung im Kontext von ShiftPlan.
- definition_en: Label field used in the ShiftPlan context.
- related_fields: none
- aliases: label, Label, Bezeichnung, ShiftPlan
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.templates includes field label labeled Label.
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.templates includes field label labeled Bezeichnung.
  - [typescript_api_interface] AssistantLink: AssistantLink includes field label.
  - [typescript_api_interface] AssistantPageHelpField: AssistantPageHelpField includes field label.
  - [typescript_api_interface] AssistantPageHelpAction: AssistantPageHelpAction includes field label.
  - [typescript_api_interface] LookupValueRead: LookupValueRead includes field label.
  - [typescript_api_interface] LookupValueCreatePayload: LookupValueCreatePayload includes field label.
  - [typescript_api_interface] LookupValueUpdatePayload: LookupValueUpdatePayload includes field label.

## shift_plan.local_end_time

- canonical_name: local_end_time
- module_key: planning
- page_id: P-03
- entity_type: ShiftPlan
- route_names: SicherPlanPlanningShifts
- form_contexts: planning_shifts.templates, customer_plan_create, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: True
- confidence: medium
- labels_de: Endzeit
- labels_en: End time
- definition_de: Feld Endzeit im Kontext von ShiftPlan.
- definition_en: End time field used in the ShiftPlan context.
- related_fields: none
- aliases: local_end_time, End time, Endzeit, ShiftPlan
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.templates includes field local_end_time labeled End time.
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.templates includes field local_end_time labeled Endzeit.
  - [typescript_api_interface] ShiftTemplateListItem: ShiftTemplateListItem includes field local_end_time.
  - [backend_schema] ShiftTemplate: ShiftTemplate includes field local_end_time.
  - [backend_schema] ShiftTemplateCreate: ShiftTemplateCreate includes field local_end_time.
  - [backend_schema] ShiftTemplateUpdate: ShiftTemplateUpdate includes field local_end_time.
  - [backend_schema] ShiftTemplateListItem: ShiftTemplateListItem includes field local_end_time.

## shift_plan.local_start_time

- canonical_name: local_start_time
- module_key: planning
- page_id: P-03
- entity_type: ShiftPlan
- route_names: SicherPlanPlanningShifts
- form_contexts: planning_shifts.templates, customer_plan_create, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: True
- confidence: medium
- labels_de: Startzeit
- labels_en: Start time
- definition_de: Feld Startzeit im Kontext von ShiftPlan.
- definition_en: Start time field used in the ShiftPlan context.
- related_fields: none
- aliases: local_start_time, Start time, Startzeit, ShiftPlan
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.templates includes field local_start_time labeled Start time.
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.templates includes field local_start_time labeled Startzeit.
  - [typescript_api_interface] ShiftTemplateListItem: ShiftTemplateListItem includes field local_start_time.
  - [backend_schema] ShiftTemplate: ShiftTemplate includes field local_start_time.
  - [backend_schema] ShiftTemplateCreate: ShiftTemplateCreate includes field local_start_time.
  - [backend_schema] ShiftTemplateUpdate: ShiftTemplateUpdate includes field local_start_time.
  - [backend_schema] ShiftTemplateListItem: ShiftTemplateListItem includes field local_start_time.

## shift_plan.planning_from

- canonical_name: planning_from
- module_key: planning
- page_id: P-03
- entity_type: ShiftPlan
- route_names: SicherPlanPlanningShifts
- form_contexts: planning_shifts.plans_and_series, customer_plan_create, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: True
- confidence: medium
- labels_de: Planung von
- labels_en: Planning from
- definition_de: Feld Planung von im Kontext von ShiftPlan.
- definition_en: Planning from field used in the ShiftPlan context.
- related_fields: none
- aliases: planning_from, Planning from, Planung von, ShiftPlan
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.plans_and_series includes field planning_from labeled Planning from.
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.plans_and_series includes field planning_from labeled Planung von.
  - [typescript_api_interface] CustomerDashboardPlanItemRead: CustomerDashboardPlanItemRead includes field planning_from.
  - [typescript_api_interface] PlanningRecordListItem: PlanningRecordListItem includes field planning_from.
  - [typescript_api_interface] PlanningRecordListFilters: PlanningRecordListFilters includes field planning_from.
  - [typescript_api_interface] ShiftPlanListItem: ShiftPlanListItem includes field planning_from.
  - [backend_schema] CustomerDashboardPlanItemRead: CustomerDashboardPlanItemRead includes field planning_from.
  - [backend_schema] PlanningRecord: PlanningRecord includes field planning_from.

## shift_plan.planning_record_id

- canonical_name: planning_record_id
- module_key: planning
- page_id: P-03
- entity_type: ShiftPlan
- route_names: SicherPlanPlanningShifts
- form_contexts: planning_shifts.plans_and_series, customer_plan_create, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: True
- confidence: medium
- labels_de: Planungsdatensatz
- labels_en: Planning record
- definition_de: Feld Planungsdatensatz im Kontext von ShiftPlan.
- definition_en: Planning record field used in the ShiftPlan context.
- related_fields: none
- aliases: planning_record_id, Planning record, Planungsdatensatz, ShiftPlan
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.plans_and_series includes field planning_record_id labeled Planning record.
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.plans_and_series includes field planning_record_id labeled Planungsdatensatz.
  - [typescript_api_interface] CustomerDashboardCalendarItemRead: CustomerDashboardCalendarItemRead includes field planning_record_id.
  - [typescript_api_interface] FinanceBillingTimesheetLineRead: FinanceBillingTimesheetLineRead includes field planning_record_id.
  - [typescript_api_interface] FinanceBillingTimesheetRead: FinanceBillingTimesheetRead includes field planning_record_id.
  - [typescript_api_interface] PlanningCommercialLinkRead: PlanningCommercialLinkRead includes field planning_record_id.
  - [typescript_api_interface] ShiftPlanListItem: ShiftPlanListItem includes field planning_record_id.
  - [typescript_api_interface] PlanningBoardShiftListItem: PlanningBoardShiftListItem includes field planning_record_id.

## shift_plan.planning_to

- canonical_name: planning_to
- module_key: planning
- page_id: P-03
- entity_type: ShiftPlan
- route_names: SicherPlanPlanningShifts
- form_contexts: planning_shifts.plans_and_series, customer_plan_create, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: True
- confidence: medium
- labels_de: Planung bis
- labels_en: Planning to
- definition_de: Feld Planung bis im Kontext von ShiftPlan.
- definition_en: Planning to field used in the ShiftPlan context.
- related_fields: none
- aliases: planning_to, Planning to, Planung bis, ShiftPlan
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.plans_and_series includes field planning_to labeled Planning to.
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.plans_and_series includes field planning_to labeled Planung bis.
  - [typescript_api_interface] CustomerDashboardPlanItemRead: CustomerDashboardPlanItemRead includes field planning_to.
  - [typescript_api_interface] PlanningRecordListItem: PlanningRecordListItem includes field planning_to.
  - [typescript_api_interface] PlanningRecordListFilters: PlanningRecordListFilters includes field planning_to.
  - [typescript_api_interface] ShiftPlanListItem: ShiftPlanListItem includes field planning_to.
  - [backend_schema] CustomerDashboardPlanItemRead: CustomerDashboardPlanItemRead includes field planning_to.
  - [backend_schema] PlanningRecord: PlanningRecord includes field planning_to.

## shift_plan.recurrence_code

- canonical_name: recurrence_code
- module_key: planning
- page_id: P-03
- entity_type: ShiftPlan
- route_names: SicherPlanPlanningShifts
- form_contexts: planning_shifts.plans_and_series, customer_plan_create, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: False
- confidence: medium
- labels_de: Wiederholung
- labels_en: Recurrence
- definition_de: Feld Wiederholung im Kontext von ShiftPlan.
- definition_en: Recurrence field used in the ShiftPlan context.
- related_fields: none
- aliases: recurrence_code, Recurrence, Wiederholung, ShiftPlan
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.plans_and_series includes field recurrence_code labeled Recurrence.
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.plans_and_series includes field recurrence_code labeled Wiederholung.
  - [typescript_api_interface] ShiftSeriesListItem: ShiftSeriesListItem includes field recurrence_code.
  - [backend_schema] ShiftSeries: ShiftSeries includes field recurrence_code.
  - [backend_schema] ShiftSeriesCreate: ShiftSeriesCreate includes field recurrence_code.
  - [backend_schema] ShiftSeriesUpdate: ShiftSeriesUpdate includes field recurrence_code.
  - [backend_schema] ShiftSeriesListItem: ShiftSeriesListItem includes field recurrence_code.

## shift_plan.release_state

- canonical_name: release_state
- module_key: planning
- page_id: P-03
- entity_type: ShiftPlan
- route_names: SicherPlanPlanningShifts
- form_contexts: planning_shifts.concrete_shift_and_release, customer_plan_create, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: False
- confidence: medium
- labels_de: Freigabestatus
- labels_en: Release state
- definition_de: Feld Freigabestatus im Kontext von ShiftPlan.
- definition_en: Release state field used in the ShiftPlan context.
- related_fields: none
- aliases: release_state, Release state, Freigabestatus, ShiftPlan
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.concrete_shift_and_release includes field release_state labeled Release state.
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.concrete_shift_and_release includes field release_state labeled Freigabestatus.
  - [typescript_api_interface] CustomerOrderListItem: CustomerOrderListItem includes field release_state.
  - [typescript_api_interface] CustomerOrderListFilters: CustomerOrderListFilters includes field release_state.
  - [typescript_api_interface] PlanningRecordListItem: PlanningRecordListItem includes field release_state.
  - [typescript_api_interface] PlanningRecordListFilters: PlanningRecordListFilters includes field release_state.
  - [typescript_api_interface] ShiftSeriesListItem: ShiftSeriesListItem includes field release_state.
  - [typescript_api_interface] ShiftListItem: ShiftListItem includes field release_state.

## shift_plan.starts_at

- canonical_name: starts_at
- module_key: planning
- page_id: P-03
- entity_type: ShiftPlan
- route_names: SicherPlanPlanningShifts
- form_contexts: planning_shifts.concrete_shift_and_release, customer_plan_create, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: True
- confidence: medium
- labels_de: Startet um
- labels_en: Starts at
- definition_de: Feld Startet um im Kontext von ShiftPlan.
- definition_en: Starts at field used in the ShiftPlan context.
- related_fields: none
- aliases: starts_at, Starts at, Startet um, ShiftPlan
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.concrete_shift_and_release includes field starts_at labeled Starts at.
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.concrete_shift_and_release includes field starts_at labeled Startet um.
  - [typescript_api_interface] CustomerDashboardCalendarItemRead: CustomerDashboardCalendarItemRead includes field starts_at.
  - [typescript_api_interface] EmployeeAvailabilityRuleRead: EmployeeAvailabilityRuleRead includes field starts_at.
  - [typescript_api_interface] EmployeeAvailabilityRuleCreatePayload: EmployeeAvailabilityRuleCreatePayload includes field starts_at.
  - [typescript_api_interface] EmployeeAvailabilityRuleUpdatePayload: EmployeeAvailabilityRuleUpdatePayload includes field starts_at.
  - [typescript_api_interface] ShiftListItem: ShiftListItem includes field starts_at.
  - [typescript_api_interface] PlanningBoardShiftListItem: PlanningBoardShiftListItem includes field starts_at.

## shift_plan.subcontractor_visible_flag

- canonical_name: subcontractor_visible_flag
- module_key: planning
- page_id: P-03
- entity_type: ShiftPlan
- route_names: SicherPlanPlanningShifts
- form_contexts: planning_shifts.concrete_shift_and_release, customer_plan_create, employee_assign_to_shift, shift_release_to_employee_app
- input_type: input
- required: False
- confidence: medium
- labels_de: Subunternehmer-Sichtbarkeit
- labels_en: Subcontractor visibility
- definition_de: Feld Subunternehmer-Sichtbarkeit im Kontext von ShiftPlan.
- definition_en: Subcontractor visibility field used in the ShiftPlan context.
- related_fields: none
- aliases: subcontractor_visible_flag, Subcontractor visibility, Subunternehmer-Sichtbarkeit, ShiftPlan
- source_basis:
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.concrete_shift_and_release includes field subcontractor_visible_flag labeled Subcontractor visibility.
  - [page_help_manifest] Assistant Page Help Manifest: P-03 manifest section planning_shifts.concrete_shift_and_release includes field subcontractor_visible_flag labeled Subunternehmer-Sichtbarkeit.
  - [typescript_api_interface] ShiftSeriesExceptionRead: ShiftSeriesExceptionRead includes field subcontractor_visible_flag.
  - [typescript_api_interface] ShiftSeriesListItem: ShiftSeriesListItem includes field subcontractor_visible_flag.
  - [typescript_api_interface] ShiftListItem: ShiftListItem includes field subcontractor_visible_flag.
  - [typescript_api_interface] ShiftReleaseDiagnosticsRead: ShiftReleaseDiagnosticsRead includes field subcontractor_visible_flag.
  - [typescript_api_interface] PlanningBoardShiftListItem: PlanningBoardShiftListItem includes field subcontractor_visible_flag.
  - [backend_schema] AssistantPlanningShiftVisibilityItemRead: AssistantPlanningShiftVisibilityItemRead includes field subcontractor_visible_flag.
