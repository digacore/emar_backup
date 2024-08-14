"""1024_in_backup_log

Revision ID: 225016f12bd4
Revises: 356e5c8ad8e8
Create Date: 2024-05-28 15:43:01.641492

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '225016f12bd4'
down_revision = '356e5c8ad8e8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('backup_logs', 'error',
               existing_type=sa.VARCHAR(length=128),
               type_=sa.String(length=1024),
               existing_nullable=True,
               existing_server_default=sa.text("''::character varying"))
    op.alter_column('backup_logs', 'notes',
               existing_type=sa.VARCHAR(length=128),
               type_=sa.String(length=1024),
               existing_nullable=True,
               existing_server_default=sa.text("''::character varying"))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('backup_logs', 'notes',
               existing_type=sa.String(length=1024),
               type_=sa.VARCHAR(length=128),
               existing_nullable=True,
               existing_server_default=sa.text("''::character varying"))
    op.alter_column('backup_logs', 'error',
               existing_type=sa.String(length=1024),
               type_=sa.VARCHAR(length=128),
               existing_nullable=True,
               existing_server_default=sa.text("''::character varying"))
    # ### end Alembic commands ###
