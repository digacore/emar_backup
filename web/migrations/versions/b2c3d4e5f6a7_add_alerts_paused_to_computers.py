"""add alerts_paused to computers

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "computers",
        sa.Column(
            "alerts_paused",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("computers", "alerts_paused")
