"""add order size and remove estimated weight

Revision ID: e9cfea332822
Revises: f1a2b3c4d5e6
Create Date: 2026-07-27 13:11:05.943817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9cfea332822'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("orders")}

    if "size" not in existing_columns:
        op.add_column(
            'orders',
            sa.Column(
                'size',
                sa.Enum('SMALL', 'MEDIUM', 'LARGE', name='ordersize', native_enum=False),
                nullable=True,
            ),
        )

    if "estimated_weight" in existing_columns:
        op.execute(
            "UPDATE orders SET size = 'SMALL' WHERE size IS NULL AND estimated_weight IS NOT NULL"
        )
        op.drop_column('orders', 'estimated_weight')


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("orders")}

    if "size" in existing_columns:
        op.drop_column('orders', 'size')

    if "estimated_weight" not in existing_columns:
        op.add_column('orders', sa.Column('estimated_weight', sa.Float(), nullable=True))
