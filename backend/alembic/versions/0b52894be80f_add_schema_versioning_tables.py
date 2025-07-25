"""add schema versioning tables

Revision ID: 0b52894be80f
Revises: 8f0c3ed2c2a8
Create Date: 2025-06-28 15:42:14.950707

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b52894be80f'
down_revision: Union[str, None] = '8f0c3ed2c2a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('graphschema',
    sa.Column('schema_id', sa.Integer(), nullable=False),
    sa.Column('version', sa.String(), nullable=False),
    sa.Column('config_hash', sa.String(), nullable=False),
    sa.Column('node_types', sa.JSON(), nullable=False),
    sa.Column('edge_types', sa.JSON(), nullable=False),
    sa.Column('polls', sa.JSON(), nullable=False),
    sa.Column('auth', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('schema_id')
    )
    op.create_table('schemamigration',
    sa.Column('migration_id', sa.Integer(), nullable=False),
    sa.Column('from_version', sa.String(), nullable=False),
    sa.Column('to_version', sa.String(), nullable=False),
    sa.Column('migration_type', sa.String(), nullable=False),
    sa.Column('changes', sa.JSON(), nullable=False),
    sa.Column('applied_at', sa.DateTime(), nullable=False),
    sa.Column('applied_by', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('migration_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('schemamigration')
    op.drop_table('graphschema')
    # ### end Alembic commands ###
