# Communication Backbone

## Scope

- `comm.message_template` stores tenant-scoped DE/EN templates by `channel + template_key + language_code`.
- `comm.outbound_message` stores rendered message history and related-entity references.
- `comm.message_recipient` stores one row per destination.
- `comm.delivery_attempt` stores append-only provider-attempt history.

## Rendering rules

- German is the default template language.
- English is the supported secondary language.
- Rendering falls back to German if an English variant is missing.
- Missing placeholders fail fast instead of silently sending partially rendered content.

## Attachment rules

- Attachments stay in the docs service.
- Communication flows link existing `docs.document` rows to `comm.outbound_message` through `docs.document_link`.
- The docs owner type `comm.outbound_message` is explicitly supported for this purpose.

## Provider boundary

- Outbound message creation expands recipients and produces provider-dispatch-ready payload previews only.
- No concrete provider call happens inside the same transaction that creates the message rows.
- Delivery-attempt rows are append-only and keep provider result details out of the main business tables.
