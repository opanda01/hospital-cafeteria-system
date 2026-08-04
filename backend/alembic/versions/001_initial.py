"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-08-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("aktif", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "departments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("departman_adi", sa.String(150), nullable=False),
        sa.Column("ust_departman_id", sa.BigInteger(), sa.ForeignKey("departments.id")),
        sa.Column("fatura_edilecek", sa.Boolean(), server_default=sa.text("false")),
    )
    op.create_index("ix_departments_tenant_id", "departments", ["tenant_id"])
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("sicil_no", sa.String(20)),
        sa.Column("ad_soyad", sa.String(150), nullable=False),
        sa.Column("kullanici_tipi", sa.String(20), nullable=False),
        sa.Column("departman_id", sa.BigInteger(), sa.ForeignKey("departments.id")),
        sa.Column("unvan", sa.String(100)),
        sa.Column("aktif", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_sicil_no", "users", ["sicil_no"])
    op.create_table(
        "meal_types",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("meal_adi", sa.String(50), nullable=False),
        sa.Column("baslangic_saat", sa.Time(), nullable=False),
        sa.Column("bitis_saat", sa.Time(), nullable=False),
        sa.Column("birim_fiyat", sa.Numeric(10, 2)),
    )
    op.create_index("ix_meal_types_tenant_id", "meal_types", ["tenant_id"])
    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("device_key", sa.String(64), nullable=False, unique=True),
        sa.Column("konum", sa.String(150), nullable=False),
        sa.Column("ip_adres", sa.String(45)),
        sa.Column("cihaz_tipi", sa.String(20)),
        sa.Column("gateway_id", sa.String(64)),
        sa.Column("api_key_hash", sa.String(255)),
        sa.Column("son_iletisim", sa.DateTime(timezone=True)),
        sa.Column("durum", sa.String(20)),
        sa.Column("cache_version", sa.Integer(), server_default="0"),
    )
    op.create_index("ix_devices_tenant_id", "devices", ["tenant_id"])
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("aktif", sa.Boolean(), server_default=sa.text("true")),
    )
    op.create_index("ix_admin_users_tenant_id", "admin_users", ["tenant_id"])
    op.create_table(
        "cards",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("kart_uid", sa.String(64), nullable=False),
        sa.Column("durum", sa.String(20), nullable=False),
        sa.Column("gecerlilik_baslangic", sa.Date()),
        sa.Column("gecerlilik_bitis", sa.Date()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "kart_uid", name="uq_cards_tenant_uid"),
    )
    op.create_index("ix_cards_tenant_id", "cards", ["tenant_id"])
    op.create_table(
        "meal_entitlements",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("meal_id", sa.Integer(), sa.ForeignKey("meal_types.id"), nullable=False),
        sa.Column("donem", sa.String(7), nullable=False),
        sa.Column("hak_adedi", sa.Integer(), nullable=False),
        sa.Column("kalan_hak", sa.Integer(), nullable=False),
        sa.Column("kaynak", sa.String(30)),
    )
    op.create_index("ix_meal_entitlements_tenant_id", "meal_entitlements", ["tenant_id"])
    op.create_table(
        "processed_events",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "meal_transactions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), unique=True),
        sa.Column("card_id", sa.BigInteger(), sa.ForeignKey("cards.id")),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("meal_id", sa.Integer(), sa.ForeignKey("meal_types.id")),
        sa.Column("okuyucu_id", sa.Integer(), sa.ForeignKey("devices.id")),
        sa.Column("islem_zamani", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("sonuc", sa.String(30), nullable=False),
        sa.Column("offline_senkron", sa.Boolean(), server_default=sa.text("false")),
    )
    op.create_index("ix_meal_tx_dup", "meal_transactions", ["tenant_id", "card_id", "meal_id", "transaction_date"])
    op.create_index("ix_meal_transactions_tenant_id", "meal_transactions", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("meal_transactions")
    op.drop_table("processed_events")
    op.drop_table("meal_entitlements")
    op.drop_table("cards")
    op.drop_table("admin_users")
    op.drop_table("devices")
    op.drop_table("meal_types")
    op.drop_table("users")
    op.drop_table("departments")
    op.drop_table("tenants")
