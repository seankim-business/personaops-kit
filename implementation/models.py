from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


FlowStatus = Literal[
    "new",
    "triage",
    "executing",
    "waiting_approval",
    "ready_to_send",
    "sent",
    "done",
    "blocked",
]

EventType = Literal[
    "inbound",
    "state_change",
    "tool_request",
    "tool_result",
    "approval_requested",
    "approval_decision",
    "outbound_enqueued",
    "outbound_sent",
    "outbound_failed",
]


class CanonicalEvent(BaseModel):
    event_id: str
    project_id: str
    flow_id: str
    task_id: str
    actor_id: str
    persona_id: str
    channel: str
    channel_message_id: str | None = None
    type: EventType
    revision: int = Field(ge=0)
    trace_id: str
    timestamp: datetime
    payload: dict[str, Any] = Field(default_factory=dict)


class FlowDecision(BaseModel):
    decision_id: str
    summary: str
    at: datetime


class FlowSnapshot(BaseModel):
    flow_id: str
    project_id: str
    status: FlowStatus = "new"
    revision: int = 0
    open_tasks: list[str] = Field(default_factory=list)
    latest_decisions: list[FlowDecision] = Field(default_factory=list)
    owners: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TransitionRequest(BaseModel):
    expected_revision: int = Field(ge=0)
    to_status: FlowStatus
    reason: str | None = None
    actor_id: str
    trace_id: str
    approval_granted: bool = False


class PolicyInput(BaseModel):
    category: str
    actor_role: str


class PolicyDecision(BaseModel):
    decision: Literal["allow", "deny", "requires_approval"]
    rule_id: str | None = None
