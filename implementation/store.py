from __future__ import annotations

from datetime import datetime, timezone

from .models import CanonicalEvent, FlowSnapshot


class RevisionConflict(Exception):
    pass


class InMemoryStore:
    def __init__(self) -> None:
        self.events: list[CanonicalEvent] = []
        self.flows: dict[str, FlowSnapshot] = {}
        self.idempotency_keys: set[str] = set()

    def append_event(self, event: CanonicalEvent) -> None:
        self.events.append(event)

    def get_flow(self, flow_id: str) -> FlowSnapshot | None:
        return self.flows.get(flow_id)

    def upsert_flow(self, flow: FlowSnapshot, expected_revision: int) -> FlowSnapshot:
        current = self.flows.get(flow.flow_id)
        if current and current.revision != expected_revision:
            raise RevisionConflict(
                f"revision conflict: expected={expected_revision}, actual={current.revision}"
            )

        flow.revision = expected_revision + 1
        flow.updated_at = datetime.now(timezone.utc)
        self.flows[flow.flow_id] = flow
        return flow

    def enqueue_outbox(self, key: str) -> bool:
        """Returns False when duplicate key is detected."""
        if key in self.idempotency_keys:
            return False
        self.idempotency_keys.add(key)
        return True
