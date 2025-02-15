"""generate rating table

Revision ID: db07fd44a335
Revises: f318a73f684d
Create Date: 2025-02-14 18:47:50.583197

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "db07fd44a335"
down_revision: Union[str, None] = "f318a73f684d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user table if it doesn't exist
    if not op.get_bind().dialect.has_table(op.get_bind(), "user"):
        op.create_table(
            "user",
            sa.Column("username", sa.VARCHAR(), nullable=False),
            sa.Column("password", sa.VARCHAR(), nullable=False),
            sa.Column("preferences", sa.JSON(), nullable=True),
            sa.Column("security_question", sa.VARCHAR(), nullable=True),
            sa.Column("security_answer", sa.VARCHAR(), nullable=True),
            sa.PrimaryKeyConstraint("username", name="user_pkey"),
        )
        op.create_index("ix_user_username", "user", ["username"], unique=False)

    # Create graphhistoryevent table if it doesn't exist
    if not op.get_bind().dialect.has_table(op.get_bind(), "graphhistoryevent"):
        op.create_table(
            "graphhistoryevent",
            sa.Column("event_id", sa.INTEGER(), autoincrement=True, nullable=False),
            sa.Column("timestamp", sa.TIMESTAMP(), nullable=False),
            sa.Column(
                "state",
                sa.Enum("created", "updated", "deleted", name="entitystate"),
                nullable=False,
            ),
            sa.Column(
                "entity_type",
                sa.Enum("node", "edge", name="entitytype"),
                nullable=False,
            ),
            sa.Column("node_id", sa.INTEGER(), nullable=True),
            sa.Column("source_id", sa.INTEGER(), nullable=True),
            sa.Column("target_id", sa.INTEGER(), nullable=True),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("username", sa.VARCHAR(), nullable=False),
            sa.PrimaryKeyConstraint("event_id", name="graphhistoryevent_pkey"),
        )

    # Create ratingevent table if it doesn't exist
    if not op.get_bind().dialect.has_table(op.get_bind(), "ratingevent"):
        op.create_table(
            "ratingevent",
            sa.Column("event_id", sa.INTEGER(), autoincrement=True, nullable=False),
            sa.Column("node_id", sa.INTEGER(), nullable=True),
            sa.Column("source_id", sa.INTEGER(), nullable=True),
            sa.Column("target_id", sa.INTEGER(), nullable=True),
            sa.Column("rating_type", sa.VARCHAR(), nullable=False),
            sa.Column(
                "rating",
                sa.Enum("A", "B", "C", "D", "E", name="likertscale"),
                nullable=False,
            ),
            sa.Column("timestamp", sa.TIMESTAMP(), nullable=False),
            sa.Column("username", sa.VARCHAR(), nullable=False),
            sa.Column(
                "entity_type",
                sa.Enum("node", "edge", name="entitytype"),
                nullable=False,
                server_default="node",
            ),
            sa.PrimaryKeyConstraint("event_id", name="ratingevent_pkey"),
        )


def downgrade() -> None:
    # Drop ratingevent table if it exists
    if op.get_bind().dialect.has_table(op.get_bind(), "ratingevent"):
        op.drop_table("ratingevent")

    # Drop graphhistoryevent table if it exists
    if op.get_bind().dialect.has_table(op.get_bind(), "graphhistoryevent"):
        op.drop_table("graphhistoryevent")

    # Drop user table if it exists
    if op.get_bind().dialect.has_table(op.get_bind(), "user"):
        op.drop_table("user")
