import uuid
from datetime import datetime

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AccessValidateRequest(BaseModel):
    card_uid: str
    device_key: str
    event_id: uuid.UUID | None = None
    timestamp: datetime | None = None
    offline_senkron: bool = False


class AccessValidateResponse(BaseModel):
    sonuc: str
    transaction_id: int | None = None
    meal_id: int | None = None


class DeviceOut(BaseModel):
    id: int
    device_key: str
    konum: str
    durum: str
    son_iletisim: datetime | None
    online: bool = False

    model_config = {"from_attributes": True}


class TransactionOut(BaseModel):
    id: int
    card_id: int | None
    user_id: int | None
    meal_id: int | None
    sonuc: str
    islem_zamani: datetime
    offline_senkron: bool

    model_config = {"from_attributes": True}


class DailySummary(BaseModel):
    basarili: int
    red: int


class EdgeSyncCard(BaseModel):
    kart_uid: str
    user_id: int
    aktif: bool = True


class EdgeSyncMeal(BaseModel):
    id: int
    meal_adi: str
    baslangic_saat: str
    bitis_saat: str


class EdgeSyncEntitlement(BaseModel):
    user_id: int
    meal_id: int
    kalan_hak: int


class EdgeSyncResponse(BaseModel):
    cache_version: int
    cards: list[EdgeSyncCard]
    meals: list[EdgeSyncMeal]
    entitlements: list[EdgeSyncEntitlement]


class MqttAccessEvent(BaseModel):
    event_id: uuid.UUID
    tenant_id: uuid.UUID
    device_key: str
    card_uid: str
    ts: datetime
    edge_preliminary: str | None = None


class HeartbeatPayload(BaseModel):
    tenant_id: uuid.UUID
    device_key: str
    ts: datetime
    firmware: str = "0.1.0"
    queue_depth: int = 0
    cache_version: int = 0
