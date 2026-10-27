"""Allow only one unfinished run per requested review."""

from alembic import op
import sqlalchemy as sa

revision = "0002_one_active_run"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Protect active-run uniqueness at the database boundary."""
    op.create_index(
        "uq_runs_active_requested_review",
        "runs",
        ["requested_review_id"],
        unique=True,
        sqlite_where=sa.text("status IN ('queued', 'running', 'interrupted')"),
        postgresql_where=sa.text("status IN ('queued', 'running', 'interrupted')"),
    )


def downgrade() -> None:
    """Remove the partial active-run constraint."""
    op.drop_index("uq_runs_active_requested_review", table_name="runs")
