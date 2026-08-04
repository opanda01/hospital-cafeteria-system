from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Card, CardStatus, Device, MealEntitlement, MealType, User
from app.schemas import EdgeSyncResponse, EdgeSyncCard, EdgeSyncMeal, EdgeSyncEntitlement

router = APIRouter(prefix="/internal/edge/v1", tags=["edge-internal"])


@router.get("/sync", response_model=EdgeSyncResponse)
async def edge_sync(
    device_key: str,
    db: AsyncSession = Depends(get_db),
    x_device_api_key: str | None = Header(default=None, alias="X-Device-Api-Key"),
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
):
    result = await db.execute(select(Device).where(Device.device_key == device_key))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Cihaz bulunamadı")

    if x_internal_key != settings.api_internal_key:
        from passlib.context import CryptContext

        pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
        if not x_device_api_key or not device.api_key_hash or not pwd.verify(x_device_api_key, device.api_key_hash):
            raise HTTPException(status_code=401, detail="Cihaz kimlik doğrulaması başarısız")

    tenant_id = device.tenant_id
    cards_result = await db.execute(
        select(Card, User)
        .join(User, Card.user_id == User.id)
        .where(
            Card.tenant_id == tenant_id,
            Card.durum == CardStatus.AKTIF.value,
            User.aktif.is_(True),
        )
    )
    cards: list[EdgeSyncCard] = []
    for card, user in cards_result.all():
        cards.append(EdgeSyncCard(kart_uid=card.kart_uid, user_id=user.id, aktif=True))

    meals_result = await db.execute(select(MealType).where(MealType.tenant_id == tenant_id))
    meals = [
        EdgeSyncMeal(
            id=m.id,
            meal_adi=m.meal_adi,
            baslangic_saat=m.baslangic_saat.isoformat(),
            bitis_saat=m.bitis_saat.isoformat(),
        )
        for m in meals_result.scalars().all()
    ]

    from app.services.access import now_tr

    period = now_tr().strftime("%Y-%m")
    ent_result = await db.execute(
        select(MealEntitlement).where(
            MealEntitlement.tenant_id == tenant_id,
            MealEntitlement.donem == period,
            MealEntitlement.kalan_hak > 0,
        )
    )
    entitlements = [
        EdgeSyncEntitlement(user_id=e.user_id, meal_id=e.meal_id, kalan_hak=e.kalan_hak)
        for e in ent_result.scalars().all()
    ]

    device.cache_version += 1
    await db.commit()

    return EdgeSyncResponse(
        cache_version=device.cache_version,
        cards=cards,
        meals=meals,
        entitlements=entitlements,
    )
