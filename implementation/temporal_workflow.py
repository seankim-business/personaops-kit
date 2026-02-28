from __future__ import annotations

"""
Temporal integration scaffold.

This module is intentionally import-safe even when `temporalio` is not installed.
Install orchestration extra to enable runtime registration:

    pip install 'personaops-kit[orchestration]'
"""

from dataclasses import dataclass


@dataclass
class WorkflowTaskInput:
    project_id: str
    flow_id: str
    task_id: str
    trace_id: str


def temporal_available() -> bool:
    try:
        import temporalio  # noqa: F401

        return True
    except Exception:
        return False


def describe_temporal_bootstrap() -> dict:
    return {
        "available": temporal_available(),
        "queue": "personaops-task-queue",
        "workflows": ["PersonaOpsTaskWorkflow"],
        "activities": ["dispatch_worker_activity", "await_approval_activity", "finalize_activity"],
    }
