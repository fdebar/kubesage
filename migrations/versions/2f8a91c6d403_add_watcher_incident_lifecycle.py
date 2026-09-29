"""Add persistent watcher incident lifecycle.

Revision ID: 2f8a91c6d403
Revises: d72c5e4b8a10
Create Date: 2026-09-29 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2f8a91c6d403"
down_revision: str | Sequence[str] | None = "d72c5e4b8a10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "watcher_incidents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("namespace", sa.String(length=255), nullable=False),
        sa.Column("pod_uid", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.String(length=100), nullable=False),
        sa.Column("pod", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_resource_version", sa.String(length=255), nullable=True),
        sa.Column("message", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_watcher_incidents_status",
        "watcher_incidents",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_watcher_incidents_pod_reason_status",
        "watcher_incidents",
        ["namespace", "pod_uid", "reason", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_watcher_incidents_pod_reason_status",
        table_name="watcher_incidents",
    )
    op.drop_index("ix_watcher_incidents_status", table_name="watcher_incidents")
    op.drop_table("watcher_incidents")
