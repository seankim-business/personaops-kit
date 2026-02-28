from implementation.temporal_workflow import describe_temporal_bootstrap
from implementation.trace import trace_log


def test_trace_log_never_raises_without_langfuse():
    trace_log("unit_test_event", trace_id="trace_test", detail="ok")


def test_temporal_scaffold_import_safe():
    info = describe_temporal_bootstrap()
    assert "available" in info
    assert info["queue"] == "personaops-task-queue"
