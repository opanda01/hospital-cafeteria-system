from datetime import date


def meal_lock_key(tenant_id, card_id: int, meal_id: int, tx_date: date) -> str:
    return f"access:{tenant_id}:{card_id}:{meal_id}:{tx_date.isoformat()}"


async def try_acquire_meal_lock(redis, tenant_id, card_id: int, meal_id: int, tx_date: date, ttl: int) -> bool:
    key = meal_lock_key(tenant_id, card_id, meal_id, tx_date)
    return await redis.set(key, "1", nx=True, ex=ttl) is True
