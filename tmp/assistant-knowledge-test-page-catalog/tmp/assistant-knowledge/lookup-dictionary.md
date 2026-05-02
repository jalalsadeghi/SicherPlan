# Assistant Lookup Dictionary

## customer.address_type

- module_key: customers
- page_id: C-01
- entity_type: CustomerAddress
- value_source_kind: static
- confidence: high
- labels_de: Adresstyp
- labels_en: Address type
- aliases: customerAdmin.fields.addressType, address type, adresstyp, address_type
- values:
  - registered: de=registered | en=registered
  - billing: de=billing | en=billing
  - mailing: de=mailing | en=mailing
  - service: de=service | en=service
- source_basis:
  - [frontend_locale] messages.ts: customerAdmin.addressType.* labels define registered, billing, mailing, and service address options.
  - [backend_schema] CustomerAddressCreate: CustomerAddressCreate.address_type enforces registered|billing|mailing|service.

## customer.classification_lookup_id

- module_key: customers
- page_id: C-01
- entity_type: Customer
- value_source_kind: tenant_lookup
- confidence: medium
- labels_de: Klassifizierung
- labels_en: Classification
- aliases: classification_lookup_id, Classification, Klassifizierung, Klassifikation, طبقه‌بندی, طبقه‌بندی مشتری
- source_basis:
  - [typescript_api_interface] CustomerReferenceDataRead: CustomerReferenceDataRead exposes tenant-scoped options used for classification_lookup_id.

## customer.customer_status_lookup_id

- module_key: customers
- page_id: C-01
- entity_type: Customer
- value_source_kind: tenant_lookup
- confidence: medium
- labels_de: Kundenstatus-Metadaten
- labels_en: Customer status metadata
- aliases: customer_status_lookup_id, Customer status metadata, Kundenstatus-Metadaten
- source_basis:
  - [typescript_api_interface] CustomerReferenceDataRead: CustomerReferenceDataRead exposes tenant-scoped options used for customer_status_lookup_id.

## customer.legal_form_lookup_id

- module_key: customers
- page_id: C-01
- entity_type: Customer
- value_source_kind: tenant_lookup
- confidence: medium
- labels_de: Rechtsform
- labels_en: Legal form
- aliases: legal_form_lookup_id, Legal form, Rechtsform
- source_basis:
  - [typescript_api_interface] CustomerReferenceDataRead: CustomerReferenceDataRead exposes tenant-scoped options used for legal_form_lookup_id.

## customer.lifecycle_status

- module_key: customers
- page_id: C-01
- entity_type: Customer
- value_source_kind: static
- confidence: high
- labels_de: Lifecycle-Status, Status
- labels_en: Lifecycle status, Status
- aliases: customerAdmin.fields.lifecycleStatus, status, lifecycle status, lifecycle_status
- values:
  - active: de=active | en=Active
  - inactive: de=inactive | en=Inactive
  - archived: de=archived | en=Archived
- source_basis:
  - [frontend_locale] messages.ts: customerAdmin.fields.lifecycleStatus and customerAdmin.status.* define the lifecycle label and its visible option labels.
  - [frontend_component] CustomerAdminView.vue: CustomerAdminView.vue binds customerDraft.status to a select with active and inactive options.

## customer.ranking_lookup_id

- module_key: customers
- page_id: C-01
- entity_type: Customer
- value_source_kind: tenant_lookup
- confidence: medium
- labels_de: Ranking
- labels_en: Ranking
- aliases: ranking_lookup_id, Ranking, Ranking, رتبه‌بندی
- source_basis:
  - [typescript_api_interface] CustomerReferenceDataRead: CustomerReferenceDataRead exposes tenant-scoped options used for ranking_lookup_id.

## planning.customer_visible_flag

- module_key: planning
- page_id: P-03
- entity_type: ShiftPlan
- value_source_kind: static
- confidence: medium
- labels_de: Kunde sichtbar
- labels_en: Customer visible
- aliases: customer visible, kunde sichtbar, customer visibility, قابل مشاهده برای مشتری
- values:
  - true: de=Sichtbar | en=Visible
  - false: de=Nicht sichtbar | en=Not visible
- source_basis:
  - [backend_schema] Planning visibility flags: Planning read models expose customer visibility as an explicit boolean release flag.

## planning.employee_visible

- module_key: planning
- page_id: P-03
- entity_type: Shift
- value_source_kind: static
- confidence: medium
- labels_de: Mitarbeiter sichtbar
- labels_en: Employee visible
- aliases: employee visible, mitarbeiter sichtbar, employee app visible, app visible, قابل مشاهده برای کارمند
- values:
  - true: de=Sichtbar | en=Visible
  - false: de=Nicht sichtbar | en=Not visible
- source_basis:
  - [backend_schema] Planning shift read model: Planning shift read schemas expose employee_visible as the employee-app visibility result for a shift.

## planning.release_state

- module_key: planning
- page_id: P-03
- entity_type: ShiftPlan
- value_source_kind: static
- confidence: medium
- labels_de: Freigabestatus
- labels_en: Release status
- aliases: release state, release status, freigabestatus, release_ready, released, draft, وضعیت انتشار
- values:
  - draft: de=Entwurf | en=Draft
  - release_ready: de=Freigabereif | en=Release ready
  - released: de=Freigegeben | en=Released
- source_basis:
  - [backend_schema] Planning release state catalog: Planning services and schemas use draft, release_ready, and released as the verified release-state values.

## planning.workforce_scope_code

- module_key: planning
- page_id: P-03
- entity_type: ShiftPlan
- value_source_kind: static
- confidence: medium
- labels_de: Einsatzkraefte-Scope
- labels_en: Workforce scope
- aliases: workforce scope, scope, mixed, internal, subcontractor, einsatzkraefte-scope, نوع پوشش نیرو
- values:
  - internal: de=Intern | en=Internal
  - subcontractor: de=Subunternehmer | en=Subcontractor
  - mixed: de=Gemischt | en=Mixed
- source_basis:
  - [backend_schema] Planning models: Planning models constrain workforce_scope_code to internal, subcontractor, or mixed.
