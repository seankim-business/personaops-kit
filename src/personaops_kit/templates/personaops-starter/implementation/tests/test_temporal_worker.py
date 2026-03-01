from fastapi.testclient import TestClient

from implementation.control_plane import app
from implementation.temporal_worker import start_worker_dry_run


def test_temporal_worker_dry_run_shape():
    info = start_worker_dry_run()
    assert "temporal_available" in info
    assert info["task_queue"] == "personaops-task-queue"
    assert "bootstrap" in info


def test_temporal_bootstrap_endpoint():
    client = TestClient(app)
    res = client.get("/temporal/bootstrap")
    assert res.status_code == 200
    body = res.json()
    assert body["task_queue"] == "personaops-task-queue"
