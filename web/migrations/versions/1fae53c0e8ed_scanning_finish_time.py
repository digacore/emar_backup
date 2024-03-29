"""scanning_finish_time

Revision ID: 1fae53c0e8ed
Revises: 98ae0eab3662
Create Date: 2023-09-01 15:05:41.083430

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1fae53c0e8ed'
down_revision = '98ae0eab3662'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pcc_activations_scans', sa.Column('finished_at', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('pcc_activations_scans', 'finished_at')
    # ### end Alembic commands ###
