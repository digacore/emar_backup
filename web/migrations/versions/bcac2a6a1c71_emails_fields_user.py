"""emails_fields_user

Revision ID: bcac2a6a1c71
Revises: fa64ea171be2
Create Date: 2024-09-12 15:15:40.686337

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bcac2a6a1c71'
down_revision = 'fa64ea171be2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('receive_alert_emails', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('receive_summaries_emails', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('receive_device_test_emails', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'receive_device_test_emails')
    op.drop_column('users', 'receive_summaries_emails')
    op.drop_column('users', 'receive_alert_emails')
    # ### end Alembic commands ###