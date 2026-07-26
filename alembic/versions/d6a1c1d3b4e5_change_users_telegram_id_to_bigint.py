"""change users.telegram_id to bigint

Revision ID: d6a1c1d3b4e5
Revises: 7ed3dfc7575a
Create Date: 2026-07-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6a1c1d3b4e5'
down_revision: Union[str, Sequence[str], None] = '7ed3dfc7575a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'users',
        'telegram_id',
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=True,
        postgresql_using='telegram_id::bigint',
    )


def downgrade() -> None:
    op.alter_column(
        'users',
        'telegram_id',
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using='telegram_id::integer',
    )
