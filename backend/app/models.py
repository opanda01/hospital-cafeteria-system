import enum
import uuid
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserType(str, enum.Enum):
    PERSONEL = "PERSONEL"
    TASERON = "TASERON"
    STAJYER = "STAJYER"
    REFAKATCI = "REFAKATCI"
    MISAFIR = "MISAFIR"


class CardStatus(str, enum.Enum):
    AKTIF = "AKTIF"
    KAYIP = "KAYIP"
    IPTAL = "IPTAL"
    SURELI = "SURELI"


class TransactionResult(str, enum.Enum):
    BASARILI = "BASARILI"
    RED_HAK_YOK = "RED_HAK_YOK"
    RED_KART_GECERSIZ = "RED_KART_GECERSIZ"
    RED_MUKERRER = "RED_MUKERRER"


class DeviceStatus(str, enum.Enum):
    AKTIF = "AKTIF"
    ARIZALI = "ARIZALI"
    BAKIMDA = "BAKIMDA"


class DeviceType(str, enum.Enum):
    TURNIKE = "TURNIKE"
    KIOSK = "KIOSK"
    EL_TERMINALI = "EL_TERMINALI"


class AdminRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    YEMEKHANE = "yemekhane"
    READ_ONLY = "read_only"


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    departman_adi: Mapped[str] = mapped_column(String(150), nullable=False)
    ust_departman_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("departments.id"))
    fatura_edilecek: Mapped[bool] = mapped_column(Boolean, default=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    sicil_no: Mapped[str | None] = mapped_column(String(20), index=True)
    ad_soyad: Mapped[str] = mapped_column(String(150), nullable=False)
    kullanici_tipi: Mapped[str] = mapped_column(String(20), nullable=False, default=UserType.PERSONEL.value)
    departman_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    unvan: Mapped[str | None] = mapped_column(String(100))
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cards: Mapped[list["Card"]] = relationship(back_populates="user")


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    kart_uid: Mapped[str] = mapped_column(String(64), nullable=False)
    durum: Mapped[str] = mapped_column(String(20), nullable=False, default=CardStatus.AKTIF.value)
    gecerlilik_baslangic: Mapped[date | None] = mapped_column(Date)
    gecerlilik_bitis: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User | None] = relationship(back_populates="cards")

    __table_args__ = (UniqueConstraint("tenant_id", "kart_uid", name="uq_cards_tenant_uid"),)


class MealType(Base):
    __tablename__ = "meal_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    meal_adi: Mapped[str] = mapped_column(String(50), nullable=False)
    baslangic_saat: Mapped[time] = mapped_column(Time, nullable=False)
    bitis_saat: Mapped[time] = mapped_column(Time, nullable=False)
    birim_fiyat: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))


class MealEntitlement(Base):
    __tablename__ = "meal_entitlements"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    meal_id: Mapped[int] = mapped_column(ForeignKey("meal_types.id"), nullable=False)
    donem: Mapped[str] = mapped_column(String(7), nullable=False)
    hak_adedi: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    kalan_hak: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    kaynak: Mapped[str] = mapped_column(String(30), default="HASTANE_KARSILAMA")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    device_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    konum: Mapped[str] = mapped_column(String(150), nullable=False)
    ip_adres: Mapped[str | None] = mapped_column(String(45))
    cihaz_tipi: Mapped[str] = mapped_column(String(20), default=DeviceType.TURNIKE.value)
    gateway_id: Mapped[str | None] = mapped_column(String(64))
    api_key_hash: Mapped[str | None] = mapped_column(String(255))
    son_iletisim: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    durum: Mapped[str] = mapped_column(String(20), default=DeviceStatus.AKTIF.value)
    cache_version: Mapped[int] = mapped_column(Integer, default=0)


class MealTransaction(Base):
    __tablename__ = "meal_transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    event_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), unique=True)
    card_id: Mapped[int | None] = mapped_column(ForeignKey("cards.id"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    meal_id: Mapped[int | None] = mapped_column(ForeignKey("meal_types.id"))
    okuyucu_id: Mapped[int | None] = mapped_column(ForeignKey("devices.id"))
    islem_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    sonuc: Mapped[str] = mapped_column(String(30), nullable=False)
    offline_senkron: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        Index("ix_meal_tx_dup", "tenant_id", "card_id", "meal_id", "transaction_date"),
    )


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tenants.id"), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default=AdminRole.TENANT_ADMIN.value)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)


class ProcessedEvent(Base):
    """Idempotent MQTT / edge event processing."""

    __tablename__ = "processed_events"

    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
