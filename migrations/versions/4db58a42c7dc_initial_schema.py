"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2025-08-27 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

# Enum names in DB (postgres)
USER_TYPE_NAME = "user_type_enum"
CARD_TYPE_NAME = "card_type_enum"
STATUS_TYPE_NAME = "status_type_enum"


def upgrade() -> None:
    # --- Enums ---
    user_type_enum = sa.Enum(
        "Admin", "Cashier", "ChiefCashier",
        name=USER_TYPE_NAME
    )
    card_type_enum = sa.Enum(
        "Terminal", "Cash",
        name=CARD_TYPE_NAME
    )
    status_type_enum = sa.Enum(
        "Pending", "Completed", "Canceled",
        name=STATUS_TYPE_NAME
    )

    user_type_enum.create(op.get_bind(), checkfirst=True)
    card_type_enum.create(op.get_bind(), checkfirst=True)
    status_type_enum.create(op.get_bind(), checkfirst=True)

    # --- company ---
    op.create_table(
        "company",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created", sa.DateTime(timezone=False), server_default=sa.text("NOW()")),
        sa.Column("updated", sa.DateTime(timezone=False), server_default=sa.text("NOW()")),
        sa.Column("amount", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("branch_url", sa.String(length=2048), nullable=True),
        sa.Column("account_url", sa.String(length=2048), nullable=True),
        sa.Column("transaction_url", sa.String(length=2048), nullable=True),
        sa.Column("confirm_transaction_url", sa.String(length=2048), nullable=True),
        sa.Column("login", sa.String(length=150), nullable=True),
        sa.Column("password", sa.String(length=150), nullable=True),
        sa.UniqueConstraint("name", name="uq_company_name"),
    )

    # --- branch ---
    op.create_table(
        "branch",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created", sa.DateTime(timezone=False), server_default=sa.text("NOW()")),
        sa.Column("updated", sa.DateTime(timezone=False), server_default=sa.text("NOW()")),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("cashiers_url", sa.String(length=2048), nullable=True),
        sa.Column("chief_cashiers_url", sa.String(length=2048), nullable=True),
        sa.Column("check_pass_url", sa.String(length=2048), nullable=True),
        sa.Column("confirm_user_url", sa.String(length=2048), nullable=True),
        sa.Column("login", sa.String(length=150), nullable=True),
        sa.Column("password", sa.String(length=150), nullable=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["company.id"],
            ondelete="CASCADE",
            name="fk_branch_company_id_company",
        ),
        sa.Index("ix_branch_company_id", "company_id"),
    )

    # --- user ---
    op.create_table(
        "\"user\"",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created", sa.DateTime(timezone=False), server_default=sa.text("NOW()")),
        sa.Column("updated", sa.DateTime(timezone=False), server_default=sa.text("NOW()")),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=True),
        sa.Column("phone", sa.String(length=13), nullable=True),
        sa.Column("login", sa.String(length=150), nullable=True),
        sa.Column("password", sa.String(length=150), nullable=True),
        sa.Column("user_type", sa.Enum(name=USER_TYPE_NAME), nullable=False, server_default="Cashier"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(
            ["branch_id"],
            ["branch.id"],
            ondelete="CASCADE",
            name="fk_user_branch_id_branch",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["company.id"],
            ondelete="CASCADE",
            name="fk_user_company_id_company",
        ),
        sa.UniqueConstraint("telegram_id", name="uq_user_telegram_id"),
        sa.UniqueConstraint("phone", name="uq_user_phone"),
        sa.Index("ix_user_branch_id", "branch_id"),
        sa.Index("ix_user_company_id", "company_id"),
    )

    # --- card_transaction ---
    op.create_table(
        "card_transaction",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created", sa.DateTime(timezone=False), server_default=sa.text("NOW()")),
        sa.Column("updated", sa.DateTime(timezone=False), server_default=sa.text("NOW()")),
        sa.Column("transaction_id", sa.String(length=64), nullable=False),
        sa.Column("image", sa.String(length=255), nullable=True),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("comment", sa.String(length=355), nullable=True),
        sa.Column("card_type", sa.Enum(name=CARD_TYPE_NAME), nullable=False),
        sa.Column("status_type", sa.Enum(name=STATUS_TYPE_NAME), nullable=False, server_default="Pending"),
        sa.Column("sender_terminal_id", sa.BigInteger(), nullable=True),
        sa.Column("receiver_terminal_id", sa.BigInteger(), nullable=True),
        sa.Column("sender_terminal_name", sa.String(length=150), nullable=True),
        sa.Column("receiver_terminal_name", sa.String(length=150), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("is_successful", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["\"user\".id"],
            ondelete="CASCADE",
            name="fk_card_tx_user_id_user",
        ),
        sa.ForeignKeyConstraint(
            ["branch_id"],
            ["branch.id"],
            ondelete="CASCADE",
            name="fk_card_tx_branch_id_branch",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["company.id"],
            ondelete="CASCADE",
            name="fk_card_tx_company_id_company",
        ),
        sa.UniqueConstraint("transaction_id", name="uq_card_tx_transaction_id"),
        sa.Index("ix_card_tx_user_id", "user_id"),
        sa.Index("ix_card_tx_branch_id", "branch_id"),
        sa.Index("ix_card_tx_company_id", "company_id"),
        sa.Index("ix_card_tx_status_type", "status_type"),
        sa.Index("ix_card_tx_timestamp", "timestamp"),
    )

    # --- channel ---
    op.create_table(
        "channel",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created", sa.DateTime(timezone=False), server_default=sa.text("NOW()")),
        sa.Column("updated", sa.DateTime(timezone=False), server_default=sa.text("NOW()")),
        sa.Column("category_id", sa.BigInteger(), nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=False),
        sa.UniqueConstraint("category_id", name="uq_channel_category_id"),
        sa.Index("ix_channel_channel_id", "channel_id"),
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("channel")
    op.drop_table("card_transaction")
    op.drop_table("\"user\"")
    op.drop_table("branch")
    op.drop_table("company")

    # Drop enums
    conn = op.get_bind()
    sa.Enum(name=STATUS_TYPE_NAME).drop(conn, checkfirst=True)
    sa.Enum(name=CARD_TYPE_NAME).drop(conn, checkfirst=True)
    sa.Enum(name=USER_TYPE_NAME).drop(conn, checkfirst=True)