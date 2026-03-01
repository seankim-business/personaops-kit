from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

from implementation.models import CanonicalEvent
from implementation.store_postgres import PostgresStore


@pytest.mark.integration
def test_postgres_store_smoke_roundtrip():
    dsn = os.getenv("PERSONAOPS_POSTGRES_DSN")
    if not dsn:
        pytest.skip("PERSONAOPS_POSTGRES_DSN is not set")

    store = PostgresStore(dsn)
    flow_id = f"flow_pg_{int(datetime.now(timezone.utc).timestamp())}"
    project_id = "proj_pg_it"

    flow = store.ensure_flow(flow_id, project_id)
    assert flow.flow_id == flow_id

    event = CanonicalEvent(
        event_id=f"evt_pg_{int(datetime.now(timezone.utc).timestamp())}",
        project_id=project_id,
        flow_id=flow_id,
        task_id="task_pg_it",
        actor_id="actor_pg_it",
        persona_id="persona_pg_it",
        channel="internal",
        type="inbound",
        revision=0,
        trace_id="trace_pg_it",
        timestamp=datetime.now(timezone.utc),
        payload={"it": True},
    )
    store.append_event(event)

    events = store.list_events_by_flow(flow_id)
    assert any(e.event_id == event.event_id for e in events)
