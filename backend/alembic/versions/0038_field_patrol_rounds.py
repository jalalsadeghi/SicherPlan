"""field patrol rounds

Revision ID: 0038_field_patrol_rounds
Revises: 0037_field_watchbook_foundation
Create Date: 2026-03-20 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0038_field_patrol_rounds"
down_revision = "0037_field_watchbook_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'field'
                  AND table_name = 'watchbook'
            ) AND NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_field_watchbook_tenant_id_id'
                  AND connamespace = 'field'::regnamespace
            ) THEN
                ALTER TABLE field.watchbook
                ADD CONSTRAINT uq_field_watchbook_tenant_id_id UNIQUE (tenant_id, id);
            END IF;
        END
        $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'ops'
                  AND table_name = 'patrol_route'
            ) AND NOT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'ops'
                  AND table_name = 'patrol_checkpoint'
            ) THEN
                CREATE TABLE ops.patrol_checkpoint (
                    tenant_id UUID NOT NULL,
                    patrol_route_id UUID NOT NULL,
                    sequence_no INTEGER NOT NULL,
                    checkpoint_code VARCHAR(80) NOT NULL,
                    label VARCHAR(255) NOT NULL,
                    scan_type_code VARCHAR(40) NOT NULL,
                    expected_token_value VARCHAR(255),
                    minimum_dwell_seconds INTEGER DEFAULT 0 NOT NULL,
                    latitude NUMERIC(9, 6),
                    longitude NUMERIC(9, 6),
                    notes TEXT,
                    id UUID DEFAULT gen_random_uuid() NOT NULL,
                    status VARCHAR(50) DEFAULT 'active' NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    created_by_user_id UUID,
                    updated_by_user_id UUID,
                    archived_at TIMESTAMP WITH TIME ZONE,
                    version_no INTEGER DEFAULT 1 NOT NULL,
                    CONSTRAINT pk_patrol_checkpoint PRIMARY KEY (id),
                    CONSTRAINT fk_patrol_checkpoint_tenant_id_tenant FOREIGN KEY(tenant_id) REFERENCES core.tenant (id) ON DELETE RESTRICT,
                    CONSTRAINT fk_ops_patrol_checkpoint_tenant_route FOREIGN KEY(tenant_id, patrol_route_id) REFERENCES ops.patrol_route (tenant_id, id) ON DELETE RESTRICT,
                    CONSTRAINT uq_ops_patrol_checkpoint_route_sequence UNIQUE (tenant_id, patrol_route_id, sequence_no),
                    CONSTRAINT uq_ops_patrol_checkpoint_route_code UNIQUE (tenant_id, patrol_route_id, checkpoint_code),
                    CONSTRAINT uq_ops_patrol_checkpoint_tenant_id_id UNIQUE (tenant_id, id),
                    CONSTRAINT ck_ops_patrol_checkpoint_coordinates_valid CHECK (
                        (latitude IS NULL AND longitude IS NULL) OR
                        (latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)
                    ),
                    CONSTRAINT ck_ops_patrol_checkpoint_dwell_non_negative CHECK (minimum_dwell_seconds >= 0)
                );
                CREATE INDEX ix_ops_patrol_checkpoint_route_sequence
                    ON ops.patrol_checkpoint (tenant_id, patrol_route_id, sequence_no);
            END IF;
        END
        $$;
        """
    )
    op.create_table(
        "patrol_round",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("shift_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("planning_record_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("patrol_route_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("watchbook_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("summary_document_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("offline_sync_token", sa.String(length=120), nullable=True),
        sa.Column("round_status_code", sa.String(length=40), nullable=False, server_default="active"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("aborted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("abort_reason_code", sa.String(length=80), nullable=True),
        sa.Column("completion_note", sa.Text(), nullable=True),
        sa.Column("total_checkpoint_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_checkpoint_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.CheckConstraint("round_status_code IN ('active','completed','aborted')", name="ck_patrol_round_status_valid"),
        sa.ForeignKeyConstraint(["tenant_id", "employee_id"], ["hr.employee.tenant_id", "hr.employee.id"], name="fk_field_patrol_round_tenant_employee"),
        sa.ForeignKeyConstraint(["tenant_id", "shift_id"], ["ops.shift.tenant_id", "ops.shift.id"], name="fk_field_patrol_round_tenant_shift"),
        sa.ForeignKeyConstraint(["tenant_id", "planning_record_id"], ["ops.planning_record.tenant_id", "ops.planning_record.id"], name="fk_field_patrol_round_tenant_planning_record"),
        sa.ForeignKeyConstraint(["tenant_id", "patrol_route_id"], ["ops.patrol_route.tenant_id", "ops.patrol_route.id"], name="fk_field_patrol_round_tenant_route"),
        sa.ForeignKeyConstraint(["tenant_id", "watchbook_id"], ["field.watchbook.tenant_id", "field.watchbook.id"], name="fk_field_patrol_round_tenant_watchbook"),
        sa.ForeignKeyConstraint(["summary_document_id"], ["docs.document.id"], name="fk_field_patrol_round_summary_document_id_document"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_field_patrol_round_tenant_id_tenant"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_patrol_round")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_field_patrol_round_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "offline_sync_token", name="uq_field_patrol_round_sync_token"),
        schema="field",
    )
    op.create_index(
        "uq_field_patrol_round_employee_active",
        "patrol_round",
        ["tenant_id", "employee_id"],
        unique=True,
        schema="field",
        postgresql_where=sa.text("round_status_code = 'active' AND archived_at IS NULL"),
    )
    op.create_index("ix_field_patrol_round_route_started_at", "patrol_round", ["tenant_id", "patrol_route_id", "started_at"], unique=False, schema="field")
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'field'
                  AND table_name = 'patrol_round'
            ) AND NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_field_patrol_round_tenant_id_id'
                  AND connamespace = 'field'::regnamespace
            ) THEN
                ALTER TABLE field.patrol_round
                ADD CONSTRAINT uq_field_patrol_round_tenant_id_id UNIQUE (tenant_id, id);
            END IF;
        END
        $$;
        """
    )

    op.create_table(
        "patrol_round_event",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("patrol_round_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("checkpoint_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("event_type_code", sa.String(length=60), nullable=False),
        sa.Column("scan_method_code", sa.String(length=40), nullable=True),
        sa.Column("token_value", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("reason_code", sa.String(length=80), nullable=True),
        sa.Column("client_event_id", sa.String(length=120), nullable=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("is_policy_compliant", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.CheckConstraint("event_type_code IN ('round_started','checkpoint_scanned','checkpoint_exception','round_completed','round_aborted')", name="ck_patrol_round_event_type_valid"),
        sa.CheckConstraint("scan_method_code IS NULL OR scan_method_code IN ('system','qr','barcode','nfc','manual')", name="ck_patrol_round_event_scan_method_valid"),
        sa.CheckConstraint("(latitude IS NULL AND longitude IS NULL) OR (latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)", name="ck_patrol_round_event_coordinates_valid"),
        sa.ForeignKeyConstraint(["tenant_id", "patrol_round_id"], ["field.patrol_round.tenant_id", "field.patrol_round.id"], name="fk_field_patrol_round_event_tenant_round", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "checkpoint_id"], ["ops.patrol_checkpoint.tenant_id", "ops.patrol_checkpoint.id"], name="fk_field_patrol_round_event_tenant_checkpoint"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["iam.user_account.id"], name="fk_field_patrol_round_event_actor_user_id_user_account"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_field_patrol_round_event_tenant_id_tenant"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_patrol_round_event")),
        sa.UniqueConstraint("tenant_id", "patrol_round_id", "sequence_no", name="uq_field_patrol_round_event_round_sequence"),
        sa.UniqueConstraint("tenant_id", "patrol_round_id", "client_event_id", name="uq_field_patrol_round_event_client_event"),
        schema="field",
    )
    op.create_index("ix_field_patrol_round_event_round_occurred_at", "patrol_round_event", ["tenant_id", "patrol_round_id", "occurred_at"], unique=False, schema="field")


def downgrade() -> None:
    op.drop_index("ix_field_patrol_round_event_round_occurred_at", table_name="patrol_round_event", schema="field")
    op.drop_table("patrol_round_event", schema="field")
    op.drop_index("ix_field_patrol_round_route_started_at", table_name="patrol_round", schema="field")
    op.drop_index("uq_field_patrol_round_employee_active", table_name="patrol_round", schema="field")
    op.drop_table("patrol_round", schema="field")
