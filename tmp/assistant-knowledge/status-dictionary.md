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
  - registered: de=Firmensitz | en=Registered office
  - billing: de=Rechnung | en=Billing
  - mailing: de=Post | en=Mailing
  - service: de=Leistungsort | en=Service location
- source_basis:
  - [frontend_locale] messages.ts: customerAdmin.addressType.* labels define registered, billing, mailing, and service address options.
  - [backend_schema] CustomerAddressCreate: CustomerAddressCreate.address_type enforces registered|billing|mailing|service.

## customer.classification_lookup_id

- module_key: customers
- page_id: C-01
- entity_type: Customer
- value_source_kind: tenant_lookup
- confidence: medium
- labels_de: Klassifikation
- labels_en: Classification
- aliases: classification_lookup_id, Classification, Klassifikation
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
  - active: de=Aktiv | en=Active
  - inactive: de=Inaktiv | en=Inactive
  - archived: de=Archiviert | en=Archived
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
- aliases: ranking_lookup_id, Ranking, Ranking
- source_basis:
  - [typescript_api_interface] CustomerReferenceDataRead: CustomerReferenceDataRead exposes tenant-scoped options used for ranking_lookup_id.
