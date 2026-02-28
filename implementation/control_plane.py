from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .context_compiler import ContextCompiler
from .discord_adapter import DiscordInboundPayload, to_canonical_event
from .models import (
    ApprovalDecisionRequest,
    ApprovalRequest,
    CanonicalEvent,
    FlowSnapshot,
    OutboxEnqueueRequest,
    OutboxMessage,
    PolicyDecision,
    PolicyInput,
    TransitionRequest,
)
from .outbox_worker import process_outbox_once
from .policy import PolicyEngine
from .settings import get_settings
from .state_machine import FlowStateMachine, InvalidTransition
from .store import NotFoundError, RevisionConflict
from .store_factory import build_store
from .trace import trace_log

app = FastAPI(title="PersonaOps Control Plane", version="0.3.0")
settings = get_settings()
store = build_store()
policy_engine = PolicyEngine()
state_machine = FlowStateMachine()
context_compiler = ContextCompiler()


class ApprovalCreateInput(BaseModel):
    project_id: str
    flow_id: str
    task_id: str
    requested_by: str
    actor_role: str = Field(default="front")
    category: str
    reason: str
    trace_id: str
    expected_revision: int = Field(ge=0)


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "service": "personaops-control-plane",
        "version": "0.3.0",
        "store_backend": settings.store_backend,
    }


@app.post("/events")
def ingest_event(event: CanonicalEvent) -> dict:
    store.ensure_flow(event.flow_id, event.project_id)
    store.append_event(event)
    trace_log(
        "event_ingested",
        trace_id=event.trace_id,
        event_id=event.event_id,
        flow_id=event.flow_id,
        task_id=event.task_id,
        event_type=event.type,
        revision=event.revision,
    )
    return {"accepted": True, "event_id": event.event_id}


@app.post("/adapters/discord/inbound")
def discord_inbound(payload: DiscordInboundPayload) -> dict:
    event = to_canonical_event(payload)
    return ingest_event(event)


@app.get("/flows/{flow_id}")
def get_flow(flow_id: str) -> FlowSnapshot:
    flow = store.get_flow(flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="flow not found")
    return flow


@app.post("/flows/{flow_id}/transition")
def transition(flow_id: str, req: TransitionRequest) -> FlowSnapshot:
    flow = store.get_flow(flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="flow not found")

    try:
        state_machine.validate(flow.status, req.to_status, approval_granted=req.approval_granted)
    except InvalidTransition as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    flow.status = req.to_status
    try:
        updated = store.upsert_flow(flow, req.expected_revision)
    except RevisionConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    trace_log(
        "flow_transition",
        trace_id=req.trace_id,
        flow_id=flow_id,
        to_status=req.to_status,
        actor_id=req.actor_id,
        revision=updated.revision,
    )
    return updated


@app.post("/policy/evaluate")
def policy_evaluate(data: PolicyInput) -> PolicyDecision:
    decision = policy_engine.evaluate(data)
    trace_log(
        "policy_evaluated",
        category=data.category,
        actor_role=data.actor_role,
        decision=decision.decision,
        rule_id=decision.rule_id,
    )
    return decision


@app.post("/approvals/request")
def request_approval(data: ApprovalCreateInput) -> dict:
    flow = store.get_flow(data.flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="flow not found")

    policy = policy_engine.evaluate(PolicyInput(category=data.category, actor_role=data.actor_role))
    if policy.decision == "deny":
        raise HTTPException(status_code=403, detail="policy denied")

    if policy.decision == "allow":
        return {"required": False, "decision": "allow"}

    approval_id = f"apr_{uuid4().hex[:12]}"
    req = ApprovalRequest(
        approval_id=approval_id,
        project_id=data.project_id,
        flow_id=data.flow_id,
        task_id=data.task_id,
        requested_by=data.requested_by,
        category=data.category,
        reason=data.reason,
        trace_id=data.trace_id,
    )
    state = store.request_approval(req)

    try:
        state_machine.validate(flow.status, "waiting_approval", approval_granted=False)
        flow.status = "waiting_approval"
        flow = store.upsert_flow(flow, data.expected_revision)
    except (InvalidTransition, RevisionConflict) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    event = CanonicalEvent(
        event_id=f"evt_{uuid4().hex[:12]}",
        project_id=data.project_id,
        flow_id=data.flow_id,
        task_id=data.task_id,
        actor_id=data.requested_by,
        persona_id="persona_ops",
        channel="internal",
        type="approval_requested",
        revision=flow.revision,
        trace_id=data.trace_id,
        timestamp=datetime.now(timezone.utc),
        payload={"approval_id": approval_id, "category": data.category, "reason": data.reason},
    )
    store.append_event(event)

    trace_log(
        "approval_requested",
        trace_id=data.trace_id,
        approval_id=approval_id,
        flow_id=data.flow_id,
        task_id=data.task_id,
    )

    return {"required": True, "approval": state, "rule_id": policy.rule_id}


@app.get("/approvals/{approval_id}")
def get_approval(approval_id: str) -> dict:
    try:
        approval = store.get_approval(approval_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"approval": approval}


@app.get("/approvals")
def list_approvals() -> dict:
    items = [x.model_dump() for x in store.list_approvals()]
    return {"count": len(items), "items": items}


@app.post("/approvals/{approval_id}/decision")
def decide_approval(approval_id: str, req: ApprovalDecisionRequest) -> dict:
    try:
        approval = store.decide_approval(
            approval_id,
            approved_by=req.approved_by,
            approved=req.approved,
            note=req.note,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    flow = store.get_flow(approval.flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="flow not found")

    target_status = "ready_to_send" if req.approved else "blocked"
    try:
        state_machine.validate(flow.status, target_status, approval_granted=req.approved)
        expected = flow.revision
        flow.status = target_status
        flow = store.upsert_flow(flow, expected)
    except (InvalidTransition, RevisionConflict) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    event = CanonicalEvent(
        event_id=f"evt_{uuid4().hex[:12]}",
        project_id=approval.project_id,
        flow_id=approval.flow_id,
        task_id=approval.task_id,
        actor_id=req.approved_by,
        persona_id="persona_ops",
        channel="internal",
        type="approval_decision",
        revision=flow.revision,
        trace_id=req.trace_id,
        timestamp=datetime.now(timezone.utc),
        payload={"approval_id": approval_id, "approved": req.approved, "note": req.note},
    )
    store.append_event(event)

    trace_log(
        "approval_decided",
        trace_id=req.trace_id,
        approval_id=approval_id,
        approved=req.approved,
        flow_id=approval.flow_id,
    )
    return {"approval": approval, "flow_status": flow.status}


@app.post("/outbox/enqueue")
def outbox_enqueue(data: OutboxEnqueueRequest) -> dict:
    raw = f"{data.channel}:{data.target}:{data.flow_id}:{data.task_id}:{data.intent}".encode("utf-8")
    key = sha256(raw).hexdigest()
    msg = OutboxMessage(
        idempotency_key=key,
        channel=data.channel,
        target=data.target,
        flow_id=data.flow_id,
        task_id=data.task_id,
        intent=data.intent,
        body=data.body,
    )
    inserted = store.enqueue_outbox(msg)

    if inserted:
        event = CanonicalEvent(
            event_id=f"evt_{uuid4().hex[:12]}",
            project_id=data.body.get("project_id", "proj_unknown"),
            flow_id=data.flow_id,
            task_id=data.task_id,
            actor_id="actor_system",
            persona_id="persona_front",
            channel="internal",
            type="outbound_enqueued",
            revision=0,
            trace_id=data.body.get("trace_id", f"trace_{uuid4().hex[:12]}"),
            timestamp=datetime.now(timezone.utc),
            payload={"idempotency_key": key, "channel": data.channel, "target": data.target},
        )
        store.append_event(event)

    return {"enqueued": inserted, "idempotency_key": key}


@app.post("/outbox/process_once")
def outbox_process_once() -> dict:
    def sender(msg: OutboxMessage) -> None:
        # placeholder sender; integrate real channel senders in v0.4
        if msg.body.get("force_fail"):
            raise RuntimeError("forced send failure for testing")

    return process_outbox_once(store, sender, max_retries=settings.outbox_max_retries)


@app.get("/outbox")
def outbox_list() -> dict:
    items = [msg.model_dump() for msg in store.list_outbox()]
    return {"count": len(items), "items": items}


@app.get("/context/{flow_id}")
def get_context(flow_id: str) -> dict:
    flow = store.get_flow(flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="flow not found")

    events = store.list_events_by_flow(flow_id, limit=20)
    related = [f"{e.type}:{e.task_id}" for e in events]
    profile = {"name": "Persona", "tone": "professional-friendly"}
    return context_compiler.compile(flow, related, profile)
