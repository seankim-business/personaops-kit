from __future__ import annotations

from datetime import datetime, timezone

from .models import ApprovalRequest, ApprovalState, CanonicalEvent, FlowDecision, FlowSnapshot, OutboxMessage
from .repository_postgres import (
    PostgresApprovalRepository,
    PostgresConfig,
    PostgresEventRepository,
    PostgresFlowRepository,
    PostgresOutboxRepository,
)
from .store import NotFoundError, RevisionConflict


def _parse_flow(row: dict) -> FlowSnapshot:
    decisions = [FlowDecision(**d) for d in row.get("latest_decisions", [])]
    return FlowSnapshot(
        flow_id=row["flow_id"],
        project_id=row["project_id"],
        status=row["status"],
        revision=row["revision"],
        open_tasks=row.get("open_tasks", []) or [],
        latest_decisions=decisions,
        owners=row.get("owners", []) or [],
        updated_at=row.get("updated_at") or datetime.now(timezone.utc),
    )


def _parse_event(row: dict) -> CanonicalEvent:
    return CanonicalEvent(
        event_id=row["event_id"],
        project_id=row["project_id"],
        flow_id=row["flow_id"],
        task_id=row["task_id"],
        actor_id=row["actor_id"],
        persona_id=row["persona_id"],
        channel=row["channel"],
        channel_message_id=row.get("channel_message_id"),
        type=row["type"],
        revision=row["revision"],
        trace_id=row["trace_id"],
        timestamp=row["timestamp"],
        payload=row.get("payload", {}) or {},
    )


def _parse_approval(row: dict) -> ApprovalState:
    return ApprovalState(
        approval_id=row["approval_id"],
        project_id=row["project_id"],
        flow_id=row["flow_id"],
        task_id=row["task_id"],
        status=row["status"],
        requested_by=row["requested_by"],
        requested_at=row["requested_at"],
        decided_by=row.get("decided_by"),
        decided_at=row.get("decided_at"),
        reason=row.get("reason"),
        note=row.get("note"),
    )


def _parse_outbox(row: dict) -> OutboxMessage:
    return OutboxMessage(
        idempotency_key=row["idempotency_key"],
        channel=row["channel"],
        target=row["target"],
        flow_id=row["flow_id"],
        task_id=row["task_id"],
        intent=row["intent"],
        body=row.get("body", {}) or {},
        status=row["status"],
        retry_count=row.get("retry_count", 0),
        next_attempt_at=row.get("next_attempt_at") or datetime.now(timezone.utc),
        last_error=row.get("last_error"),
    )


class PostgresStore:
    def __init__(self, dsn: str) -> None:
        cfg = PostgresConfig(dsn=dsn)
        self.events = PostgresEventRepository(cfg)
        self.flows = PostgresFlowRepository(cfg)
        self.approvals = PostgresApprovalRepository(cfg)
        self.outbox = PostgresOutboxRepository(cfg)

    def ensure_flow(self, flow_id: str, project_id: str) -> FlowSnapshot:
        row = self.flows.ensure_flow(flow_id, project_id)
        return _parse_flow(row)

    def append_event(self, event: CanonicalEvent) -> None:
        self.events.append_event(event.model_dump())

    def list_events_by_flow(self, flow_id: str, limit: int = 20) -> list[CanonicalEvent]:
        rows = self.events.list_by_flow(flow_id, limit=limit)
        return [_parse_event(r) for r in rows]

    def get_flow(self, flow_id: str) -> FlowSnapshot | None:
        row = self.flows.get_flow(flow_id)
        if not row:
            return None
        return _parse_flow(row)

    def upsert_flow(self, flow: FlowSnapshot, expected_revision: int) -> FlowSnapshot:
        try:
            row = self.flows.upsert_flow_with_revision(flow.model_dump(), expected_revision)
            return _parse_flow(row)
        except RuntimeError as exc:
            raise RevisionConflict(str(exc)) from exc

    def enqueue_outbox(self, msg: OutboxMessage) -> bool:
        return self.outbox.enqueue(msg.model_dump())

    def get_due_outbox(self, limit: int = 50) -> list[OutboxMessage]:
        rows = self.outbox.get_due(limit=limit)
        return [_parse_outbox(r) for r in rows]

    def list_outbox(self) -> list[OutboxMessage]:
        rows = self.outbox.list_all()
        return [_parse_outbox(r) for r in rows]

    def get_outbox(self, key: str) -> OutboxMessage:
        row = self.outbox.get(key)
        if not row:
            raise NotFoundError(f"outbox key not found: {key}")
        return _parse_outbox(row)

    def mark_outbox_sent(self, key: str) -> None:
        self.outbox.mark_sent(key)

    def mark_outbox_retry(self, key: str, error: str, *, max_retries: int = 3) -> None:
        self.outbox.mark_retry(key, error, max_retries=max_retries)

    def request_approval(self, req: ApprovalRequest) -> ApprovalState:
        row = self.approvals.request(req.model_dump())
        return _parse_approval(row)

    def get_approval(self, approval_id: str) -> ApprovalState:
        row = self.approvals.get(approval_id)
        if not row:
            raise NotFoundError(f"approval not found: {approval_id}")
        return _parse_approval(row)

    def list_approvals(self) -> list[ApprovalState]:
        rows = self.approvals.list_all()
        return [_parse_approval(r) for r in rows]

    def decide_approval(self, approval_id: str, *, approved_by: str, approved: bool, note: str | None) -> ApprovalState:
        row = self.approvals.decide(approval_id, approved_by=approved_by, approved=approved, note=note)
        if not row:
            raise NotFoundError(f"approval not found: {approval_id}")
        return _parse_approval(row)
