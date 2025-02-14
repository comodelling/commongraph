"""addentity_type column to ratingevent table

Revision ID: 2f40bcbcab53
Revises: db07fd44a335
Create Date: 2025-02-14 19:34:53.848215

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2f40bcbcab53"
down_revision: Union[str, None] = "db07fd44a335"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ratingevent",
        sa.Column(
            "entity_type",
            sa.Enum("node", "edge", name="entitytype"),
            nullable=False,
            server_default="node",
        ),
    )
    op.execute("ALTER TABLE ratingevent ALTER COLUMN entity_type DROP DEFAULT")


def downgrade() -> None:
    op.drop_column("ratingevent", "entity_type")
