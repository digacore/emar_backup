"""add_flag_id_desktop_client

Revision ID: 614e71ec07ce
Revises: 194cdc9cc3a3
Create Date: 2023-09-26 12:51:33.853600

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '614e71ec07ce'
down_revision = '194cdc9cc3a3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('desktop_clients', sa.Column('flag_id', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('desktop_clients', 'flag_id')
    # ### end Alembic commands ###