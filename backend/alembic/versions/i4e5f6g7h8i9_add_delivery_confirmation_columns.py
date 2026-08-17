"""add_delivery_confirmation_columns

Revision ID: i4e5f6g7h8i9
Revises: h3d4e5f6g7h8
Create Date: 2026-07-28 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'i4e5f6g7h8i9'
down_revision: Union[str, Sequence[str], None] = 'h3d4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add confirmed_at column for tracking when delivery was confirmed
    op.add_column('orders', sa.Column('confirmed_at', sa.DateTime(), nullable=True))
    
    # Add problem_reported_at column for tracking when delivery problem was reported
    op.add_column('orders', sa.Column('problem_reported_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove in reverse order
    op.drop_column('orders', 'problem_reported_at')
    op.drop_column('orders', 'confirmed_at')
