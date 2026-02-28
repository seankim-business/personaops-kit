from datetime import datetime, timezone

from fastapi.testclient import TestClient

from implementation.control_plane import app, store


def setup_function():
    # reset singleton store between tests when backend supports reset
    if hasattr(store, "reset"):
        store.reset()


def test_discord_inbound_creates_flow_and_event():
    client = TestClient(app)

    res = client.post(
        "/adapters/discord/inbound",
        json={
            "message_id": "m_1",
            "channel_id": "c_1",
            "sender_id": "u_1",
            "content": "hello",
            "project_id": "proj_1",
            "flow_id": "flow_1",
            "task_id": "task_1",
            "persona_id": "persona_1",
        },
    )
    assert res.status_code == 200
    assert res.json()["accepted"] is True

    flow = client.get("/flows/flow_1")
    assert flow.status_code == 200
    assert flow.json()["status"] == "new"


def test_approval_round_trip_moves_flow_to_ready_to_send():
    client = TestClient(app)

    # create flow via inbound event
    client.post(
        "/adapters/discord/inbound",
        json={
            "message_id": "m_2",
            "channel_id": "c_1",
            "sender_id": "u_2",
            "content": "need contract update",
            "project_id": "proj_2",
            "flow_id": "flow_2",
            "task_id": "task_2",
            "persona_id": "persona_2",
        },
    )

    # new -> triage
    t1 = client.post(
        "/flows/flow_2/transition",
        json={
            "expected_revision": 0,
            "to_status": "triage",
            "actor_id": "actor_ops",
            "trace_id": "trace_t1",
            "approval_granted": False,
        },
    )
    assert t1.status_code == 200
    assert t1.json()["revision"] == 1

    # request approval (category requires approval)
    req = client.post(
        "/approvals/request",
        json={
            "project_id": "proj_2",
            "flow_id": "flow_2",
            "task_id": "task_2",
            "requested_by": "actor_ops",
            "actor_role": "ops",
            "category": "legal_commitment",
            "reason": "customer contract commitment",
            "trace_id": "trace_apr_1",
            "expected_revision": 1,
        },
    )
    assert req.status_code == 200
    body = req.json()
    assert body["required"] is True
    approval_id = body["approval"]["approval_id"]

    flow_wait = client.get("/flows/flow_2").json()
    assert flow_wait["status"] == "waiting_approval"

    # approve
    dec = client.post(
        f"/approvals/{approval_id}/decision",
        json={
            "approved_by": "human_approver",
            "approved": True,
            "note": "approved",
            "trace_id": "trace_apr_2",
        },
    )
    assert dec.status_code == 200
    assert dec.json()["flow_status"] == "ready_to_send"


def test_policy_deny_on_unknown_category():
    client = TestClient(app)

    client.post(
        "/adapters/discord/inbound",
        json={
            "message_id": "m_deny",
            "channel_id": "c_1",
            "sender_id": "u_3",
            "content": "unknown action",
            "project_id": "proj_9",
            "flow_id": "flow_9",
            "task_id": "task_9",
            "persona_id": "persona_9",
        },
    )
    client.post(
        "/flows/flow_9/transition",
        json={
            "expected_revision": 0,
            "to_status": "triage",
            "actor_id": "actor_ops",
            "trace_id": "trace_t9",
            "approval_granted": False,
        },
    )

    denied = client.post(
        "/approvals/request",
        json={
            "project_id": "proj_9",
            "flow_id": "flow_9",
            "task_id": "task_9",
            "requested_by": "actor_ops",
            "actor_role": "ops",
            "category": "unknown_category",
            "reason": "should deny",
            "trace_id": "trace_deny",
            "expected_revision": 1,
        },
    )
    assert denied.status_code == 403


def test_outbox_idempotency_and_dead_letter():
    client = TestClient(app)

    first = client.post(
        "/outbox/enqueue",
        json={
            "channel": "discord",
            "target": "channel:1",
            "flow_id": "flow_3",
            "task_id": "task_3",
            "intent": "notify",
            "body": {"text": "hello"},
        },
    )
    second = client.post(
        "/outbox/enqueue",
        json={
            "channel": "discord",
            "target": "channel:1",
            "flow_id": "flow_3",
            "task_id": "task_3",
            "intent": "notify",
            "body": {"text": "hello"},
        },
    )
    assert first.json()["enqueued"] is True
    assert second.json()["enqueued"] is False

    # a second message that always fails to verify retry -> dead letter
    fail = client.post(
        "/outbox/enqueue",
        json={
            "channel": "discord",
            "target": "channel:2",
            "flow_id": "flow_3",
            "task_id": "task_3b",
            "intent": "notify_fail",
            "body": {"force_fail": True},
        },
    )
    assert fail.json()["enqueued"] is True
    fail_key = fail.json()["idempotency_key"]

    for _ in range(4):
        client.post("/outbox/process_once")
        if hasattr(store, "force_outbox_due"):
            try:
                store.force_outbox_due(fail_key)
            except Exception:
                pass
        else:
            # fallback for persistent stores where next_attempt_at cannot be mutated from tests
            pass

    outbox = client.get("/outbox").json()["items"]
    fail_item = next(x for x in outbox if x["idempotency_key"] == fail_key)
    assert fail_item["status"] == "dead_letter"


def test_context_endpoint_returns_recent_events():
    client = TestClient(app)
    client.post(
        "/adapters/discord/inbound",
        json={
            "message_id": "m_ctx",
            "channel_id": "c_1",
            "sender_id": "u_ctx",
            "content": "context me",
            "project_id": "proj_ctx",
            "flow_id": "flow_ctx",
            "task_id": "task_ctx",
            "persona_id": "persona_ctx",
        },
    )

    res = client.get("/context/flow_ctx")
    assert res.status_code == 200
    body = res.json()
    assert body["flow"]["flow_id"] == "flow_ctx"
