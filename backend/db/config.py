# SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from sqlalchemy import create_engine
from sqlmodel import SQLModel

_engine = None


def get_engine(database_url: str):
    global _engine
    if _engine is None:
        _engine = create_engine(database_url)
        SQLModel.metadata.create_all(_engine)
    return _engine
