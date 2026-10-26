"""Initial Paper Review schema.

Revision ID: 0001_initial
Revises:
"""

from alembic import op

from app.infrastructure.persistence.orm_models import Base

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial versioned entities."""
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    """Remove the initial schema."""
    Base.metadata.drop_all(bind=op.get_bind())

