# ADR 001: MQTT Topic Şeması

- Events: `yemekhane/{tenant_id}/devices/{device_id}/events`
- Heartbeat: `yemekhane/{tenant_id}/devices/{device_id}/heartbeat`
- Payload: JSON with `event_id`, `card_uid`, `ts`, `result` (edge preliminary)
