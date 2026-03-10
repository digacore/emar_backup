"""add alert_settings table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-02-02

"""
from alembic import op
from sqlalchemy import text
import sqlalchemy as sa


revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "alert_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("support_emails", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    conn = op.get_bind()
    conn.execute(
        text(
            "INSERT INTO alert_settings (id, support_emails, updated_at) VALUES (1, '', CURRENT_TIMESTAMP)"
        )
    )


def downgrade():
    op.drop_table("alert_settings")
