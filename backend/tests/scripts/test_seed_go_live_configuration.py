from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

from scripts import seed_go_live_configuration


class _FakeTenantScalarResult:
    def __init__(self, values: list[str]) -> None:
        self.values = values

    def __iter__(self):
        return iter(self.values)


class _FakeSession:
    def __init__(self, tenant_ids: list[str]) -> None:
        self.tenant_ids = tenant_ids
        self.committed = False

    def scalars(self, statement):  # noqa: ANN001
        rendered = str(statement)
        if "core.tenant" not in rendered:
            raise AssertionError(rendered)
        return _FakeTenantScalarResult(self.tenant_ids)

    def commit(self) -> None:
        self.committed = True


class _SessionContext:
    def __init__(self, session: _FakeSession) -> None:
        self.session = session

    def __enter__(self) -> _FakeSession:
        return self.session

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None


class TestSeedGoLiveConfigurationScript(unittest.TestCase):
    def test_parse_args_rejects_all_tenants_without_confirmation(self) -> None:
        with self.assertRaises(SystemExit):
            seed_go_live_configuration._parse_args(["--all-tenants"])

    def test_parse_args_rejects_mixed_single_and_all_tenant_modes(self) -> None:
        with self.assertRaises(SystemExit):
            seed_go_live_configuration._parse_args(
                [
                    "--tenant-id",
                    "tenant-1",
                    "--all-tenants",
                    "--confirm-all-tenants",
                    seed_go_live_configuration.ALL_TENANTS_CONFIRMATION,
                ]
            )

    def test_main_backfills_all_active_tenants_only_when_explicitly_confirmed(self) -> None:
        session = _FakeSession(["tenant-a", "tenant-b"])
        output = io.StringIO()

        with (
            patch.object(
                seed_go_live_configuration,
                "SessionLocal",
                return_value=_SessionContext(session),
            ),
            patch.object(
                seed_go_live_configuration,
                "seed_lookup_values",
                side_effect=[
                    {"inserted": 1, "updated": 0},
                    {"inserted": 2, "updated": 0},
                    {"inserted": 0, "updated": 0},
                ],
            ) as seed_lookup_values_mock,
            patch.object(
                seed_go_live_configuration,
                "seed_document_types",
                return_value={"inserted": 7, "updated": 0},
            ),
            patch.object(
                seed_go_live_configuration,
                "seed_default_tenant_settings",
                side_effect=[
                    {"inserted": 3, "updated": 0},
                    {"inserted": 0, "updated": 0},
                ],
            ) as seed_default_tenant_settings_mock,
            patch.object(
                seed_go_live_configuration,
                "seed_baseline_employee_catalogs",
                side_effect=[
                    {
                        "function_types_inserted": 4,
                        "function_types_updated": 0,
                        "qualification_types_inserted": 4,
                        "qualification_types_updated": 0,
                    },
                    {
                        "function_types_inserted": 0,
                        "function_types_updated": 1,
                        "qualification_types_inserted": 0,
                        "qualification_types_updated": 1,
                    },
                ],
            ) as seed_baseline_employee_catalogs_mock,
            patch(
                "sys.argv",
                [
                    "seed_go_live_configuration.py",
                    "--all-tenants",
                    "--confirm-all-tenants",
                    seed_go_live_configuration.ALL_TENANTS_CONFIRMATION,
                ],
            ),
            redirect_stdout(output),
        ):
            result = seed_go_live_configuration.main()

        self.assertEqual(result, 0)
        self.assertTrue(session.committed)
        self.assertEqual(seed_lookup_values_mock.call_count, 3)
        self.assertEqual(
            [call.kwargs["tenant_id"] for call in seed_default_tenant_settings_mock.call_args_list],
            ["tenant-a", "tenant-b"],
        )
        self.assertEqual(
            [call.kwargs["tenant_id"] for call in seed_baseline_employee_catalogs_mock.call_args_list],
            ["tenant-a", "tenant-b"],
        )
        self.assertIn("'mode': 'all-tenants'", output.getvalue())
        self.assertIn("'tenant_count': 2", output.getvalue())

