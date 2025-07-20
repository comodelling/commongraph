"""add is_super_admin to user

Revision ID: f9a8b1c2d3e4
Revises: 8f0c3ed2c2a8
Create Date: 2025-07-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9a8b1c2d3e4'
down_revision: Union[str, None] = '8f0c3ed2c2a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the is_super_admin column with default value False
    op.add_column('user', sa.Column('is_super_admin', sa.Boolean(), nullable=True, server_default=sa.text("false")))
    
    # Backfill existing rows
    op.execute('UPDATE "user" SET is_super_admin = false WHERE is_super_admin IS NULL')
    
    # Make the column NOT NULL after backfilling
    op.alter_column('user', 'is_super_admin', nullable=False)


def downgrade() -> None:
    # Remove the is_super_admin column
    op.drop_column('user', 'is_super_admin')
