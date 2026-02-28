from __future__ import annotations

from pathlib import Path

import yaml

from .models import PolicyDecision, PolicyInput

BASE = Path(__file__).resolve().parents[1]
RULES_FILE = BASE / "policies" / "approval_rules.yaml"


class PolicyEngine:
    def __init__(self) -> None:
        data = yaml.safe_load(RULES_FILE.read_text())
        self.rules = data.get("rules", [])
        self.default_decision = data.get("default_decision", "deny")

    def evaluate(self, policy_input: PolicyInput) -> PolicyDecision:
        for rule in self.rules:
            if rule.get("match", {}).get("category") == policy_input.category:
                return PolicyDecision(decision=rule["decision"], rule_id=rule.get("id"))
        return PolicyDecision(decision=self.default_decision)
