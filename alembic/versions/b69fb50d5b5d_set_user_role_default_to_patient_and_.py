"""Set user role default to PATIENT and make not nullable

Revision ID: b69fb50d5b5d
Revises: 7f8305c6709f
Create Date: 2026-01-12 16:49:00.862658

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b69fb50d5b5d'
down_revision = '7f8305c6709f'
branch_labels = None
depends_on = None


def upgrade():
    # Update existing null roles to PATIENT
    op.execute("UPDATE users SET role = 'PATIENT' WHERE role IS NULL")
    
    # Alter column to not nullable with default
    op.alter_column('users', 'role',
                    existing_type=sa.String(20),
                    nullable=False,
                    server_default='PATIENT')


def downgrade():
    # Revert to nullable
    op.alter_column('users', 'role',
                    existing_type=sa.String(20),
                    nullable=True,
                    server_default=None)
