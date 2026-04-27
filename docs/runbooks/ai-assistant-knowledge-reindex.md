# AI Assistant Knowledge Reindex Runbook

## Purpose

This runbook explains how the current SicherPlan assistant knowledge indexing works and what to do when documentation-backed assistant answers need to be refreshed.

Important current state:

- the repository implements knowledge ingestion and retrieval services;
- the repository now exposes a developer CLI reindex path;
- there is still no supported assistant knowledge reindex HTTP endpoint or admin UI;
- reindex remains a developer/operator maintenance action, not a productized runtime feature.

## When to Reindex

Reindex is needed when indexed documentation changes in ways that should affect assistant answers:

- `docs/` content changed materially;
- sprint docs changed;
- repository engineering/security/runbook/QA docs changed;
- verified page-help guidance changed;
- route/page catalog assumptions changed;
- deployment includes new or corrected assistant reference docs.

Reindex is not needed for:

- unrelated operational database changes;
- customer data changes;
- employee/private document changes;
- portal business data changes.

## Who May Reindex

Permission model:

- `assistant.knowledge.reindex`

Current seeded role mapping:

- `platform_admin`

Current implementation note:

- this permission is seeded and surfaced in capabilities;
- there is still no HTTP route in [router.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/router.py) that executes a reindex.

## Source Locations

The knowledge ingestion adapter is file-based and policy-restricted.

Supported source types from [knowledge/types.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/knowledge/types.py):

- `markdown`
- `text`
- `json`
- `openapi`
- `sprint_doc`
- `repository_docs`
- `manual`

Deferred source types:

- `pdf`
- `xlsx`

Allowed file suffixes from [knowledge/source_loader.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/knowledge/source_loader.py):

- `.md`
- `.txt`
- `.json`
- `.yaml`
- `.yml`

Current repository intent:

- index repository documentation and curated text sources only;
- do not index operational business data or uploaded private documents.

Blocked file patterns include:

- `.env`
- `*.pem`
- `*.key`
- `*secret*`
- `*token*`
- `*credential*`
- database dump / sqlite style files

## Reindex Methods

### Supported today

Developer/operator CLI:

```bash
cd backend
PYTHONPATH=. python3 -m app.modules.assistant.knowledge.ingest --reindex
```

This command:

- rebuilds the default assistant knowledge registrations;
- regenerates the curated markdown sources under `tmp/assistant-knowledge/`;
- purges existing `assistant.knowledge_*` rows when `--reindex` is provided;
- ingests the curated documentation corpus again;
- prints a JSON summary with source and chunk counts.

Expected JSON keys now include:

- `sources_registered`
- `sources_indexed`
- `sources_skipped_unchanged`
- `chunks_created`
- `chunks_active`
- `failures`

### Stage / Docker Compose

If the stage stack runs the backend in Docker Compose, execute the same module inside the backend container:

```bash
docker compose exec backend sh -lc 'cd /app/backend && PYTHONPATH=. python3 -m app.modules.assistant.knowledge.ingest --reindex'
```

Use the actual compose service name and container workdir from the deployment if they differ.

Relevant files:

- [knowledge/source_loader.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/knowledge/source_loader.py)
- [knowledge/ingest.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/knowledge/ingest.py)
- [knowledge/repository.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/knowledge/repository.py)

### Not supported yet

- no `POST /api/assistant/knowledge/reindex`
- no `GET /api/assistant/knowledge/status`
- no admin UI button

Treat any direct Python invocation as a controlled maintenance action, not a normal operator workflow.

## Expected Output

`AssistantKnowledgeIngestionService.ingest(...)` returns `KnowledgeIngestionResult` with:

- `sources_seen`
- `sources_indexed`
- `sources_skipped`
- `sources_failed`
- `chunks_created`
- `failures`

Expected behaviors:

- unchanged path/hash pairs are skipped;
- changed sources are reindexed and chunk rows replaced;
- unsupported or blocked sources are marked failed;
- ingestion is deterministic for the same normalized content.

## Validation After Reindex

Because there is no runtime status endpoint yet, validate reindex by checking:

1. database rows in:
   - `assistant.knowledge_source`
   - `assistant.knowledge_chunk`
2. ingestion result counts from the maintenance invocation
3. retrieval behavior through backend tests or controlled assistant questions
4. assistant answers that should reference newly updated docs

Useful test files for regression:

- [backend/tests/modules/assistant/test_knowledge_source_loader.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_knowledge_source_loader.py)
- [backend/tests/modules/assistant/test_knowledge_chunker.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_knowledge_chunker.py)
- [backend/tests/modules/assistant/test_knowledge_ingestion.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_knowledge_ingestion.py)
- [backend/tests/modules/assistant/test_knowledge_retrieval.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_knowledge_retrieval.py)

## Troubleshooting

### Missing permission

Symptom:
- actor has no `assistant.knowledge.reindex`

Current note:
- the CLI is a maintenance operation and is not permission-enforced inside the process;
- any future HTTP or UI operator surface must still require `assistant.knowledge.reindex`.

### Feature disabled

Symptom:
- `SP_AI_ENABLED=false`

Impact:
- assistant capability surface is disabled;
- ingestion classes still exist, but reindex should not be treated as a production-facing operation in disabled mode.

### Source path missing or outside allowed roots

Cause:
- registration path does not exist or resolves outside configured roots

Where enforced:
- [knowledge/source_loader.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/knowledge/source_loader.py)

### Unsupported file type

Cause:
- suffix outside `.md`, `.txt`, `.json`, `.yaml`, `.yml`
- or source type is `pdf` / `xlsx`

Result:
- safe failure through `UnsupportedKnowledgeSourceError`

### Embedding provider unavailable

Current state:
- runtime retrieval uses lexical retrieval by default;
- vector retrieval is optional and no-op by default, so embedding availability is not required for baseline operation.

### Vector extension unavailable

Current state:
- no pgvector-backed runtime path exists in this branch;
- `embedding` is stored in JSONB and lexical retrieval remains the fallback.

### Hash unchanged

Cause:
- normalized content hash did not change

Result:
- source is skipped intentionally

### Provider timeout

Current state:
- provider timeout affects answer generation, not ingestion itself;
- knowledge ingestion is local file + database work.

### Malformed document

Examples:

- invalid UTF-8
- oversize file
- blocked filename pattern

Result:
- source is marked failed with failure detail in ingestion result

## Rollback and Safe Recovery

Current safe recovery options:

1. fix the source file and rerun ingestion;
2. mark or replace the failed source record through repository-backed maintenance code;
3. rerun ingestion for only the affected registrations;
4. continue using lexical retrieval for already indexed chunks.

What is not implemented:

- one-click knowledge rollback endpoint;
- explicit chunk purge admin command;
- UI-level source deactivate/reactivate flow.

## Operational Cautions

- do not index operational business data;
- do not index customer-private, employee-private, HR-private, or payroll-sensitive documents;
- do not index secrets, tokens, or environment files;
- do not treat uploaded document buckets as global assistant knowledge;
- avoid ad hoc bulk reindexing during peak time until a controlled operator flow exists;
- keep the indexed corpus curated and documentation-focused.
