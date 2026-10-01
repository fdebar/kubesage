"""Link watcher incident episodes to their analyses.

Revision ID: bc6ad2f10281
Revises: 2f8a91c6d403
Create Date: 2026-10-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bc6ad2f10281"
down_revision: str | Sequence[str] | None = "2f8a91c6d403"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("watcher_incidents") as batch_op:
        batch_op.add_column(
            sa.Column("analysis_id", sa.String(length=36), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_watcher_incidents_analysis_id_analyses",
            "analyses",
            ["analysis_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("watcher_incidents") as batch_op:
        batch_op.drop_constraint(
            "fk_watcher_incidents_analysis_id_analyses", type_="foreignkey"
        )
        batch_op.drop_column("analysis_id")
