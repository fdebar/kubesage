"""Add persistent watcher state and deduplication caches.

Revision ID: d72c5e4b8a10
Revises: 63c330af54f0
Create Date: 2026-09-28 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d72c5e4b8a10"
down_revision: str | Sequence[str] | None = "63c330af54f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "watcher_pod_states",
        sa.Column("namespace", sa.String(length=255), nullable=False),
        sa.Column("pod_uid", sa.String(length=255), nullable=False),
        sa.Column("state", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("namespace", "pod_uid"),
    )
    op.create_table(
        "incident_deduplication",
        sa.Column("namespace", sa.String(length=255), nullable=False),
        sa.Column("pod_uid", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.String(length=100), nullable=False),
        sa.Column("seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("namespace", "pod_uid", "reason"),
    )
    op.create_index(
        "ix_incident_deduplication_expires_at",
        "incident_deduplication",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_incident_deduplication_expires_at", table_name="incident_deduplication"
    )
    op.drop_table("incident_deduplication")
    op.drop_table("watcher_pod_states")
