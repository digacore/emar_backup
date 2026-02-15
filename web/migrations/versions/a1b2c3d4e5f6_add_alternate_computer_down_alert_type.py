"""add ALTERNATE_COMPUTER_DOWN to alerteventtype

Revision ID: a1b2c3d4e5f6
Revises: bcac2a6a1c71
Create Date: 2026-02-03

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "bcac2a6a1c71"
branch_labels = None
depends_on = None


def upgrade():
    # Add new value to existing PostgreSQL enum (cannot remove enum values in downgrade easily)
    op.execute("ALTER TYPE alerteventtype ADD VALUE 'ALTERNATE_COMPUTER_DOWN'")


def downgrade():
    # PostgreSQL does not support removing enum values; no-op
    pass
