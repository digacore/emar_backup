"""add_company_id_computer_location

Revision ID: 220cf3eb048a
Revises: 683ba442f443
Create Date: 2023-09-26 10:30:49.020106

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '220cf3eb048a'
down_revision = '683ba442f443'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('computers', sa.Column('company_id', sa.Integer(), nullable=True))
    op.add_column('locations', sa.Column('company_id', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('locations', 'company_id')
    op.drop_column('computers', 'company_id')
    # ### end Alembic commands ###
