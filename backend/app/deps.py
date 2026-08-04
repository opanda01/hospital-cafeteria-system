from datetime import UTC, datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_utils import decode_token
from app.database import get_db
from app.models import AdminUser

security = HTTPBearer(auto_error=False)


async def get_current_admin(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    if not creds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kimlik doğrulama gerekli")
    try:
        payload = decode_token(creds.credentials)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz token") from exc
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz token")
    result = await db.execute(select(AdminUser).where(AdminUser.email == email, AdminUser.aktif.is_(True)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kullanıcı bulunamadı")
    return user


def require_roles(*roles: str):
    async def checker(admin: AdminUser = Depends(get_current_admin)) -> AdminUser:
        if admin.role not in roles and admin.role != "super_admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Yetkisiz")
        return admin

    return checker


async def verify_device_api_key(
    device_key: str,
    api_key: str,
    db: AsyncSession,
):
    from passlib.context import CryptContext

    from app.models import Device

    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    result = await db.execute(select(Device).where(Device.device_key == device_key))
    device = result.scalar_one_or_none()
    if not device or not device.api_key_hash:
        raise HTTPException(status_code=401, detail="Cihaz doğrulanamadı")
    if not pwd.verify(api_key, device.api_key_hash):
        raise HTTPException(status_code=401, detail="Cihaz doğrulanamadı")
    return device


def device_online(last_seen: datetime | None, threshold_sec: int = 120) -> bool:
    if not last_seen:
        return False
    now = datetime.now(UTC)
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=UTC)
    return (now - last_seen).total_seconds() <= threshold_sec
