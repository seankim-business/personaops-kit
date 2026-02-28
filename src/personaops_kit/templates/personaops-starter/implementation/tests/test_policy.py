from implementation.models import PolicyInput
from implementation.policy import PolicyEngine


def test_policy_requires_approval_for_legal_commitment():
    engine = PolicyEngine()
    decision = engine.evaluate(PolicyInput(category="legal_commitment", actor_role="front"))
    assert decision.decision == "requires_approval"


def test_policy_default_deny_unknown_category():
    engine = PolicyEngine()
    decision = engine.evaluate(PolicyInput(category="unknown_category", actor_role="front"))
    assert decision.decision == "deny"
