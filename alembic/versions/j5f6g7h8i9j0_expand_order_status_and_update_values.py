"""expand_order_status_and_update_values

Revision ID: j5f6g7h8i9j0
Revises: i4e5f6g7h8i9
Create Date: 2026-07-30 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'j5f6g7h8i9j0'
down_revision: Union[str, Sequence[str], None] = 'i4e5f6g7h8i9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_ORDER_STATUS_VALUES = (
    "WAITING_FOR_COURIER",
    "ACCEPTED",
    "PICKED_UP",
    "DELIVERING",
    "AWAITING_CONFIRMATION",
    "COMPLETED",
    "DELIVERY_PROBLEM",
    "DELIVERED",
    "CANCELED",
)

OLD_ORDER_STATUS_VALUES = (
    "WAITING_FOR_COURIER",
    "ACCEPTED",
    "PICKED_UP",
    "DELIVERING",
    "DELIVERED",
    "CANCELED",
)


def _build_check_sql(values: tuple[str, ...]) -> str:
    quoted = ", ".join(f"'{value}'" for value in values)
    return f"status IN ({quoted})"


def upgrade() -> None:
    # Drop legacy enum check constraints that may have been auto/generated differently.
    op.execute("ALTER TABLE orders DROP CONSTRAINT IF EXISTS orderstatus")
    op.execute("ALTER TABLE orders DROP CONSTRAINT IF EXISTS ck_orders_status_orderstatus")

    op.alter_column(
        'orders',
        'status',
        existing_type=sa.String(length=19),
        type_=sa.String(length=100),
        existing_nullable=False,
    )

    op.create_check_constraint(
        'orderstatus',
        'orders',
        _build_check_sql(NEW_ORDER_STATUS_VALUES),
    )


def downgrade() -> None:
    op.execute("ALTER TABLE orders DROP CONSTRAINT IF EXISTS orderstatus")
    op.execute("ALTER TABLE orders DROP CONSTRAINT IF EXISTS ck_orders_status_orderstatus")

    op.alter_column(
        'orders',
        'status',
        existing_type=sa.String(length=100),
        type_=sa.String(length=19),
        existing_nullable=False,
    )

    op.create_check_constraint(
        'orderstatus',
        'orders',
        _build_check_sql(OLD_ORDER_STATUS_VALUES),
    )
