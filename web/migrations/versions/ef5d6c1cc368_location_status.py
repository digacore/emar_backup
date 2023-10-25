"""location_status

Revision ID: ef5d6c1cc368
Revises: 3ab2ceb40929
Create Date: 2023-10-25 13:08:55.455264

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "ef5d6c1cc368"
down_revision = "3ab2ceb40929"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    location_status = postgresql.ENUM(
        "ONLINE",
        "ONLINE_PRIMARY_OFFLINE",
        "OFFLINE",
        name="locationstatus",
    )
    location_status.create(op.get_bind())

    op.add_column(
        "locations",
        sa.Column(
            "status",
            sa.Enum(
                "ONLINE", "ONLINE_PRIMARY_OFFLINE", "OFFLINE", name="locationstatus"
            ),
            nullable=True,
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("locations", "status")

    location_status = postgresql.ENUM(
        "ONLINE",
        "ONLINE_PRIMARY_OFFLINE",
        "OFFLINE",
        name="locationstatus",
    )
    location_status.drop(op.get_bind())
    # ### end Alembic commands ###