"""
Compliance Engine — Scoring

Calculates compliance score, risk score, risk level, and score breakdowns
from rule results and findings.

Compliance Score:
    Weighted sum across three categories:
        mandatory_eligibility:  0.60
        statutory_compliance:   0.25
        documentation:          0.15
    
    category_fulfillment = rules_passed / rules_applicable
    compliance_score = sum(weight * fulfillment) * 100

Risk Score:
    Additive risk points (capped at 100):
        BLOCKER finding:                    +30
        HIGH finding:                       +20
        MEDIUM finding:                     +10
        Mandatory rule FAIL:                +25
        SOURCE_UNAVAILABLE on mandatory:    +15
        NEEDS_CLARIFICATION on mandatory:   +15
        Identity MISMATCH (match_type):     +20
        Low-confidence material fact:       +5

Risk Level:
    0–24:   LOW
    25–49:  MODERATE
    50–74:  HIGH
    75–100: CRITICAL

Design constraints:
    - Deterministic: same inputs always produce same outputs.
    - No database access, no HTTP calls, no LLM calls, no side effects.
    - NOT_APPLICABLE rules are excluded from the denominator.
    - has_mandatory_failure is True if ANY mandatory rule has FAIL result.
"""

from __future__ import annotations

from .schemas import (
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


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CATEGORY_WEIGHTS: dict[RuleCategory, float] = {
    RuleCategory.MANDATORY_ELIGIBILITY: 0.60,
    RuleCategory.STATUTORY_COMPLIANCE: 0.25,
    RuleCategory.DOCUMENTATION: 0.15,
}

_FINDING_RISK_POINTS: dict[Severity, int] = {
    Severity.BLOCKER: 30,
    Severity.HIGH: 20,
    Severity.MEDIUM: 10,
    Severity.LOW: 0,
    Severity.INFO: 0,
}


# ---------------------------------------------------------------------------
# Compliance score
# ---------------------------------------------------------------------------

def _calculate_compliance_score(
    rule_results: list[RuleResult],
) -> tuple[float, list[ScoreBreakdown]]:
    """
    Calculate the weighted compliance score and per-category breakdowns.

    Returns:
        (compliance_score: 0–100, breakdowns: list[ScoreBreakdown])
    """
    # Group rules by category
    category_rules: dict[RuleCategory, list[RuleResult]] = {
        cat: [] for cat in RuleCategory
    }
    for rr in rule_results:
        category_rules[rr.category].append(rr)

    breakdowns: list[ScoreBreakdown] = []
    total_score = 0.0

    for category in RuleCategory:
        rules = category_rules[category]
        weight = _CATEGORY_WEIGHTS.get(category, 0.0)

        # Exclude NOT_APPLICABLE from denominator
        applicable = [
            r for r in rules
            if r.result != RuleResultStatus.NOT_APPLICABLE
        ]
        passed = [
            r for r in applicable
            if r.result == RuleResultStatus.PASS
        ]

        rules_total = len(applicable)
        rules_passed = len(passed)

        if rules_total > 0:
            fulfilled = rules_passed / rules_total
        else:
            fulfilled = 1.0  # No applicable rules → fully fulfilled

        total_score += weight * fulfilled

        # Build detail notes
        details: list[str] = []
        for r in rules:
            if r.result == RuleResultStatus.NOT_APPLICABLE:
                details.append(f"{r.rule_id}: Not applicable")
            elif r.result == RuleResultStatus.PASS:
                details.append(f"{r.rule_id}: Passed")
            elif r.result == RuleResultStatus.FAIL:
                details.append(f"{r.rule_id}: FAILED — {r.message}")
            elif r.result == RuleResultStatus.NEEDS_CLARIFICATION:
                details.append(f"{r.rule_id}: Needs clarification — {r.message}")
            elif r.result == RuleResultStatus.SOURCE_UNAVAILABLE:
                details.append(f"{r.rule_id}: Source unavailable — {r.message}")

        breakdowns.append(ScoreBreakdown(
            category=category,
            weight=weight,
            fulfilled=round(fulfilled, 4),
            rules_passed=rules_passed,
            rules_total=rules_total,
            details=details,
        ))

    compliance_score = round(total_score * 100, 2)
    return compliance_score, breakdowns


# ---------------------------------------------------------------------------
# Risk score
# ---------------------------------------------------------------------------

def _calculate_risk_score(
    findings: list[Finding],
    rule_results: list[RuleResult],
    match_results: list[MatchResult],
) -> tuple[float, RiskLevel, bool]:
    """
    Calculate the additive risk score, risk level, and mandatory failure flag.

    Returns:
        (risk_score: 0–100, risk_level: RiskLevel, has_mandatory_failure: bool)
    """
    risk_points = 0.0
    has_mandatory_failure = False

    # Points from findings
    for f in findings:
        risk_points += _FINDING_RISK_POINTS.get(f.severity, 0)

    # Points from rule results
    for rr in rule_results:
        is_mandatory = rr.priority == RulePriority.MANDATORY

        if rr.result == RuleResultStatus.FAIL:
            if is_mandatory:
                risk_points += 25
                has_mandatory_failure = True

        elif rr.result == RuleResultStatus.SOURCE_UNAVAILABLE:
            if is_mandatory:
                risk_points += 15

        elif rr.result == RuleResultStatus.NEEDS_CLARIFICATION:
            if is_mandatory:
                risk_points += 15

    # Points from identity mismatches in match results
    for mr in match_results:
        if mr.match_type == MatchType.MISMATCH:
            risk_points += 20

    # Cap at 100
    risk_score = min(round(risk_points, 2), 100.0)

    # Determine risk level
    if risk_score >= 75:
        risk_level = RiskLevel.CRITICAL
    elif risk_score >= 50:
        risk_level = RiskLevel.HIGH
    elif risk_score >= 25:
        risk_level = RiskLevel.MODERATE
    else:
        risk_level = RiskLevel.LOW

    return risk_score, risk_level, has_mandatory_failure


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_scores(
    rule_results: list[RuleResult],
    findings: list[Finding],
    match_results: list[MatchResult],
) -> tuple[float, float, RiskLevel, bool, list[ScoreBreakdown]]:
    """
    Calculate compliance score, risk score, risk level, mandatory failure
    flag, and score breakdowns.

    Args:
        rule_results: Results from rule engine evaluation.
        findings: Findings from conflict detector.
        match_results: Match results from entity matcher.

    Returns:
        Tuple of:
            compliance_score (0–100),
            risk_score (0–100),
            risk_level (RiskLevel enum),
            has_mandatory_failure (bool),
            score_breakdown (list[ScoreBreakdown])
    """
    compliance_score, breakdowns = _calculate_compliance_score(rule_results)
    risk_score, risk_level, has_mandatory_failure = _calculate_risk_score(
        findings, rule_results, match_results,
    )

    return compliance_score, risk_score, risk_level, has_mandatory_failure, breakdowns
