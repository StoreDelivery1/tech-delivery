"""add courier availability column

Revision ID: g2c3d4e5f6g7
Revises: e9cfea332822
Create Date: 2026-07-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'g2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'e9cfea332822'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('availability', sa.String(length=50), nullable=True))
    op.execute("UPDATE users SET availability = 'OFFLINE' WHERE availability IS NULL")
    op.alter_column('users', 'availability', nullable=False)


def downgrade() -> None:
    op.drop_column('users', 'availability')
