from datetime import datetime, timezone

import pytest

from implementation.models import CanonicalEvent, FlowSnapshot
from implementation.state_machine import FlowStateMachine, InvalidTransition
from implementation.store import InMemoryStore, RevisionConflict


def test_state_machine_blocks_invalid_transition():
    sm = FlowStateMachine()
    with pytest.raises(InvalidTransition):
        sm.validate("new", "sent", approval_granted=False)


def test_revision_conflict_raised():
    store = InMemoryStore()
    flow = FlowSnapshot(flow_id="flow_x", project_id="proj_x", status="new")
    store.flows[flow.flow_id] = flow

    flow.status = "triage"
    store.upsert_flow(flow, expected_revision=0)

    flow.status = "executing"
    with pytest.raises(RevisionConflict):
        store.upsert_flow(flow, expected_revision=0)


def test_event_append_and_readback():
    store = InMemoryStore()
    event = CanonicalEvent(
        event_id="evt_1",
        project_id="proj_1",
        flow_id="flow_1",
        task_id="task_1",
        actor_id="actor_1",
        persona_id="persona_1",
        channel="discord",
        type="inbound",
        revision=0,
        trace_id="trace_1",
        timestamp=datetime.now(timezone.utc),
        payload={"text": "hello"},
    )
    store.append_event(event)
    assert len(store.events) == 1
    assert store.events[0].event_id == "evt_1"
