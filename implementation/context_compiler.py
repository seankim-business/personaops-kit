from __future__ import annotations

from .models import FlowSnapshot


class ContextCompiler:
    """Builds a bounded context pack for persona responses."""

    def compile(self, flow: FlowSnapshot, recent_event_summaries: list[str], persona_profile: dict) -> dict:
        decisions = [d.summary for d in flow.latest_decisions][-5:]
        return {
            "persona_profile": {
                "name": persona_profile.get("name"),
                "tone": persona_profile.get("tone"),
                "meta_leakage_block": True,
            },
            "flow": {
                "flow_id": flow.flow_id,
                "project_id": flow.project_id,
                "status": flow.status,
                "revision": flow.revision,
                "open_tasks": flow.open_tasks[:10],
            },
            "latest_decisions": decisions,
            "recent_events": recent_event_summaries[-10:],
        }
