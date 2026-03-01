from implementation.models import PolicyInput
from implementation.policy import PolicyEngine


def test_high_risk_categories_require_approval():
    engine = PolicyEngine()

    categories = [
        "legal_commitment",
        "financial_transaction",
        "account_privilege_change",
        "public_announcement",
    ]

    for cat in categories:
        decision = engine.evaluate(PolicyInput(category=cat, actor_role="front"))
        assert decision.decision == "requires_approval", f"category={cat}"


def test_low_risk_internal_update_is_allowed():
    engine = PolicyEngine()
    decision = engine.evaluate(PolicyInput(category="internal_update", actor_role="ops"))
    assert decision.decision == "allow"


def test_unknown_category_denied():
    engine = PolicyEngine()
    decision = engine.evaluate(PolicyInput(category="unknown_regression_category", actor_role="front"))
    assert decision.decision == "deny"
