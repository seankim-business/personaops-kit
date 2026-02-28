from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel

from .models import CanonicalEvent


class DiscordInboundPayload(BaseModel):
    message_id: str
    channel_id: str
    sender_id: str
    content: str
    timestamp: datetime | None = None
    project_id: str
    flow_id: str
    task_id: str
    persona_id: str


def to_canonical_event(payload: DiscordInboundPayload, trace_id: str | None = None) -> CanonicalEvent:
    now = payload.timestamp or datetime.now(timezone.utc)
    return CanonicalEvent(
        event_id=f"evt_{uuid4().hex[:12]}",
        project_id=payload.project_id,
        flow_id=payload.flow_id,
        task_id=payload.task_id,
        actor_id=f"actor_discord_{payload.sender_id}",
        persona_id=payload.persona_id,
        channel="discord",
        channel_message_id=payload.message_id,
        type="inbound",
        revision=0,
        trace_id=trace_id or f"trace_{uuid4().hex[:12]}",
        timestamp=now,
        payload={
            "content": payload.content,
            "channel_id": payload.channel_id,
            "sender_id": payload.sender_id,
        },
    )
