import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db, get_redis
from app.deps import require_roles
from app.models import AdminUser, Device, MealTransaction
from app.schemas import (
    AccessValidateRequest,
    AccessValidateResponse,
    DailySummary,
    TransactionOut,
)
from app.services.access import validate_access

router = APIRouter(tags=["access"])


@router.post("/access/validate", response_model=AccessValidateResponse)
async def access_validate(
    body: AccessValidateRequest,
    db: AsyncSession = Depends(get_db),
    x_device_api_key: str | None = Header(default=None, alias="X-Device-Api-Key"),
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
):
    result = await db.execute(select(Device).where(Device.device_key == body.device_key))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Cihaz bulunamadı")

    if x_internal_key != settings.api_internal_key:
        from passlib.context import CryptContext

        pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
        if not x_device_api_key or not device.api_key_hash or not pwd.verify(x_device_api_key, device.api_key_hash):
            raise HTTPException(status_code=401, detail="Cihaz kimlik doğrulaması başarısız")

    redis = await get_redis()
    event_id = body.event_id or uuid.uuid4()
    sonuc, tx = await validate_access(
        db,
        redis,
        tenant_id=device.tenant_id,
        card_uid=body.card_uid,
        device=device,
        event_id=event_id,
        at=body.timestamp,
        offline_senkron=body.offline_senkron,
    )
    await db.commit()
    return AccessValidateResponse(
        sonuc=sonuc.value,
        transaction_id=tx.id if tx else None,
        meal_id=tx.meal_id if tx else None,
    )


@router.get("/reports/transactions/recent", response_model=list[TransactionOut])
async def recent_transactions(
    limit: int = 50,
    admin: AdminUser = Depends(require_roles("tenant_admin", "yemekhane", "read_only")),
    db: AsyncSession = Depends(get_db),
):
    if not admin.tenant_id:
        raise HTTPException(status_code=400, detail="Tenant atanmamış")
    result = await db.execute(
        select(MealTransaction)
        .where(MealTransaction.tenant_id == admin.tenant_id)
        .order_by(MealTransaction.islem_zamani.desc())
        .limit(min(limit, 200))
    )
    return list(result.scalars().all())


@router.get("/reports/summary/today", response_model=DailySummary)
async def today_summary(
    admin: AdminUser = Depends(require_roles("tenant_admin", "yemekhane", "read_only")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import func

    from app.models import TransactionResult
    from app.services.access import now_tr

    if not admin.tenant_id:
        raise HTTPException(status_code=400, detail="Tenant atanmamış")
    today = now_tr().date()
    basarili = await db.scalar(
        select(func.count())
        .select_from(MealTransaction)
        .where(
            MealTransaction.tenant_id == admin.tenant_id,
            MealTransaction.transaction_date == today,
            MealTransaction.sonuc == TransactionResult.BASARILI.value,
        )
    )
    red = await db.scalar(
        select(func.count())
        .select_from(MealTransaction)
        .where(
            MealTransaction.tenant_id == admin.tenant_id,
            MealTransaction.transaction_date == today,
            MealTransaction.sonuc != TransactionResult.BASARILI.value,
        )
    )
    return DailySummary(basarili=basarili or 0, red=red or 0)
