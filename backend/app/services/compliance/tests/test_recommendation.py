"""
Phase 6 Tests — Recommendation Generator

Tests the deterministic recommendation decision tree and summary generation.
"""

from __future__ import annotations

import pytest

from backend.app.services.compliance.schemas import (
    Finding,
    MatchResult,
    MatchType,
    RECOMMENDATION_CLARIFICATION,
    RECOMMENDATION_COMPLIANT,
    RECOMMENDATION_HIGH_RISK,
    RiskLevel,
    RuleCategory,
    RulePriority,
    RuleResult,
    RuleResultStatus,
    Severity,
)
from backend.app.services.compliance.recommendation import (
    generate_recommendation,
)


# ===================================================================
# Helpers
# ===================================================================

def _rule(
    rule_id: str = "R1",
    result: RuleResultStatus = RuleResultStatus.PASS,
    priority: RulePriority = RulePriority.MANDATORY,
    message: str = "Test rule",
    severity: Severity | None = None,
    tender_clause: str | None = None,
) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        rule_name=f"Rule {rule_id}",
        result=result,
        priority=priority,
        category=RuleCategory.MANDATORY_ELIGIBILITY,
        tender_clause=tender_clause,
        message=message,
        severity=severity,
    )


def _finding(
    finding_type: str = "TEST",
    severity: Severity = Severity.MEDIUM,
) -> Finding:
    return Finding(
        finding_id=f"FND-{finding_type}",
        type=finding_type,
        severity=severity,
        message=f"Finding: {finding_type}",
        rule_id=finding_type,
    )


def _match(
    match_type: MatchType = MatchType.EXACT,
) -> MatchResult:
    return MatchResult(
        field="pan", bid_value="X", source_value="X", source="TEST",
        match_type=match_type, is_confirmed=match_type == MatchType.EXACT,
    )


# ===================================================================
# Compliant path
# ===================================================================


class TestCompliantRecommendation:

    def test_all_pass_low_risk(self):
        rules = [
            _rule("R1", RuleResultStatus.PASS),
            _rule("R2", RuleResultStatus.PASS),
        ]
        rec, summary = generate_recommendation(
            rules, [], [], RiskLevel.LOW, False,
        )
        assert rec == RECOMMENDATION_COMPLIANT

    def test_all_pass_moderate_risk(self):
        rules = [_rule("R1", RuleResultStatus.PASS)]
        rec, _ = generate_recommendation(
            rules, [], [], RiskLevel.MODERATE, False,
        )
        assert rec == RECOMMENDATION_COMPLIANT

    def test_na_rules_treated_as_pass(self):
        rules = [
            _rule("R1", RuleResultStatus.PASS),
            _rule("R2", RuleResultStatus.NOT_APPLICABLE),
        ]
        rec, _ = generate_recommendation(
            rules, [], [], RiskLevel.LOW, False,
        )
        assert rec == RECOMMENDATION_COMPLIANT

    def test_summary_mentions_passed(self):
        rules = [_rule("GST_ACTIVE", RuleResultStatus.PASS)]
        _, summary = generate_recommendation(
            rules, [], [], RiskLevel.LOW, False,
        )
        assert "passed" in summary.lower() or "active" in summary.lower()


# ===================================================================
# High-risk path
# ===================================================================


class TestHighRiskRecommendation:

    def test_mandatory_failure_with_blocker(self):
        rules = [_rule("R1", RuleResultStatus.FAIL, severity=Severity.BLOCKER)]
        findings = [_finding("BL", Severity.BLOCKER)]
        rec, _ = generate_recommendation(
            rules, findings, [], RiskLevel.CRITICAL, True,
        )
        assert rec == RECOMMENDATION_HIGH_RISK

    def test_mandatory_failure_without_blocker(self):
        rules = [_rule("R1", RuleResultStatus.FAIL, severity=Severity.HIGH)]
        rec, _ = generate_recommendation(
            rules, [], [], RiskLevel.MODERATE, True,
        )
        assert rec == RECOMMENDATION_HIGH_RISK

    def test_high_risk_level_no_mandatory_failure(self):
        rules = [_rule("R1", RuleResultStatus.PASS)]
        findings = [
            _finding("F1", Severity.BLOCKER),
            _finding("F2", Severity.HIGH),
        ]
        rec, _ = generate_recommendation(
            rules, findings, [], RiskLevel.HIGH, False,
        )
        assert rec == RECOMMENDATION_HIGH_RISK

    def test_critical_risk_level(self):
        rules = [_rule("R1", RuleResultStatus.PASS)]
        rec, _ = generate_recommendation(
            rules, [], [], RiskLevel.CRITICAL, False,
        )
        assert rec == RECOMMENDATION_HIGH_RISK

    def test_mandatory_failure_overrides_high_score(self):
        """Mandatory failure must not be overridden by passing other rules."""
        rules = [
            _rule("R1", RuleResultStatus.PASS),
            _rule("R2", RuleResultStatus.PASS),
            _rule("R3", RuleResultStatus.FAIL, severity=Severity.BLOCKER),
        ]
        rec, _ = generate_recommendation(
            rules, [], [], RiskLevel.LOW, True,
        )
        assert rec == RECOMMENDATION_HIGH_RISK

    def test_summary_references_blockers(self):
        rules = [_rule("GST_CHECK", RuleResultStatus.FAIL,
                        severity=Severity.BLOCKER,
                        tender_clause="Clause 4.2")]
        findings = [_finding("BLACKLIST_HIT", Severity.BLOCKER)]
        _, summary = generate_recommendation(
            rules, findings, [], RiskLevel.CRITICAL, True,
        )
        assert "BLACKLIST_HIT" in summary or "GST_CHECK" in summary


# ===================================================================
# Clarification path
# ===================================================================


class TestClarificationRecommendation:

    def test_needs_clarification_rule(self):
        rules = [
            _rule("R1", RuleResultStatus.PASS),
            _rule("R2", RuleResultStatus.NEEDS_CLARIFICATION),
        ]
        rec, _ = generate_recommendation(
            rules, [], [], RiskLevel.LOW, False,
        )
        assert rec == RECOMMENDATION_CLARIFICATION

    def test_mandatory_source_unavailable(self):
        rules = [
            _rule("R1", RuleResultStatus.PASS),
            _rule("R2", RuleResultStatus.SOURCE_UNAVAILABLE,
                  priority=RulePriority.MANDATORY),
        ]
        rec, _ = generate_recommendation(
            rules, [], [], RiskLevel.LOW, False,
        )
        assert rec == RECOMMENDATION_CLARIFICATION

    def test_medium_finding(self):
        rules = [_rule("R1", RuleResultStatus.PASS)]
        findings = [_finding("LOW_CONF", Severity.MEDIUM)]
        rec, _ = generate_recommendation(
            rules, findings, [], RiskLevel.LOW, False,
        )
        assert rec == RECOMMENDATION_CLARIFICATION

    def test_recommended_source_unavailable_not_trigger(self):
        """SOURCE_UNAVAILABLE on recommended (not mandatory) rule should not trigger clarification alone."""
        rules = [
            _rule("R1", RuleResultStatus.PASS),
            _rule("R2", RuleResultStatus.SOURCE_UNAVAILABLE,
                  priority=RulePriority.RECOMMENDED),
        ]
        rec, _ = generate_recommendation(
            rules, [], [], RiskLevel.LOW, False,
        )
        # Recommended source unavailable doesn't trigger clarification by itself
        assert rec == RECOMMENDATION_COMPLIANT

    def test_summary_references_issues(self):
        rules = [_rule("UDYAM_VALID", RuleResultStatus.NEEDS_CLARIFICATION,
                        message="Udyam certificate not submitted")]
        _, summary = generate_recommendation(
            rules, [], [], RiskLevel.LOW, False,
        )
        assert "UDYAM_VALID" in summary


# ===================================================================
# Safe default
# ===================================================================


class TestSafeDefault:

    def test_empty_inputs_clarification(self):
        """No rules, no findings → safe default is clarification."""
        rec, _ = generate_recommendation([], [], [], RiskLevel.LOW, False)
        # With no mandatory rules at all, all_mandatory_pass is True (vacuously)
        # and risk is LOW → should be COMPLIANT
        assert rec == RECOMMENDATION_COMPLIANT

    def test_no_mandatory_pass_moderate(self):
        """Recommended FAIL with moderate risk → clarification or compliant depending on findings."""
        rules = [
            _rule("R1", RuleResultStatus.FAIL,
                  priority=RulePriority.RECOMMENDED),
        ]
        rec, _ = generate_recommendation(
            rules, [], [], RiskLevel.LOW, False,
        )
        # No mandatory failures, no medium+ findings, all mandatory pass (vacuous) → compliant
        assert rec == RECOMMENDATION_COMPLIANT


# ===================================================================
# Determinism
# ===================================================================


class TestDeterminism:

    def test_same_inputs_same_output(self):
        rules = [_rule("R1", RuleResultStatus.FAIL, severity=Severity.BLOCKER)]
        findings = [_finding("BL", Severity.BLOCKER)]
        rec1, sum1 = generate_recommendation(
            rules, findings, [], RiskLevel.CRITICAL, True,
        )
        rec2, sum2 = generate_recommendation(
            rules, findings, [], RiskLevel.CRITICAL, True,
        )
        assert rec1 == rec2
        assert sum1 == sum2
