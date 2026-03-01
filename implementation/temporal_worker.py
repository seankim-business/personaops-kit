from __future__ import annotations

import os
from dataclasses import dataclass

from .temporal_workflow import describe_temporal_bootstrap, temporal_available


@dataclass
class TemporalWorkerConfig:
    endpoint: str = os.getenv("PERSONAOPS_TEMPORAL_ENDPOINT", "localhost:7233")
    namespace: str = os.getenv("PERSONAOPS_TEMPORAL_NAMESPACE", "default")
    task_queue: str = os.getenv("PERSONAOPS_TEMPORAL_TASK_QUEUE", "personaops-task-queue")


def start_worker_dry_run() -> dict:
    """
    Dry-run helper for deployment/runbook checks.

    This does not connect to Temporal server yet; it validates configuration
    and reports readiness so platform teams can wire process supervision first.
    """

    cfg = TemporalWorkerConfig()
    bootstrap = describe_temporal_bootstrap()
    return {
        "temporal_available": temporal_available(),
        "endpoint": cfg.endpoint,
        "namespace": cfg.namespace,
        "task_queue": cfg.task_queue,
        "bootstrap": bootstrap,
    }
