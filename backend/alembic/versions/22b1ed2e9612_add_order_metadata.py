"""add order metadata

Revision ID: 22b1ed2e9612
Revises: d6ada255cf58
Create Date: 2026-07-22

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "22b1ed2e9612"
down_revision: Union[str, Sequence[str], None] = "d6ada255cf58"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column(
            "created_by",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "orders",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.add_column(
        "orders",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_orders_created_by_users",
        "orders",
        "users",
        ["created_by"],
        ["id"],
    )

    op.execute(
        """
        UPDATE orders
        SET created_at = NOW(),
            updated_at = NOW()
        WHERE created_at IS NULL;
        """
    )

    op.alter_column(
        "orders",
        "created_at",
        nullable=False,
    )

    op.alter_column(
        "orders",
        "updated_at",
        nullable=False,
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_orders_created_by_users",
        "orders",
        type_="foreignkey",
    )

    op.drop_column("orders", "updated_at")
    op.drop_column("orders", "created_at")
    op.drop_column("orders", "created_by")