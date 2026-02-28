from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256

from fastapi import FastAPI, HTTPException

from .context_compiler import ContextCompiler
from .models import CanonicalEvent, FlowSnapshot, PolicyDecision, PolicyInput, TransitionRequest
from .policy import PolicyEngine
from .state_machine import FlowStateMachine, InvalidTransition
from .store import InMemoryStore, RevisionConflict

app = FastAPI(title="PersonaOps Control Plane", version="0.1.0")
store = InMemoryStore()
policy_engine = PolicyEngine()
state_machine = FlowStateMachine()
context_compiler = ContextCompiler()


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "personaops-control-plane"}


@app.post("/events")
def ingest_event(event: CanonicalEvent) -> dict:
    # ensure flow exists
    flow = store.get_flow(event.flow_id)
    if flow is None:
        flow = FlowSnapshot(flow_id=event.flow_id, project_id=event.project_id)
        store.flows[event.flow_id] = flow

    store.append_event(event)
    return {"accepted": True, "event_id": event.event_id}


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
        return store.upsert_flow(flow, req.expected_revision)
    except RevisionConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/policy/evaluate")
def policy_evaluate(data: PolicyInput) -> PolicyDecision:
    return policy_engine.evaluate(data)


@app.post("/outbox/enqueue")
def outbox_enqueue(channel: str, target: str, flow_id: str, task_id: str, intent: str) -> dict:
    raw = f"{channel}:{target}:{flow_id}:{task_id}:{intent}".encode("utf-8")
    key = sha256(raw).hexdigest()
    inserted = store.enqueue_outbox(key)
    return {"enqueued": inserted, "idempotency_key": key}


@app.get("/context/{flow_id}")
def get_context(flow_id: str) -> dict:
    flow = store.get_flow(flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="flow not found")

    related = [
        f"{e.type}:{e.task_id}"
        for e in store.events
        if e.flow_id == flow_id and e.timestamp > datetime.now(timezone.utc).replace(year=2000)
    ]
    profile = {"name": "Persona", "tone": "professional-friendly"}
    return context_compiler.compile(flow, related, profile)
