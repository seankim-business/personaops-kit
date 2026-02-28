from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import ApprovalRequest, ApprovalState, CanonicalEvent, FlowSnapshot, OutboxMessage


class RevisionConflict(Exception):
    pass


class NotFoundError(Exception):
    pass


class InMemoryStore:
    def __init__(self) -> None:
        self.events: list[CanonicalEvent] = []
        self.flows: dict[str, FlowSnapshot] = {}
        self.idempotency_keys: set[str] = set()
        self.approvals: dict[str, ApprovalState] = {}
        self.outbox: dict[str, OutboxMessage] = {}

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

    def enqueue_outbox(self, msg: OutboxMessage) -> bool:
        """Returns False when duplicate idempotency key is detected."""
        key = msg.idempotency_key
        if key in self.idempotency_keys:
            return False
        self.idempotency_keys.add(key)
        self.outbox[key] = msg
        return True

    def get_due_outbox(self, limit: int = 50) -> list[OutboxMessage]:
        now = datetime.now(timezone.utc)
        due = [
            msg
            for msg in self.outbox.values()
            if msg.status in {"pending", "failed"} and msg.next_attempt_at <= now
        ]
        due.sort(key=lambda x: x.next_attempt_at)
        return due[:limit]

    def mark_outbox_sent(self, key: str) -> None:
        msg = self.outbox.get(key)
        if not msg:
            raise NotFoundError(f"outbox key not found: {key}")
        msg.status = "sent"
        msg.last_error = None

    def mark_outbox_retry(self, key: str, error: str, *, max_retries: int = 3) -> None:
        msg = self.outbox.get(key)
        if not msg:
            raise NotFoundError(f"outbox key not found: {key}")

        msg.retry_count += 1
        msg.last_error = error
        if msg.retry_count > max_retries:
            msg.status = "dead_letter"
            return

        msg.status = "failed"
        # simple linear backoff: 10s * retry_count
        msg.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=10 * msg.retry_count)

    def request_approval(self, req: ApprovalRequest) -> ApprovalState:
        state = ApprovalState(
            approval_id=req.approval_id,
            project_id=req.project_id,
            flow_id=req.flow_id,
            task_id=req.task_id,
            status="pending",
            requested_by=req.requested_by,
            requested_at=req.requested_at,
            reason=req.reason,
        )
        self.approvals[req.approval_id] = state
        return state

    def get_approval(self, approval_id: str) -> ApprovalState:
        state = self.approvals.get(approval_id)
        if not state:
            raise NotFoundError(f"approval not found: {approval_id}")
        return state

    def decide_approval(self, approval_id: str, *, approved_by: str, approved: bool, note: str | None) -> ApprovalState:
        state = self.get_approval(approval_id)
        state.status = "approved" if approved else "rejected"
        state.decided_by = approved_by
        state.decided_at = datetime.now(timezone.utc)
        state.note = note
        return state
