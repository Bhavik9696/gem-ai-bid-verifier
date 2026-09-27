"""
Phase 5 Tests — Scoring

Tests compliance score calculation, risk score accumulation, risk level
mapping, mandatory failure gating, and score breakdowns.
"""

from __future__ import annotations

import pytest

from backend.app.services.compliance.schemas import (
    Finding,
    MatchResult,
    MatchType,
    RiskLevel,
    RuleCategory,
    RulePriority,
    RuleResult,
    RuleResultStatus,
    ScoreBreakdown,
    Severity,
)
from backend.app.services.compliance.scoring import calculate_scores


# ===================================================================
# Helpers — fixture factories
# ===================================================================

def _make_rule_result(
    rule_id: str,
    result: RuleResultStatus = RuleResultStatus.PASS,
    priority: RulePriority = RulePriority.MANDATORY,
    category: RuleCategory = RuleCategory.MANDATORY_ELIGIBILITY,
    severity: Severity | None = None,
) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        rule_name=f"Rule {rule_id}",
        result=result,
        priority=priority,
        category=category,
        tender_clause=None,
        message=f"Rule {rule_id} result: {result.value}",
        severity=severity,
    )


def _make_finding(
    finding_type: str,
    severity: Severity,
) -> Finding:
    return Finding(
        finding_id=f"FND-{finding_type}",
        type=finding_type,
        severity=severity,
        message=f"Finding: {finding_type}",
        rule_id=finding_type,
    )


def _make_match(
    field: str,
    match_type: MatchType = MatchType.EXACT,
) -> MatchResult:
    return MatchResult(
        field=field,
        bid_value="X",
        source_value="X",
        source="TEST",
        match_type=match_type,
        is_confirmed=match_type == MatchType.EXACT,
    )


# ===================================================================
# All pass scenario
# ===================================================================


class TestAllPassScoring:
    """All rules pass, no findings, no mismatches."""

    def test_perfect_compliance_score(self):
        rules = [
            _make_rule_result("R1", RuleResultStatus.PASS, category=RuleCategory.MANDATORY_ELIGIBILITY),
            _make_rule_result("R2", RuleResultStatus.PASS, category=RuleCategory.MANDATORY_ELIGIBILITY),
            _make_rule_result("R3", RuleResultStatus.PASS, category=RuleCategory.STATUTORY_COMPLIANCE),
            _make_rule_result("R4", RuleResultStatus.PASS, category=RuleCategory.DOCUMENTATION),
        ]
        score, risk, level, mandatory_fail, breakdowns = calculate_scores(rules, [], [])
        assert score == 100.0
        assert risk == 0.0
        assert level == RiskLevel.LOW
        assert mandatory_fail is False

    def test_not_applicable_excluded_from_denominator(self):
        rules = [
            _make_rule_result("R1", RuleResultStatus.PASS, category=RuleCategory.MANDATORY_ELIGIBILITY),
            _make_rule_result("R2", RuleResultStatus.NOT_APPLICABLE, category=RuleCategory.MANDATORY_ELIGIBILITY),
            _make_rule_result("R3", RuleResultStatus.PASS, category=RuleCategory.STATUTORY_COMPLIANCE),
            _make_rule_result("R4", RuleResultStatus.PASS, category=RuleCategory.DOCUMENTATION),
        ]
        score, _, _, _, breakdowns = calculate_scores(rules, [], [])
        # NA excluded: mandatory has 1/1 = 1.0
        assert score == 100.0
        # Verify breakdown
        mand_bd = next(b for b in breakdowns if b.category == RuleCategory.MANDATORY_ELIGIBILITY)
        assert mand_bd.rules_total == 1  # NA excluded
        assert mand_bd.rules_passed == 1


# ===================================================================
# Mandatory failure
# ===================================================================


class TestMandatoryFailure:

    def test_mandatory_fail_sets_flag(self):
        rules = [
            _make_rule_result("R1", RuleResultStatus.FAIL,
                              priority=RulePriority.MANDATORY,
                              category=RuleCategory.MANDATORY_ELIGIBILITY,
                              severity=Severity.BLOCKER),
            _make_rule_result("R2", RuleResultStatus.PASS, category=RuleCategory.STATUTORY_COMPLIANCE),
        ]
        score, risk, level, mandatory_fail, _ = calculate_scores(rules, [], [])
        assert mandatory_fail is True
        assert score < 100.0
        assert risk >= 25  # at least 25 points for mandatory FAIL

    def test_recommended_fail_does_not_set_flag(self):
        rules = [
            _make_rule_result("R1", RuleResultStatus.PASS, category=RuleCategory.MANDATORY_ELIGIBILITY),
            _make_rule_result("R2", RuleResultStatus.FAIL,
                              priority=RulePriority.RECOMMENDED,
                              category=RuleCategory.STATUTORY_COMPLIANCE),
        ]
        _, _, _, mandatory_fail, _ = calculate_scores(rules, [], [])
        assert mandatory_fail is False  # recommended, not mandatory


# ===================================================================
# Risk score accumulation
# ===================================================================


class TestRiskScore:

    def test_blocker_finding_adds_30(self):
        findings = [_make_finding("BL_HIT", Severity.BLOCKER)]
        _, risk, _, _, _ = calculate_scores([], findings, [])
        assert risk >= 30.0

    def test_high_finding_adds_20(self):
        findings = [_make_finding("HIGH_F", Severity.HIGH)]
        _, risk, _, _, _ = calculate_scores([], findings, [])
        assert risk >= 20.0

    def test_medium_finding_adds_10(self):
        findings = [_make_finding("MED_F", Severity.MEDIUM)]
        _, risk, _, _, _ = calculate_scores([], findings, [])
        assert risk >= 10.0

    def test_risk_capped_at_100(self):
        findings = [_make_finding(f"F{i}", Severity.BLOCKER) for i in range(10)]
        _, risk, level, _, _ = calculate_scores([], findings, [])
        assert risk == 100.0
        assert level == RiskLevel.CRITICAL

    def test_identity_mismatch_adds_20(self):
        matches = [_make_match("pan", MatchType.MISMATCH)]
        _, risk, _, _, _ = calculate_scores([], [], matches)
        assert risk >= 20.0

    def test_mandatory_fail_adds_25_to_risk(self):
        rules = [
            _make_rule_result("R1", RuleResultStatus.FAIL,
                              priority=RulePriority.MANDATORY,
                              severity=Severity.BLOCKER),
        ]
        _, risk, _, _, _ = calculate_scores(rules, [], [])
        assert risk >= 25.0

    def test_source_unavailable_mandatory_adds_15(self):
        rules = [
            _make_rule_result("R1", RuleResultStatus.SOURCE_UNAVAILABLE,
                              priority=RulePriority.MANDATORY),
        ]
        _, risk, _, _, _ = calculate_scores(rules, [], [])
        assert risk >= 15.0

    def test_needs_clarification_mandatory_adds_15(self):
        rules = [
            _make_rule_result("R1", RuleResultStatus.NEEDS_CLARIFICATION,
                              priority=RulePriority.MANDATORY),
        ]
        _, risk, _, _, _ = calculate_scores(rules, [], [])
        assert risk >= 15.0


# ===================================================================
# Risk level mapping
# ===================================================================


class TestRiskLevel:

    def test_low(self):
        _, _, level, _, _ = calculate_scores([], [], [])
        assert level == RiskLevel.LOW

    def test_moderate(self):
        findings = [_make_finding("F1", Severity.BLOCKER)]  # 30 → MODERATE
        _, risk, level, _, _ = calculate_scores([], findings, [])
        assert 25.0 <= risk < 50.0
        assert level == RiskLevel.MODERATE

    def test_high(self):
        findings = [
            _make_finding("F1", Severity.BLOCKER),  # 30
            _make_finding("F2", Severity.HIGH),  # 20
        ]
        _, risk, level, _, _ = calculate_scores([], findings, [])
        assert risk >= 50.0
        assert level == RiskLevel.HIGH

    def test_critical(self):
        findings = [
            _make_finding("F1", Severity.BLOCKER),  # 30
            _make_finding("F2", Severity.BLOCKER),  # 30
            _make_finding("F3", Severity.HIGH),  # 20
        ]
        _, risk, level, _, _ = calculate_scores([], findings, [])
        assert risk >= 75.0
        assert level == RiskLevel.CRITICAL


# ===================================================================
# Score breakdowns
# ===================================================================


class TestScoreBreakdowns:

    def test_three_categories_always_present(self):
        rules = [_make_rule_result("R1", RuleResultStatus.PASS)]
        _, _, _, _, breakdowns = calculate_scores(rules, [], [])
        cats = {b.category for b in breakdowns}
        assert RuleCategory.MANDATORY_ELIGIBILITY in cats
        assert RuleCategory.STATUTORY_COMPLIANCE in cats
        assert RuleCategory.DOCUMENTATION in cats

    def test_weights_sum_to_1(self):
        rules = [_make_rule_result("R1", RuleResultStatus.PASS)]
        _, _, _, _, breakdowns = calculate_scores(rules, [], [])
        total_weight = sum(b.weight for b in breakdowns)
        assert abs(total_weight - 1.0) < 0.001

    def test_breakdown_details_populated(self):
        rules = [
            _make_rule_result("R1", RuleResultStatus.PASS, category=RuleCategory.MANDATORY_ELIGIBILITY),
            _make_rule_result("R2", RuleResultStatus.FAIL, category=RuleCategory.MANDATORY_ELIGIBILITY),
        ]
        _, _, _, _, breakdowns = calculate_scores(rules, [], [])
        mand_bd = next(b for b in breakdowns if b.category == RuleCategory.MANDATORY_ELIGIBILITY)
        assert mand_bd.rules_total == 2
        assert mand_bd.rules_passed == 1
        assert mand_bd.fulfilled == 0.5
        assert len(mand_bd.details) == 2


# ===================================================================
# Combined scenario
# ===================================================================


class TestCombinedScoring:

    def test_multiple_failures_and_findings(self):
        """Multiple failures across categories + findings → low score, high risk."""
        rules = [
            _make_rule_result("R1", RuleResultStatus.FAIL,
                              priority=RulePriority.MANDATORY,
                              category=RuleCategory.MANDATORY_ELIGIBILITY,
                              severity=Severity.BLOCKER),
            _make_rule_result("R2", RuleResultStatus.PASS,
                              category=RuleCategory.MANDATORY_ELIGIBILITY),
            _make_rule_result("R3", RuleResultStatus.FAIL,
                              priority=RulePriority.RECOMMENDED,
                              category=RuleCategory.STATUTORY_COMPLIANCE),
            _make_rule_result("R4", RuleResultStatus.PASS,
                              category=RuleCategory.DOCUMENTATION),
        ]
        findings = [
            _make_finding("GST_NAME", Severity.HIGH),
            _make_finding("PAN_MISMATCH", Severity.BLOCKER),
        ]
        matches = [_make_match("pan", MatchType.MISMATCH)]

        score, risk, level, mandatory_fail, breakdowns = calculate_scores(
            rules, findings, matches,
        )

        assert mandatory_fail is True
        assert score < 100.0
        # Risk: 25 (mandatory FAIL) + 20 (HIGH) + 30 (BLOCKER) + 20 (mismatch) = 95
        assert risk >= 75.0
        assert level == RiskLevel.CRITICAL
