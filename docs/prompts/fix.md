You are fixing 2 failing backend pytest tests in the SicherPlan monorepo.

Current failing command
python -m pytest -q

Current failures

1)
FAILED backend/tests/modules/core/test_config_seed.py::TestConfigSeed::test_tenant_setting_seed_is_idempotent

Observed failure:
expected:
{"inserted": 2, "updated": 0}
actual:
{"inserted": 3, "updated": 0}

2)
FAILED backend/tests/modules/subcontractors/test_subcontractor_readiness.py::SubcontractorReadinessServiceTest::test_missing_proof_and_expired_compliance_qualification_block_worker

Observed failure:
expected:
blocking_issue_count >= 2
actual:
blocking_issue_count == 1

Your job
Diagnose the real root cause of both failures and fix them correctly.
Do NOT make superficial changes just to satisfy the assertions.
Do NOT weaken the tests unless the test expectation is truly outdated and you can justify it from the codebase behavior and domain rules.

Work process

1) Inspect the exact implementation and tests for both failing areas:
- backend/tests/modules/core/test_config_seed.py
- backend/tests/modules/subcontractors/test_subcontractor_readiness.py

And inspect the production code they cover, especially:
- the function that seeds default tenant settings
- the seed definitions/source of truth for tenant settings
- the subcontractor readiness service
- the logic that calculates readiness_status
- the logic that builds blocking issues / blocking_issue_count
- any helper methods used for compliance proof checks and qualification expiry checks

2) For the config seed failure, determine which of these is true:
- the seed implementation now intentionally has 3 default tenant settings and the test is stale
OR
- the seed implementation is incorrectly inserting an extra setting
OR
- idempotence is broken in a way that only appears as an inserted-count mismatch

Important:
- preserve idempotence
- do not allow duplicate tenant settings for the same tenant/key
- the second call must not insert duplicates
- keep the returned inserted/updated counts semantically correct

3) For the subcontractor readiness failure, determine why only 1 blocking issue is being counted instead of at least 2.
Specifically verify whether both of these conditions are supposed to independently contribute blocking issues:
- missing proof
- expired compliance qualification

Check for mistakes such as:
- one issue overwriting another
- de-duplication collapsing distinct blockers incorrectly
- only the final blocker being retained
- filtering logic that excludes one blocker
- mismatch between readiness_status logic and blocking_issue_count logic
- qualification/proof issues being combined into one generic blocker when the test/domain expects separate blocking issues

Important:
- preserve domain correctness
- if two independent blocking conditions exist, they should both be represented in blocking_issue_count unless the codebase intentionally aggregates them into one issue and the tests are outdated
- do not inflate counts artificially

4) Add or adjust tests only when justified
- If the production code is correct and the test is outdated, update the test with a short code comment or clear rationale in the implementation/report
- Otherwise fix the implementation and keep the tests meaningful
- Add focused regression coverage if useful for:
  - tenant setting seed idempotence and count behavior
  - subcontractor readiness counting multiple simultaneous blockers

Constraints
- Keep changes minimal and maintainable
- Do not refactor unrelated modules
- Do not change public API semantics unless clearly necessary
- Do not hide failures by loosening assertions without understanding the domain logic
- Prefer fixing root cause over patching test data

Definition of done
- Both failing tests pass
- Full test suite passes with:
  python -m pytest -q
- Tenant setting seeding remains idempotent
- Blocking issue count in subcontractor readiness accurately reflects simultaneous blockers
- No unrelated regressions

Before coding
Briefly report:
1) which files you will inspect/change
2) your preliminary hypothesis for each of the 2 failures

After coding
Report:
1) root cause of failure #1
2) root cause of failure #2
3) changed files
4) whether you changed production code, tests, or both, and why
5) results of:
   - python -m pytest backend/tests/modules/core/test_config_seed.py -q
   - python -m pytest backend/tests/modules/subcontractors/test_subcontractor_readiness.py -q
   - python -m pytest -q


Those errors are:
(.venv-backend-test) jey@DESKTOP-M16IUT4:~/Projects/SicherPlan$ python -m pytest -q
.....F............................................................................................................................................................................................................... [ 46%]
.................................................................................................................................................................................................................................... [ 95%]
......F..............                                                                                                                                                                                                                [100%]
================================================================================================================= FAILURES =================================================================================================================
__________________________________________________________________________________________ TestConfigSeed.test_tenant_setting_seed_is_idempotent ___________________________________________________________________________________________

self = <tests.modules.core.test_config_seed.TestConfigSeed testMethod=test_tenant_setting_seed_is_idempotent>

    def test_tenant_setting_seed_is_idempotent(self) -> None:
        session = _FakeSession()
        first = seed_default_tenant_settings(session, tenant_id="tenant-1")
        second = seed_default_tenant_settings(session, tenant_id="tenant-1")
>       self.assertEqual(first, {"inserted": 2, "updated": 0})
E       AssertionError: {'inserted': 3, 'updated': 0} != {'inserted': 2, 'updated': 0}
E       - {'inserted': 3, 'updated': 0}
E       ?              ^
E
E       + {'inserted': 2, 'updated': 0}
E       ?              ^

backend/tests/modules/core/test_config_seed.py:60: AssertionError
__________________________________________________________________ SubcontractorReadinessServiceTest.test_missing_proof_and_expired_compliance_qualification_block_worker __________________________________________________________________

self = <tests.modules.subcontractors.test_subcontractor_readiness.SubcontractorReadinessServiceTest testMethod=test_missing_proof_and_expired_compliance_qualification_block_worker>

    def test_missing_proof_and_expired_compliance_qualification_block_worker(self) -> None:
        result = self.service.get_worker_readiness("tenant-1", "subcontractor-1", "worker-blocked", self.context)

        self.assertEqual(result.readiness_status, "not_ready")
>       self.assertGreaterEqual(result.blocking_issue_count, 2)
E       AssertionError: 1 not greater than or equal to 2

backend/tests/modules/subcontractors/test_subcontractor_readiness.py:308: AssertionError
========================================================================================================= short test summary info ==========================================================================================================
FAILED backend/tests/modules/core/test_config_seed.py::TestConfigSeed::test_tenant_setting_seed_is_idempotent - AssertionError: {'inserted': 3, 'updated': 0} != {'inserted': 2, 'updated': 0}
FAILED backend/tests/modules/subcontractors/test_subcontractor_readiness.py::SubcontractorReadinessServiceTest::test_missing_proof_and_expired_compliance_qualification_block_worker - AssertionError: 1 not greater than or equal to 2
2 failed, 460 passed, 15 subtests passed in 8.45s