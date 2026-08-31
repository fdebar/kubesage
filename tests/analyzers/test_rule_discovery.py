from kubesage.analyzers.rules.application.application_error import (
    ApplicationErrorRule,
)
from kubesage.analyzers.rules.rule_loader import discover_rules


def test_application_error_rule_is_discovered() -> None:
    rules = discover_rules()

    rule_ids = {rule.rule_id for rule in rules}

    assert "application_error" in rule_ids
    assert any(isinstance(rule, ApplicationErrorRule) for rule in rules)
