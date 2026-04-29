Fix field/lookup corpus freshness check so unrelated frontend changes do not make the generated artifact stale.

Current issue:
The Stage Deploy workflow fails before Docker image build in:
Verify committed field/lookup corpus artifact is current

The exporter is deterministic: tmp1 and tmp2 match.
The committed artifact differs only in source_hashes.frontend_root:
old frontend_root != regenerated frontend_root

field_count and lookup_count are unchanged:
field_count=219
lookup_count=10

Root cause:
field_lookup_corpus.json stores a broad frontend_root hash. This hash changes for unrelated frontend changes, even when the extracted field/lookup corpus does not change. Therefore CI fails too often and blocks backend image builds even when corpus content is unchanged.

Tasks:
1. Inspect backend/app/modules/assistant/field_dictionary.py, especially _collect_source_hashes and any helper used to hash frontend_root.
2. Verify exactly which files are included in frontend_root.
3. Replace the broad frontend_root hash with semantic hashes over extraction-relevant data only.
4. Do not hash the entire web/apps/web-antd/src tree.
5. Compute stable hashes from normalized extracted inputs, for example:
   - locale labels used by corpus extraction;
   - legacy messages used by corpus extraction;
   - Vue form bindings extracted by the corpus extractor;
   - TypeScript API interface fields extracted by the corpus extractor;
   - backend schema fields extracted by the corpus extractor;
   - page help seed data.
6. If keeping a diagnostic frontend_root hash is useful, keep it outside the freshness-compared artifact, or mark it as diagnostic only and exclude it from CI diff.
7. Ensure the committed artifact changes only when effective corpus content or semantic extraction inputs change.
8. Regenerate backend/app/modules/assistant/generated/field_lookup_corpus.json after the fix.
9. Update the CI check to compare deterministic semantic artifact output.
10. Add tests:
   - changing an unrelated frontend style/component text that is not used by extractor must not change artifact output;
   - changing a field label in de-DE/en-US locale must change artifact output;
   - changing a v-model field binding used by extractor must change artifact output;
   - exporter remains deterministic;
   - Vertragsreferenz and Rechtlicher Name remain in-scope;
   - Apfelkuchen remains out-of-scope.

Acceptance criteria:
- The current workflow no longer fails only because frontend_root changed.
- Unrelated frontend changes do not require refreshing field_lookup_corpus.json.
- Real field/lookup/i18n/schema changes still require refreshing the artifact.
- Docker image build step is reached.
- Tests pass.