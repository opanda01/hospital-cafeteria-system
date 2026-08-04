from datetime import datetime, time
from zoneinfo import ZoneInfo

from app.models import MealType
from app.services.access import current_meal


def test_current_meal_ogle():
    meals = [
        MealType(
            id=1,
            tenant_id="00000000-0000-0000-0000-000000000001",
            meal_adi="Öğle",
            baslangic_saat=time(11, 30),
            bitis_saat=time(14, 30),
        )
    ]
    at = datetime(2026, 8, 4, 12, 0, tzinfo=ZoneInfo("Europe/Istanbul"))
    assert current_meal(meals, at) is not None
