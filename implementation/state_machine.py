from __future__ import annotations

from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parents[1]
FLOW_FILE = BASE / "flows" / "default_flow.yaml"


class InvalidTransition(Exception):
    pass


class FlowStateMachine:
    def __init__(self) -> None:
        data = yaml.safe_load(FLOW_FILE.read_text())
        self.transitions: dict[str, list[str]] = data["transitions"]

    def validate(self, from_status: str, to_status: str, *, approval_granted: bool = False) -> None:
        allowed = self.transitions.get(from_status, [])
        if to_status not in allowed:
            raise InvalidTransition(f"Transition not allowed: {from_status} -> {to_status}")
        if to_status == "sent" and not approval_granted:
            raise InvalidTransition("Approval required before transition to sent")
