# SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""merge_heads

Revision ID: 36373c67bbee
Revises: 0b52894be80f, f9a8b1c2d3e4
Create Date: 2025-07-20 13:03:26.869116

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "36373c67bbee"
down_revision: Union[str, None] = ("0b52894be80f", "f9a8b1c2d3e4")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
