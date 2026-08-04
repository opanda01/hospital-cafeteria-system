import asyncio
import json
import logging
from datetime import UTC

import aiomqtt
from pydantic import ValidationError
from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal, get_redis
from app.models import Device
from app.schemas import HeartbeatPayload, MqttAccessEvent
from app.services.access import mark_event_processed, validate_access

logger = logging.getLogger(__name__)


async def mqtt_consumer_loop(stop_event: asyncio.Event) -> None:
    broker = settings.mqtt_broker
    port = settings.mqtt_port
    while not stop_event.is_set():
        try:
            async with aiomqtt.Client(hostname=broker, port=port) as client:
                await client.subscribe("yemekhane/+/devices/+/events")
                await client.subscribe("yemekhane/+/devices/+/heartbeat")
                logger.info("MQTT connected to %s:%s", broker, port)
                async for message in client.messages:
                    if stop_event.is_set():
                        break
                    topic = str(message.topic)
                    try:
                        payload = json.loads(message.payload.decode())
                    except json.JSONDecodeError:
                        continue
                    if topic.endswith("/heartbeat"):
                        await _handle_heartbeat(payload)
                    elif topic.endswith("/events"):
                        await _handle_event(payload)
        except asyncio.CancelledError:
            break
        except (aiomqtt.MqttError, OSError, ConnectionError):
            logger.exception("MQTT connection error, retry in 5s")
            await asyncio.sleep(5)


async def _handle_heartbeat(raw: dict) -> None:
    try:
        body = HeartbeatPayload.model_validate(raw)
    except ValidationError:
        return

    async with SessionLocal() as db:
        result = await db.execute(
            select(Device).where(
                Device.tenant_id == body.tenant_id,
                Device.device_key == body.device_key,
            )
        )
        device = result.scalar_one_or_none()
        if not device:
            return
        ts = body.ts
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        device.son_iletisim = ts.astimezone(UTC)
        device.cache_version = body.cache_version
        await db.commit()


async def _handle_event(raw: dict) -> None:
    try:
        evt = MqttAccessEvent.model_validate(raw)
    except ValidationError:
        return
    redis = await get_redis()
    async with SessionLocal() as db:
        if not await mark_event_processed(db, evt.event_id):
            await db.rollback()
            return
        result = await db.execute(select(Device).where(Device.device_key == evt.device_key))
        device = result.scalar_one_or_none()
        if not device:
            await db.rollback()
            return
        await validate_access(
            db,
            redis,
            tenant_id=evt.tenant_id,
            card_uid=evt.card_uid,
            device=device,
            event_id=evt.event_id,
            at=evt.ts,
            offline_senkron=True,
        )
        await db.commit()
