"""add is_first_login column

Revision ID: 7b90543e559f
Revises: b69fb50d5b5d
Create Date: 2026-01-18 22:57:17.717104

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b90543e559f'
down_revision = 'b69fb50d5b5d'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_first_login column to users table with default value for existing rows
    op.add_column('users', sa.Column('is_first_login', sa.Boolean(), nullable=True, default=True), schema='memotion')
    # Update existing rows to have default value
    op.execute("UPDATE memotion.users SET is_first_login = true WHERE is_first_login IS NULL")
    # Make column not nullable
    op.alter_column('users', 'is_first_login', nullable=False, schema='memotion')


def downgrade():
    # Remove is_first_login column from users table
    op.drop_column('users', 'is_first_login', schema='memotion')


def downgrade():
    pass
