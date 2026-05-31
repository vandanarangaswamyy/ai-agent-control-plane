"""create agent registry

Revision ID: 202605310001
Revises:
Create Date: 2026-05-31 00:01:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202605310001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner", sa.String(length=255), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("uq_agents_name_lower", "agents", [sa.text("lower(name)")], unique=True)

    op.create_table(
        "agent_versions",
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=False),
        sa.Column(
            "tool_config",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "runtime_config",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "lifecycle",
            sa.Enum(
                "DRAFT",
                "EVALUATED",
                "APPROVED",
                "PRODUCTION",
                "DEPRECATED",
                name="agentversionlifecycle",
                native_enum=False,
                length=32,
            ),
            server_default="DRAFT",
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("version > 0", name="ck_agent_versions_version_positive"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id", "version", name="uq_agent_versions_agent_id_version"),
    )
    op.create_index(
        op.f("ix_agent_versions_agent_id"),
        "agent_versions",
        ["agent_id"],
        unique=False,
    )
    op.create_index(
        "ix_agent_versions_agent_id_lifecycle",
        "agent_versions",
        ["agent_id", "lifecycle"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_versions_lifecycle"),
        "agent_versions",
        ["lifecycle"],
        unique=False,
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_agent_versions_lifecycle")
    op.execute("DROP INDEX IF EXISTS ix_agent_versions_agent_id_lifecycle")
    op.execute("DROP INDEX IF EXISTS ix_agent_versions_agent_id")
    op.drop_table("agent_versions")
    op.execute("DROP INDEX IF EXISTS uq_agents_name_lower")
    op.execute("DROP INDEX IF EXISTS ix_agents_name")
    op.drop_table("agents")
