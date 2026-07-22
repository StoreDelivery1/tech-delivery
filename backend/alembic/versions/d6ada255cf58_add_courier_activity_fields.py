"""add courier activity fields

Revision ID: d6ada255cf58
Revises: fa85ef9ac7a6
Create Date: 2026-07-22 22:16:13.556311

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d6ada255cf58"
down_revision: Union[str, Sequence[str], None] = "fa85ef9ac7a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "users",
        sa.Column(
            "is_online",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "last_seen",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.alter_column(
        "users",
        "is_online",
        server_default=None,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "users",
        "last_seen",
    )

    op.drop_column(
        "users",
        "is_online",
    )