"""add is_active to user

Revision ID: d6c2c5539c74
Revises: 
Create Date: 2025-06-25 23:19:22.953381

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6c2c5539c74'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text("true")))

    # 2) backfill existing rows
    op.execute(
        # set to the same boolean you chose above
        'UPDATE "user" SET is_active = true'
    )

    # ### end Alembic commands ###
    op.alter_column("user", "is_active", nullable=False)
    op.alter_column("user", "is_active", server_default=None)

def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'is_active')
    # ### end Alembic commands ###
