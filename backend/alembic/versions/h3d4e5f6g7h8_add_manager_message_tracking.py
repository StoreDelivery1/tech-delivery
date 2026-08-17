"""add_manager_message_tracking

Revision ID: h3d4e5f6g7h8
Revises: g2c3d4e5f6g7
Create Date: 2026-07-27 14:23:45.123456

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'h3d4e5f6g7h8'
down_revision: Union[str, Sequence[str], None] = 'g2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('manager_chat_id', sa.BigInteger(), nullable=True))
    op.add_column('orders', sa.Column('manager_message_id', sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column('orders', 'manager_message_id')
    op.drop_column('orders', 'manager_chat_id')
