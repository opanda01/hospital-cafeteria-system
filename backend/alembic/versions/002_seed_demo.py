"""seed demo tenant

Revision ID: 002
Revises: 001
"""

import uuid
from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from passlib.context import CryptContext

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
DEVICE_KEY_HASH = pwd.hash("dev_device_key_change_me")
ADMIN_HASH = pwd.hash("admin123")


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO tenants (id, name, slug, aktif) VALUES
            (:id, 'Demo Hastane', 'demo-hastane', true)
            ON CONFLICT DO NOTHING
            """
        ),
        {"id": str(TENANT_ID)},
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO departments (tenant_id, departman_adi) VALUES
            (:tid, 'Genel Cerrahi')
            """
        ),
        {"tid": str(TENANT_ID)},
    )
    dept_id = conn.execute(sa.text("SELECT id FROM departments WHERE tenant_id = :tid LIMIT 1"), {"tid": str(TENANT_ID)}).scalar()
    conn.execute(
        sa.text(
            """
            INSERT INTO users (tenant_id, sicil_no, ad_soyad, kullanici_tipi, departman_id, unvan, aktif) VALUES
            (:tid, '1001', 'Ayşe Yılmaz', 'PERSONEL', :dept, 'Hemşire', true),
            (:tid, '1002', 'Mehmet Demir', 'PERSONEL', :dept, 'Doktor', true)
            """
        ),
        {"tid": str(TENANT_ID), "dept": dept_id},
    )
    u1 = conn.execute(sa.text("SELECT id FROM users WHERE sicil_no = '1001'")).scalar()
    u2 = conn.execute(sa.text("SELECT id FROM users WHERE sicil_no = '1002'")).scalar()
    conn.execute(
        sa.text(
            """
            INSERT INTO meal_types (tenant_id, meal_adi, baslangic_saat, bitis_saat) VALUES
            (:tid, 'Kahvaltı', '07:00', '10:00'),
            (:tid, 'Öğle', '11:30', '14:30'),
            (:tid, 'Akşam', '17:00', '20:00')
            """
        ),
        {"tid": str(TENANT_ID)},
    )
    meal_ogle = conn.execute(
        sa.text("SELECT id FROM meal_types WHERE tenant_id = :tid AND meal_adi = 'Öğle'"),
        {"tid": str(TENANT_ID)},
    ).scalar()
    period = datetime.now().strftime("%Y-%m")
    conn.execute(
        sa.text(
            """
            INSERT INTO meal_entitlements (tenant_id, user_id, meal_id, donem, hak_adedi, kalan_hak, kaynak) VALUES
            (:tid, :u1, :meal, :period, 30, 30, 'HASTANE_KARSILAMA'),
            (:tid, :u2, :meal, :period, 30, 30, 'HASTANE_KARSILAMA')
            """
        ),
        {"tid": str(TENANT_ID), "u1": u1, "u2": u2, "meal": meal_ogle, "period": period},
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO cards (tenant_id, user_id, kart_uid, durum) VALUES
            (:tid, :u1, 'A1B2C3D4', 'AKTIF'),
            (:tid, :u2, 'E5F6G7H8', 'AKTIF')
            """
        ),
        {"tid": str(TENANT_ID), "u1": u1, "u2": u2},
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO devices (tenant_id, device_key, konum, cihaz_tipi, api_key_hash, durum, cache_version) VALUES
            (:tid, 'reader-giris-1', 'Ana Yemekhane Giriş-1', 'TURNIKE', :key, 'AKTIF', 0),
            (:tid, 'reader-giris-2', 'Ana Yemekhane Giriş-2', 'TURNIKE', :key, 'AKTIF', 0)
            """
        ),
        {"tid": str(TENANT_ID), "key": DEVICE_KEY_HASH},
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO admin_users (tenant_id, email, password_hash, role, aktif) VALUES
            (:tid, 'admin@demo.local', :ph, 'tenant_admin', true)
            """
        ),
        {"tid": str(TENANT_ID), "ph": ADMIN_HASH},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM meal_transactions WHERE tenant_id = :tid"), {"tid": str(TENANT_ID)})
    conn.execute(sa.text("DELETE FROM processed_events"))
    conn.execute(sa.text("DELETE FROM meal_entitlements WHERE tenant_id = :tid"), {"tid": str(TENANT_ID)})
    conn.execute(sa.text("DELETE FROM cards WHERE tenant_id = :tid"), {"tid": str(TENANT_ID)})
    conn.execute(sa.text("DELETE FROM admin_users WHERE tenant_id = :tid"), {"tid": str(TENANT_ID)})
    conn.execute(sa.text("DELETE FROM devices WHERE tenant_id = :tid"), {"tid": str(TENANT_ID)})
    conn.execute(sa.text("DELETE FROM meal_types WHERE tenant_id = :tid"), {"tid": str(TENANT_ID)})
    conn.execute(sa.text("DELETE FROM users WHERE tenant_id = :tid"), {"tid": str(TENANT_ID)})
    conn.execute(sa.text("DELETE FROM departments WHERE tenant_id = :tid"), {"tid": str(TENANT_ID)})
    conn.execute(sa.text("DELETE FROM tenants WHERE id = :tid"), {"tid": str(TENANT_ID)})
