"""creation_report_foreign_keys

Revision ID: dd1be74b7454
Revises: e7b58bd0e419
Create Date: 2023-09-08 13:52:12.596731

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "dd1be74b7454"
down_revision = "e7b58bd0e419"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "pcc_creation_reports",
        sa.Column("status_changed_by_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_status_changed_by_id_users",
        "pcc_creation_reports",
        "users",
        ["status_changed_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_company_id_companies",
        "pcc_creation_reports",
        "companies",
        ["company_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_column("pcc_creation_reports", "status_changed_by")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "pcc_creation_reports",
        sa.Column(
            "status_changed_by",
            sa.VARCHAR(length=255),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.drop_constraint(
        "fk_status_changed_by_id_users", "pcc_creation_reports", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_company_id_companies", "pcc_creation_reports", type_="foreignkey"
    )
    op.drop_column("pcc_creation_reports", "status_changed_by_id")
    # ### end Alembic commands ###
