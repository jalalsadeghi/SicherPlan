from __future__ import annotations

import unittest
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from sqlalchemy import CheckConstraint
from sqlalchemy.dialects import postgresql

from app.db import Base
from app.errors import ApiException
from app.modules.customers.commercial_service import CustomerCommercialService
from app.modules.customers.models import CustomerRateCard, CustomerRateLine, CustomerSurchargeRule
from app.modules.customers.schemas import (
    CustomerCreate,
    CustomerRateCardCreate,
    CustomerRateCardUpdate,
    CustomerRateLineCreate,
    CustomerRateLineUpdate,
    CustomerSurchargeRuleCreate,
)
from app.modules.customers.service import CustomerService
from app.modules.iam.audit_service import AuditService
from tests.modules.customers.test_customer_backbone import FakeCustomerRepository, _actor
from tests.modules.customers.test_customer_commercial_profile import RecordingAuditRepository


@dataclass
class FakeRateLine:
    id: str
    tenant_id: str
    rate_card_id: str
    line_kind: str
    billing_unit: str
    unit_price: Decimal
    function_type_id: str | None = None
    qualification_type_id: str | None = None
    function_type: object | None = None
    qualification_type: object | None = None
    planning_mode_code: str | None = None
    minimum_quantity: Decimal | None = None
    sort_order: int = 100
    notes: str | None = None
    status: str = "active"
    version_no: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by_user_id: str | None = None
    updated_by_user_id: str | None = None
    archived_at: datetime | None = None


@dataclass
class FakeSurchargeRule:
    id: str
    tenant_id: str
    rate_card_id: str
    surcharge_type: str
    effective_from: date
    effective_to: date | None = None
    weekday_mask: str | None = None
    time_from_minute: int | None = None
    time_to_minute: int | None = None
    region_code: str | None = None
    percent_value: Decimal | None = None
    fixed_amount: Decimal | None = None
    currency_code: str | None = None
    sort_order: int = 100
    notes: str | None = None
    status: str = "active"
    version_no: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by_user_id: str | None = None
    updated_by_user_id: str | None = None
    archived_at: datetime | None = None


@dataclass
class FakeRateCard:
    id: str
    tenant_id: str
    customer_id: str
    rate_kind: str
    currency_code: str
    effective_from: date
    effective_to: date | None = None
    notes: str | None = None
    status: str = "active"
    version_no: int = 1
    rate_lines: list[FakeRateLine] = field(default_factory=list)
    surcharge_rules: list[FakeSurchargeRule] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by_user_id: str | None = None
    updated_by_user_id: str | None = None
    archived_at: datetime | None = None


class FakePricingRepository(FakeCustomerRepository):
    def __init__(self) -> None:
        super().__init__()
        self.rate_cards: dict[str, list[FakeRateCard]] = {}

    def list_rate_cards(self, tenant_id: str, customer_id: str) -> list[FakeRateCard]:
        return [row for row in self.rate_cards.get(customer_id, []) if row.tenant_id == tenant_id]

    def get_rate_card(self, tenant_id: str, customer_id: str, rate_card_id: str) -> FakeRateCard | None:
        return next(
            (
                row
                for row in self.rate_cards.get(customer_id, [])
                if row.tenant_id == tenant_id and row.id == rate_card_id
            ),
            None,
        )

    def create_rate_card(self, tenant_id: str, customer_id: str, payload: CustomerRateCardCreate, actor_user_id: str | None):
        row = FakeRateCard(
            id=str(uuid4()),
            tenant_id=tenant_id,
            customer_id=customer_id,
            rate_kind=payload.rate_kind,
            currency_code=payload.currency_code,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.rate_cards.setdefault(customer_id, []).append(row)
        return row

    def update_rate_card(self, tenant_id: str, customer_id: str, rate_card_id: str, payload: CustomerRateCardUpdate, actor_user_id: str | None):
        row = self.get_rate_card(tenant_id, customer_id, rate_card_id)
        if row is None:
            return None
        updates = payload.model_dump(exclude_unset=True, exclude={"version_no"})
        next_row = replace(
            row,
            **updates,
            version_no=row.version_no + 1,
            updated_by_user_id=actor_user_id,
            updated_at=datetime.now(UTC),
        )
        self.rate_cards[customer_id] = [next_row if card.id == rate_card_id else card for card in self.rate_cards.get(customer_id, [])]
        return next_row

    def list_overlapping_rate_cards(self, tenant_id: str, customer_id: str, *, rate_kind: str, effective_from: date, effective_to: date | None, exclude_id: str | None = None) -> list[FakeRateCard]:
        rows = []
        for row in self.rate_cards.get(customer_id, []):
            if row.tenant_id != tenant_id or row.archived_at is not None or row.rate_kind != rate_kind or row.id == exclude_id:
                continue
            row_end = row.effective_to
            probe_end = effective_to
            overlaps = (probe_end is None or row.effective_from <= probe_end) and (row_end is None or row_end >= effective_from)
            if overlaps:
                rows.append(row)
        return rows

    def list_rate_lines(self, tenant_id: str, rate_card_id: str) -> list[FakeRateLine]:
        card = self._find_card_by_id(tenant_id, rate_card_id)
        return list(card.rate_lines if card else [])

    def get_rate_line(self, tenant_id: str, rate_card_id: str, rate_line_id: str) -> FakeRateLine | None:
        card = self._find_card_by_id(tenant_id, rate_card_id)
        if card is None:
            return None
        return next((row for row in card.rate_lines if row.id == rate_line_id), None)

    def create_rate_line(self, tenant_id: str, rate_card_id: str, payload: CustomerRateLineCreate, actor_user_id: str | None):
        card = self._find_card_by_id(tenant_id, rate_card_id)
        row = FakeRateLine(
            id=str(uuid4()),
            tenant_id=tenant_id,
            rate_card_id=rate_card_id,
            line_kind=payload.line_kind,
            function_type_id=payload.function_type_id,
            qualification_type_id=payload.qualification_type_id,
            function_type=self.get_function_type(tenant_id, payload.function_type_id) if payload.function_type_id else None,
            qualification_type=(
                self.get_qualification_type(tenant_id, payload.qualification_type_id)
                if payload.qualification_type_id
                else None
            ),
            planning_mode_code=payload.planning_mode_code,
            billing_unit=payload.billing_unit,
            unit_price=payload.unit_price,
            minimum_quantity=payload.minimum_quantity,
            sort_order=payload.sort_order,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        assert card is not None
        card.rate_lines.append(row)
        return row

    def update_rate_line(self, tenant_id: str, rate_card_id: str, rate_line_id: str, payload: CustomerRateLineUpdate, actor_user_id: str | None):
        card = self._find_card_by_id(tenant_id, rate_card_id)
        row = self.get_rate_line(tenant_id, rate_card_id, rate_line_id)
        if card is None or row is None:
            return None
        updates = payload.model_dump(exclude_unset=True, exclude={"version_no"})
        next_row = replace(
            row,
            **updates,
            function_type=(
                self.get_function_type(tenant_id, updates["function_type_id"])
                if "function_type_id" in updates and updates["function_type_id"]
                else (None if "function_type_id" in updates else row.function_type)
            ),
            qualification_type=(
                self.get_qualification_type(tenant_id, updates["qualification_type_id"])
                if "qualification_type_id" in updates and updates["qualification_type_id"]
                else (None if "qualification_type_id" in updates else row.qualification_type)
            ),
            version_no=row.version_no + 1,
            updated_by_user_id=actor_user_id,
            updated_at=datetime.now(UTC),
        )
        card.rate_lines = [next_row if line.id == rate_line_id else line for line in card.rate_lines]
        return next_row

    def find_duplicate_rate_line(self, tenant_id: str, rate_card_id: str, *, line_kind: str, function_type_id: str | None, qualification_type_id: str | None, planning_mode_code: str | None, billing_unit: str, exclude_id: str | None = None) -> FakeRateLine | None:
        return next(
            (
                row
                for row in self.list_rate_lines(tenant_id, rate_card_id)
                if row.id != exclude_id
                and row.archived_at is None
                and row.line_kind == line_kind
                and row.function_type_id == function_type_id
                and row.qualification_type_id == qualification_type_id
                and row.planning_mode_code == planning_mode_code
                and row.billing_unit == billing_unit
            ),
            None,
        )

    def list_surcharge_rules(self, tenant_id: str, rate_card_id: str) -> list[FakeSurchargeRule]:
        card = self._find_card_by_id(tenant_id, rate_card_id)
        return list(card.surcharge_rules if card else [])

    def get_surcharge_rule(self, tenant_id: str, rate_card_id: str, surcharge_rule_id: str) -> FakeSurchargeRule | None:
        card = self._find_card_by_id(tenant_id, rate_card_id)
        if card is None:
            return None
        return next((row for row in card.surcharge_rules if row.id == surcharge_rule_id), None)

    def create_surcharge_rule(self, tenant_id: str, rate_card_id: str, payload: CustomerSurchargeRuleCreate, actor_user_id: str | None):
        card = self._find_card_by_id(tenant_id, rate_card_id)
        row = FakeSurchargeRule(
            id=str(uuid4()),
            tenant_id=tenant_id,
            rate_card_id=rate_card_id,
            surcharge_type=payload.surcharge_type,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            weekday_mask=payload.weekday_mask,
            time_from_minute=payload.time_from_minute,
            time_to_minute=payload.time_to_minute,
            region_code=payload.region_code,
            percent_value=payload.percent_value,
            fixed_amount=payload.fixed_amount,
            currency_code=payload.currency_code,
            sort_order=payload.sort_order,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        assert card is not None
        card.surcharge_rules.append(row)
        return row

    def _find_card_by_id(self, tenant_id: str, rate_card_id: str) -> FakeRateCard | None:
        for rows in self.rate_cards.values():
            for row in rows:
                if row.tenant_id == tenant_id and row.id == rate_card_id:
                    return row
        return None


class TestCustomerPricingMetadata(unittest.TestCase):
    def test_pricing_tables_are_registered(self) -> None:
        self.assertIn("crm.customer_rate_card", Base.metadata.tables)
        self.assertIn("crm.customer_rate_line", Base.metadata.tables)
        self.assertIn("crm.customer_surcharge_rule", Base.metadata.tables)

    def test_pricing_tables_use_uuid_scope_columns(self) -> None:
        for table_name, column_names in (
            ("crm.customer_rate_card", ("tenant_id", "customer_id", "id", "created_by_user_id", "updated_by_user_id")),
            (
                "crm.customer_rate_line",
                (
                    "tenant_id",
                    "rate_card_id",
                    "function_type_id",
                    "qualification_type_id",
                    "id",
                    "created_by_user_id",
                    "updated_by_user_id",
                ),
            ),
            (
                "crm.customer_surcharge_rule",
                ("tenant_id", "rate_card_id", "id", "created_by_user_id", "updated_by_user_id"),
            ),
        ):
            table = Base.metadata.tables[table_name]
            for column_name in column_names:
                with self.subTest(table=table_name, column=column_name):
                    self.assertIsInstance(table.c[column_name].type, postgresql.UUID)

    def test_rate_line_uses_hr_catalog_foreign_keys(self) -> None:
        names = {constraint.name for constraint in CustomerRateLine.__table__.constraints if getattr(constraint, "name", None)}
        self.assertIn("fk_crm_customer_rate_line_tenant_function_type", names)
        self.assertIn("fk_crm_customer_rate_line_tenant_qualification_type", names)

    def test_pricing_tables_have_effective_window_checks(self) -> None:
        names = {
            constraint.name
            for constraint in CustomerRateCard.__table__.constraints.union(CustomerSurchargeRule.__table__.constraints)
            if isinstance(constraint, CheckConstraint)
        }
        self.assertTrue(any(name.endswith("crm_customer_rate_card_effective_window_valid") for name in names))
        self.assertTrue(any(name.endswith("crm_customer_surcharge_rule_effective_window_valid") for name in names))


class TestCustomerPricingService(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakePricingRepository()
        self.audit_repo = RecordingAuditRepository()
        self.service = CustomerCommercialService(self.repository, audit_service=AuditService(self.audit_repo))
        self.customer = CustomerService(self.repository).create_customer(
            "tenant-1",
            CustomerCreate(tenant_id="tenant-1", customer_number="K-2000", name="Atlas Security GmbH"),
            _actor(),
        )
        self.function_type_id = "55555555-5555-4555-8555-555555555555"
        self.qualification_type_id = "66666666-6666-4666-8666-666666666666"

    def test_rate_cards_reject_overlapping_windows_for_same_kind(self) -> None:
        self.service.create_rate_card(
            "tenant-1",
            self.customer.id,
            CustomerRateCardCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                rate_kind="guarding",
                currency_code="eur",
                effective_from=date(2026, 1, 1),
                effective_to=date(2026, 3, 31),
            ),
            _actor(),
        )

        with self.assertRaises(ApiException) as context:
            self.service.create_rate_card(
                "tenant-1",
                self.customer.id,
                CustomerRateCardCreate(
                    tenant_id="tenant-1",
                    customer_id=self.customer.id,
                    rate_kind="guarding",
                    currency_code="EUR",
                    effective_from=date(2026, 3, 1),
                    effective_to=date(2026, 4, 30),
                ),
                _actor(),
            )

        self.assertEqual(context.exception.code, "customers.conflict.rate_card_overlap")

    def test_rate_line_dimension_uniqueness_is_enforced_per_card(self) -> None:
        rate_card = self.service.create_rate_card(
            "tenant-1",
            self.customer.id,
            CustomerRateCardCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                rate_kind="alarm",
                currency_code="EUR",
                effective_from=date(2026, 1, 1),
            ),
            _actor(),
        )
        self.service.create_rate_line(
            "tenant-1",
            self.customer.id,
            rate_card.id,
            CustomerRateLineCreate(
                tenant_id="tenant-1",
                rate_card_id=rate_card.id,
                line_kind="base",
                billing_unit="hour",
                planning_mode_code="standard",
                unit_price=Decimal("22.50"),
            ),
            _actor(),
        )

        with self.assertRaises(ApiException) as context:
            self.service.create_rate_line(
                "tenant-1",
                self.customer.id,
                rate_card.id,
                CustomerRateLineCreate(
                    tenant_id="tenant-1",
                    rate_card_id=rate_card.id,
                    line_kind="base",
                    billing_unit="hour",
                    planning_mode_code="standard",
                    unit_price=Decimal("25.00"),
                ),
                _actor(),
            )

        self.assertEqual(context.exception.code, "customers.conflict.rate_line_duplicate")

    def test_surcharge_rules_validate_masks_and_amount_combinations(self) -> None:
        rate_card = self.service.create_rate_card(
            "tenant-1",
            self.customer.id,
            CustomerRateCardCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                rate_kind="guarding",
                currency_code="EUR",
                effective_from=date(2026, 1, 1),
                effective_to=date(2026, 12, 31),
            ),
            _actor(),
        )

        with self.assertRaises(ApiException) as mask_context:
            self.service.create_surcharge_rule(
                "tenant-1",
                self.customer.id,
                rate_card.id,
                CustomerSurchargeRuleCreate(
                    tenant_id="tenant-1",
                    rate_card_id=rate_card.id,
                    surcharge_type="night",
                    effective_from=date(2026, 1, 1),
                    effective_to=date(2026, 12, 31),
                    weekday_mask="11x1111",
                    percent_value=Decimal("25.00"),
                ),
                _actor(),
            )
        with self.assertRaises(ApiException) as amount_context:
            self.service.create_surcharge_rule(
                "tenant-1",
                self.customer.id,
                rate_card.id,
                CustomerSurchargeRuleCreate(
                    tenant_id="tenant-1",
                    rate_card_id=rate_card.id,
                    surcharge_type="weekend",
                    effective_from=date(2026, 1, 1),
                    effective_to=date(2026, 12, 31),
                    percent_value=Decimal("20.00"),
                    fixed_amount=Decimal("10.00"),
                    currency_code="EUR",
                ),
                _actor(),
            )

        self.assertEqual(mask_context.exception.code, "customers.validation.surcharge_rule_weekday_mask")
        self.assertEqual(amount_context.exception.code, "customers.validation.surcharge_rule_amount_combination")

    def test_rate_line_rejects_unknown_function_and_qualification_catalog_ids(self) -> None:
        rate_card = self.service.create_rate_card(
            "tenant-1",
            self.customer.id,
            CustomerRateCardCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                rate_kind="guarding",
                currency_code="EUR",
                effective_from=date(2026, 1, 1),
            ),
            _actor(),
        )

        with self.assertRaises(ApiException) as function_context:
            self.service.create_rate_line(
                "tenant-1",
                self.customer.id,
                rate_card.id,
                CustomerRateLineCreate(
                    tenant_id="tenant-1",
                    rate_card_id=rate_card.id,
                    line_kind="base",
                    function_type_id=str(uuid4()),
                    billing_unit="hour",
                    unit_price=Decimal("25.00"),
                ),
                _actor(),
            )
        with self.assertRaises(ApiException) as qualification_context:
            self.service.create_rate_line(
                "tenant-1",
                self.customer.id,
                rate_card.id,
                CustomerRateLineCreate(
                    tenant_id="tenant-1",
                    rate_card_id=rate_card.id,
                    line_kind="base",
                    qualification_type_id=str(uuid4()),
                    billing_unit="hour",
                    unit_price=Decimal("25.00"),
                ),
                _actor(),
            )

        self.assertEqual(function_context.exception.code, "customers.validation.rate_line_function_type")
        self.assertEqual(qualification_context.exception.code, "customers.validation.rate_line_qualification_type")

    def test_pricing_profile_exposes_finance_read_contract(self) -> None:
        rate_card = self.service.create_rate_card(
            "tenant-1",
            self.customer.id,
            CustomerRateCardCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                rate_kind="guarding",
                currency_code="EUR",
                effective_from=date(2026, 4, 1),
            ),
            _actor(),
        )
        self.service.create_rate_line(
            "tenant-1",
            self.customer.id,
            rate_card.id,
            CustomerRateLineCreate(
                tenant_id="tenant-1",
                rate_card_id=rate_card.id,
                line_kind="base",
                function_type_id=self.function_type_id,
                qualification_type_id=self.qualification_type_id,
                planning_mode_code="release",
                billing_unit="hour",
                unit_price=Decimal("23.40"),
            ),
            _actor(),
        )
        self.service.create_surcharge_rule(
            "tenant-1",
            self.customer.id,
            rate_card.id,
            CustomerSurchargeRuleCreate(
                tenant_id="tenant-1",
                rate_card_id=rate_card.id,
                surcharge_type="night",
                effective_from=date(2026, 4, 1),
                percent_value=Decimal("25.00"),
            ),
            _actor(),
        )

        pricing = self.service.get_pricing_profile("tenant-1", self.customer.id, _actor())

        self.assertEqual(pricing.customer_id, self.customer.id)
        self.assertEqual(len(pricing.rate_cards), 1)
        self.assertEqual(pricing.rate_cards[0].currency_code, "EUR")
        self.assertEqual(pricing.rate_cards[0].rate_lines[0].function_type_id, self.function_type_id)
        self.assertEqual(pricing.rate_cards[0].rate_lines[0].function_type.code, "SEC_GUARD")
        self.assertEqual(pricing.rate_cards[0].rate_lines[0].qualification_type.code, "G34A")
        self.assertEqual(pricing.rate_cards[0].surcharge_rules[0].surcharge_type, "night")
        self.assertGreaterEqual(len(self.audit_repo.audit_events), 3)

    def test_migration_normalizes_only_real_hr_catalog_uuid_references(self) -> None:
        migration_sql = Path("backend/alembic/versions/0058_customer_rate_line_hr_catalog_refs.py").read_text(encoding="utf-8")

        self.assertIn("func-guard", migration_sql)
        self.assertIn("qualification_type_id_uuid", migration_sql)
        self.assertIn("function_type_id ~*", migration_sql)
        self.assertIn("qualification_type_id ~*", migration_sql)
        self.assertIn("FROM hr.function_type", migration_sql)
        self.assertIn("FROM hr.qualification_type", migration_sql)


if __name__ == "__main__":
    unittest.main()
