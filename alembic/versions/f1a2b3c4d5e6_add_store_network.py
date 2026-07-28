"""add store network column

Revision ID: f1a2b3c4d5e6
Revises: c97fcdf90e89
Create Date: 2026-07-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'd6a1c1d3b4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('stores', sa.Column('network', sa.String(length=50), nullable=True))
    op.execute("UPDATE stores SET network = 'APPLE_ROOM' WHERE network IS NULL")
    op.alter_column('stores', 'network', nullable=False)


def downgrade() -> None:
    op.drop_column('stores', 'network')
