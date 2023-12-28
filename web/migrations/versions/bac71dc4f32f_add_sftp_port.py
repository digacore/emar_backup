"""add_sftp_port

Revision ID: bac71dc4f32f
Revises: cd5377f00639
Create Date: 2023-12-14 18:48:01.815678

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bac71dc4f32f'
down_revision = 'cd5377f00639'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('computers', sa.Column('sftp_port', sa.Integer(), server_default='22', nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('computers', 'sftp_port')
    # ### end Alembic commands ###