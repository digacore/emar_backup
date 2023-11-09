"""soft_delete_location_groups

Revision ID: f5fb40f5eaba
Revises: 9a9e891bb23e
Create Date: 2023-11-09 11:24:53.221205

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f5fb40f5eaba"
down_revision = "9a9e891bb23e"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "location_groups", sa.Column("deleted_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "location_groups",
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
    )
    op.add_column(
        "location_groups",
        sa.Column(
            "is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=True
        ),
    )
    op.create_unique_constraint(
        "unique_location_group_per_company", "location_groups", ["company_id", "name"]
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "unique_location_group_per_company", "location_groups", type_="unique"
    )
    op.drop_column("location_groups", "is_deleted")
    op.drop_column("location_groups", "created_at")
    op.drop_column("location_groups", "deleted_at")
    # ### end Alembic commands ###
