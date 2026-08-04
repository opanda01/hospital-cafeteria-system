from datetime import date, datetime, timedelta, time, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Card,
    CardStatus,
    Device,
    MealEntitlement,
    MealTransaction,
    MealType,
    ProcessedEvent,
    TransactionResult,
    User,
)
from app.services.redis_lock import try_acquire_meal_lock

TR_TZ = ZoneInfo("Europe/Istanbul")


def now_tr() -> datetime:
    return datetime.now(TR_TZ)


def current_meal(meals: list[MealType], at: datetime | None = None) -> MealType | None:
    at = at or now_tr()
    t = at.timetz().replace(tzinfo=None)
    for meal in meals:
        start = meal.baslangic_saat
        end = meal.bitis_saat
        if start <= end:
            if start <= t <= end:
                return meal
        else:
            if t >= start or t <= end:
                return meal
    return None


async def load_meals(session: AsyncSession, tenant_id) -> list[MealType]:
    result = await session.execute(select(MealType).where(MealType.tenant_id == tenant_id))
    return list(result.scalars().all())


async def validate_access(
    session: AsyncSession,
    redis,
    *,
    tenant_id,
    card_uid: str,
    device: Device,
    event_id=None,
    at: datetime | None = None,
    offline_senkron: bool = False,
) -> tuple[TransactionResult, MealTransaction | None]:
    at = at or now_tr()
    tx_date = at.date()

    result = await session.execute(
        select(Card).where(Card.tenant_id == tenant_id, Card.kart_uid == card_uid)
    )
    card = result.scalar_one_or_none()
    if not card or card.durum != CardStatus.AKTIF.value:
        tx = await _persist(
            session,
            tenant_id=tenant_id,
            card=card,
            user_id=None,
            meal_id=None,
            device=device,
            tx_date=tx_date,
            at=at,
            sonuc=TransactionResult.RED_KART_GECERSIZ.value,
            event_id=event_id,
            offline_senkron=offline_senkron,
        )
        return TransactionResult.RED_KART_GECERSIZ, tx

    user: User | None = None
    if card.user_id:
        user = await session.get(User, card.user_id)
    if not user or not user.aktif:
        tx = await _persist(
            session,
            tenant_id=tenant_id,
            card=card,
            user_id=card.user_id,
            meal_id=None,
            device=device,
            tx_date=tx_date,
            at=at,
            sonuc=TransactionResult.RED_KART_GECERSIZ.value,
            event_id=event_id,
            offline_senkron=offline_senkron,
        )
        return TransactionResult.RED_KART_GECERSIZ, tx

    meals = await load_meals(session, tenant_id)
    meal = current_meal(meals, at)
    if not meal:
        tx = await _persist(
            session,
            tenant_id=tenant_id,
            card=card,
            user_id=user.id,
            meal_id=None,
            device=device,
            tx_date=tx_date,
            at=at,
            sonuc=TransactionResult.RED_HAK_YOK.value,
            event_id=event_id,
            offline_senkron=offline_senkron,
        )
        return TransactionResult.RED_HAK_YOK, tx

    period = at.strftime("%Y-%m")
    ent_result = await session.execute(
        select(MealEntitlement).where(
            MealEntitlement.tenant_id == tenant_id,
            MealEntitlement.user_id == user.id,
            MealEntitlement.meal_id == meal.id,
            MealEntitlement.donem == period,
        )
    )
    ent = ent_result.scalar_one_or_none()
    if not ent or ent.kalan_hak <= 0:
        tx = await _persist(
            session,
            tenant_id=tenant_id,
            card=card,
            user_id=user.id,
            meal_id=meal.id,
            device=device,
            tx_date=tx_date,
            at=at,
            sonuc=TransactionResult.RED_HAK_YOK.value,
            event_id=event_id,
            offline_senkron=offline_senkron,
        )
        return TransactionResult.RED_HAK_YOK, tx

    ttl = _seconds_until_meal_end(at, meal.bitis_saat)
    acquired = await try_acquire_meal_lock(redis, tenant_id, card.id, meal.id, tx_date, ttl)
    if not acquired:
        tx = await _persist(
            session,
            tenant_id=tenant_id,
            card=card,
            user_id=user.id,
            meal_id=meal.id,
            device=device,
            tx_date=tx_date,
            at=at,
            sonuc=TransactionResult.RED_MUKERRER.value,
            event_id=event_id,
            offline_senkron=offline_senkron,
        )
        return TransactionResult.RED_MUKERRER, tx

    ent.kalan_hak -= 1
    tx = await _persist(
        session,
        tenant_id=tenant_id,
        card=card,
        user_id=user.id,
        meal_id=meal.id,
        device=device,
        tx_date=tx_date,
        at=at,
        sonuc=TransactionResult.BASARILI.value,
        event_id=event_id,
        offline_senkron=offline_senkron,
    )
    return TransactionResult.BASARILI, tx


def _seconds_until_meal_end(at: datetime, meal_end: time) -> int:
    end_dt = datetime.combine(at.date(), meal_end, tzinfo=at.tzinfo)
    if end_dt <= at:
        end_dt = end_dt + timedelta(days=1)
    return max(int((end_dt - at).total_seconds()), 60)


async def _persist(
    session: AsyncSession,
    *,
    tenant_id,
    card: Card | None,
    user_id,
    meal_id,
    device: Device,
    tx_date: date,
    at: datetime,
    sonuc: str,
    event_id,
    offline_senkron: bool,
) -> MealTransaction:
    tx = MealTransaction(
        tenant_id=tenant_id,
        event_id=event_id,
        card_id=card.id if card else None,
        user_id=user_id,
        meal_id=meal_id,
        okuyucu_id=device.id,
        islem_zamani=at.astimezone(timezone.utc),
        transaction_date=tx_date,
        sonuc=sonuc,
        offline_senkron=offline_senkron,
    )
    session.add(tx)
    await session.flush()
    return tx


async def mark_event_processed(session: AsyncSession, event_id) -> bool:
    existing = await session.get(ProcessedEvent, event_id)
    if existing:
        return False
    session.add(ProcessedEvent(event_id=event_id))
    return True
