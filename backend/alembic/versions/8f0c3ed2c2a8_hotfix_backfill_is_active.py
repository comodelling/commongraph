"""hotfix: backfill is_active

Revision ID: 8f0c3ed2c2a8
Revises: de8b3bb22e53
Create Date: 2025-06-25 23:46:06.918920

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f0c3ed2c2a8'
down_revision: Union[str, None] = 'de8b3bb22e53'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('UPDATE "user" SET is_active = TRUE WHERE is_active IS DISTINCT FROM TRUE;')


def downgrade() -> None:
    op.execute('UPDATE "user" SET is_active = FALSE;')