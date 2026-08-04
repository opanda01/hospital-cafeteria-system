from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import device_online, require_roles
from app.models import AdminUser, Device
from app.schemas import DeviceOut, HeartbeatPayload

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceOut])
async def list_devices(
    admin: AdminUser = Depends(require_roles("tenant_admin", "yemekhane", "read_only")),
    db: AsyncSession = Depends(get_db),
):
    if not admin.tenant_id:
        raise HTTPException(status_code=400, detail="Tenant atanmamış")
    result = await db.execute(select(Device).where(Device.tenant_id == admin.tenant_id))
    devices = result.scalars().all()
    out: list[DeviceOut] = []
    for d in devices:
        item = DeviceOut.model_validate(d)
        item.online = device_online(d.son_iletisim)
        out.append(item)
    return out


@router.post("/heartbeat")
async def device_heartbeat(body: HeartbeatPayload, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Device).where(
            Device.tenant_id == body.tenant_id,
            Device.device_key == body.device_key,
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Cihaz bulunamadı")
    device.son_iletisim = body.ts.astimezone(timezone.utc) if body.ts.tzinfo else body.ts.replace(tzinfo=timezone.utc)
    device.cache_version = body.cache_version
    await db.commit()
    return {"ok": True}
