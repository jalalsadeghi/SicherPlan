# US-34 Migration Template Package v1

## Load order

1. `customers`
2. `employees`
3. `subcontractors`
4. `orders`
5. `documents`

## Matching rules

- `upsert`: create if the business key is missing, update if it already exists.
- `create_only`: fail if the business key already exists.
- `update_only`: fail if the business key does not exist yet.
- Fuzzy matching on names is not allowed.

## Business keys

- Customers: `customer_number`
- Employees: `personnel_no`
- Subcontractors: `subcontractor_number`
- Orders: `order_no`
- Documents: `manifest_row_key`

## Cross-sheet references

- `orders.customer_number` must resolve to `customers.customer_number` in the same package or an already existing CRM customer.
- `documents.owner_sheet` plus `documents.owner_business_key` must resolve to one of the approved business sheets.
- `orders.requirement_type_code` must already exist in the planning master data; orders do not create requirement types implicitly.

## Document migration rules

- Historical files are imported only through manifest rows.
- Each manifest row must include explicit owner linkage, checksum, source system, and legacy document ID.
- Imported files become `docs.document`, `docs.document_version`, and `docs.document_link` rows. No legacy file path is treated as business semantics.

## Representative example rows

### customers

```json
{
  "match_action": "upsert",
  "customer_number": "K-1001",
  "name": "Messe Berlin",
  "legal_name": "Messe Berlin GmbH",
  "legal_form_code": "gmbh",
  "status": "active"
}
```

### employees

```json
{
  "match_action": "upsert",
  "personnel_no": "P-2001",
  "first_name": "Anna",
  "last_name": "Schmidt",
  "work_email": "anna.schmidt@example.test",
  "status": "active"
}
```

### subcontractors

```json
{
  "match_action": "upsert",
  "subcontractor_number": "SU-3001",
  "legal_name": "Nord Security Service GmbH",
  "subcontractor_status_code": "active",
  "status": "active"
}
```

### orders

```json
{
  "match_action": "upsert",
  "order_no": "A-4001",
  "customer_number": "K-1001",
  "requirement_type_code": "event_security",
  "title": "Fruehjahrsmesse Eingang Nord",
  "service_category_code": "event",
  "service_from": "2026-04-15",
  "service_to": "2026-04-20"
}
```

### documents

```json
{
  "manifest_row_key": "DOC-1",
  "source_system": "legacy_dms",
  "legacy_document_id": "4711",
  "source_file_name": "vertrag.pdf",
  "title": "Rahmenvertrag 2025",
  "owner_sheet": "customers",
  "owner_business_key": "K-1001",
  "document_type_key": "customer_contract",
  "relation_type": "attachment",
  "checksum_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "content_base64": "UERG"
}
```

## Error report shape

Each preflight row emits:

- `sheet_key`
- `row_no`
- `business_key`
- `status`
- `match_result`
- `issues[]`

Each issue contains:

- `severity`
- `code`
- `message`
