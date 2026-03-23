# US-34 Historical Document Pilot

## Purpose

This pilot proves that legacy files and new QR/barcode-style outputs can coexist in the central docs model without bypassing metadata, versions, or links.

## Historical import manifest rules

- `source_module` is fixed to `migration_import`.
- `source_label` is deterministic: `historical:<source_system>:<legacy_document_id>`.
- The manifest must contain:
  - explicit owner linkage
  - legacy source identifiers
  - checksum
  - source file name
  - base64 file content for the pilot flow
- Provenance is written into `docs.document.metadata_json.migration`.

## Duplicate detection

- Duplicate `manifest_row_key` inside one request is invalid.
- Duplicate `source_system + legacy_document_id` across already imported docs is invalid.

## Deterministic code output payloads

Format:

```text
SP|1|<output_kind>|<owner_type>|<owner_id>|key=value|key=value
```

Representative output kinds:

- `employee_badge`
- `order_badge`

The payload format is intentionally text-based and deterministic for UAT/go-live validation. It remains compatible with later QR/barcode rendering without creating a second output storage path.
