"""Make user role nullable

Revision ID: 7f8305c6709f
Revises: 87e7271aed8b
Create Date: 2026-01-12 16:35:19.332140

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f8305c6709f'
down_revision = '87e7271aed8b'
branch_labels = None
depends_on = None


def upgrade():
    # Make role column nullable in users table
    op.alter_column('users', 'role', nullable=True)


def downgrade():
    # Make role column not nullable in users table
    op.alter_column('users', 'role', nullable=False)
