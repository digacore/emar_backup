"""last_saved_path

Revision ID: a6a760e24123
Revises: f646e7bf3921
Create Date: 2023-08-09 14:51:26.522749

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a6a760e24123'
down_revision = 'f646e7bf3921'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('computers', sa.Column('last_saved_path', sa.String(length=256), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('computers', 'last_saved_path')
    # ### end Alembic commands ###
