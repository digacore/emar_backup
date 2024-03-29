"""primary_alternate_device

Revision ID: f680e9979d73
Revises: 6e7842b97fdb
Create Date: 2023-09-26 18:11:09.132550

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "f680e9979d73"
down_revision = "6e7842b97fdb"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    device_type = postgresql.ENUM(
        "LAPTOP",
        "DESKTOP",
        name="devicetype",
    )
    device_type.create(op.get_bind())

    device_role = postgresql.ENUM(
        "PRIMARY",
        "ALTERNATE",
        name="devicerole",
    )
    device_role.create(op.get_bind())

    op.add_column(
        "computers",
        sa.Column(
            "device_type",
            sa.Enum("LAPTOP", "DESKTOP", name="devicetype"),
            nullable=True,
        ),
    )
    op.add_column(
        "computers",
        sa.Column(
            "device_role",
            sa.Enum("PRIMARY", "ALTERNATE", name="devicerole"),
            server_default=sa.text("'PRIMARY'"),
            nullable=False,
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("computers", "device_role")
    op.drop_column("computers", "device_type")

    device_type = postgresql.ENUM(
        "LAPTOP",
        "DESKTOP",
        name="devicetype",
    )
    device_type.drop(op.get_bind())

    device_role = postgresql.ENUM(
        "PRIMARY",
        "ALTERNATE",
        name="devicerole",
    )
    device_role.drop(op.get_bind())
    # ### end Alembic commands ###
