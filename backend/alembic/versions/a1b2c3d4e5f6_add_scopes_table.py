"""add scopes table

Revision ID: a1b2c3d4e5f6
Revises: 36373c67bbee
Create Date: 2025-10-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "36373c67bbee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create scopes table
    op.create_table(
        "scope",
        sa.Column("scope_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("scope_id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_scope_name"), "scope", ["name"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_scope_name"), table_name="scope")
    op.drop_table("scope")
