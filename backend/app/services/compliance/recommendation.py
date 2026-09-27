"""
Compliance Engine — Recommendation Generator

Produces a deterministic, explainable recommendation for the Procurement
Officer based on rule results, findings, scores, and risk level.

Only three recommendation values are permitted:
    "Compliant — Ready for Officer Confirmation"
    "Needs Clarification — Missing or Unverified Evidence"
    "High-Risk — Officer Review Required"

Decision tree:
    1. IF has_mandatory_failure AND any BLOCKER finding:
        → "High-Risk — Officer Review Required"

    2. ELSE IF has_mandatory_failure OR risk_level in (HIGH, CRITICAL):
        → "High-Risk — Officer Review Required"

    3. ELSE IF any NEEDS_CLARIFICATION rule result
        OR any SOURCE_UNAVAILABLE on mandatory rule
        OR any finding with severity MEDIUM or higher:
        → "Needs Clarification — Missing or Unverified Evidence"

    4. ELSE IF all mandatory rules PASS AND risk_level in (LOW, MODERATE):
        → "Compliant — Ready for Officer Confirmation"

    5. ELSE:
        → "Needs Clarification — Missing or Unverified Evidence"  (safe default)

Design constraints:
    - Deterministic: same inputs always produce same outputs.
    - The recommendation summary references the top findings.
    - Mandatory failures cannot be overridden by a high compliance score.
    - The Officer retains final decision-making authority.
"""

from __future__ import annotations

from .schemas import (
    Finding,
    MatchResult,
    MatchType,
    RECOMMENDATION_CLARIFICATION,
    RECOMMENDATION_COMPLIANT,
    RECOMMENDATION_HIGH_RISK,
    RiskLevel,
    RuleResult,
    RuleResultStatus,
    RulePriority,
    Severity,
)


# ---------------------------------------------------------------------------
# Summary generators
# ---------------------------------------------------------------------------

def _build_compliant_summary(
    rule_results: list[RuleResult],
    findings: list[Finding],
) -> str:
    """Build a summary for a compliant recommendation."""
    mandatory_passed = sum(
        1 for r in rule_results
        if r.priority == RulePriority.MANDATORY
        and r.result == RuleResultStatus.PASS
    )
    total_mandatory = sum(
        1 for r in rule_results
        if r.priority == RulePriority.MANDATORY
        and r.result != RuleResultStatus.NOT_APPLICABLE
    )

    parts = []
    if total_mandatory > 0:
        parts.append(
            f"All {mandatory_passed} applicable mandatory checks passed."
        )

    # Mention key passing checks
    check_names = []
    for r in rule_results:
        if r.result == RuleResultStatus.PASS:
            if "GST" in r.rule_id:
                check_names.append("GST active")
            elif "PAN" in r.rule_id:
                check_names.append("PAN verified")
            elif "UDYAM" in r.rule_id:
                check_names.append("Udyam valid")
            elif "OEM" in r.rule_id:
                check_names.append("OEM valid")
            elif "BLACKLIST" in r.rule_id:
                check_names.append("not blacklisted")
            elif "MCA" in r.rule_id:
                check_names.append("MCA active")

    if check_names:
        parts.append(", ".join(check_names[:4]) + ".")

    info_findings = [f for f in findings if f.severity in (Severity.LOW, Severity.INFO)]
    if not findings or (len(findings) == len(info_findings)):
        parts.append("No material conflicts detected.")

    parts.append("Ready for officer confirmation.")
    return " ".join(parts)


def _build_clarification_summary(
    rule_results: list[RuleResult],
    findings: list[Finding],
) -> str:
    """Build a summary for a clarification recommendation."""
    issues: list[str] = []

    # Mention NEEDS_CLARIFICATION rules
    for r in rule_results:
        if r.result == RuleResultStatus.NEEDS_CLARIFICATION:
            issues.append(f"{r.rule_id}: {r.message}")
        elif r.result == RuleResultStatus.SOURCE_UNAVAILABLE:
            if r.priority == RulePriority.MANDATORY:
                issues.append(f"{r.rule_id}: {r.message}")

    # Mention MEDIUM+ findings
    for f in findings:
        if f.severity in (Severity.MEDIUM, Severity.HIGH):
            issues.append(f"{f.type}: {f.message}")

    if not issues:
        return (
            "Some evidence could not be fully verified. "
            "Officer review is required before confirmation."
        )

    # Take the top 3 issues for the summary
    summary_items = issues[:3]
    result = " | ".join(summary_items)

    if len(issues) > 3:
        result += f" | ... and {len(issues) - 3} more issue(s)."

    return result


def _build_high_risk_summary(
    rule_results: list[RuleResult],
    findings: list[Finding],
    has_mandatory_failure: bool,
) -> str:
    """Build a summary for a high-risk recommendation."""
    critical_issues: list[str] = []

    # Mention BLOCKER findings first
    for f in findings:
        if f.severity == Severity.BLOCKER:
            critical_issues.append(f"{f.type}: {f.message}")

    # Mention mandatory FAILs
    for r in rule_results:
        if (
            r.result == RuleResultStatus.FAIL
            and r.priority == RulePriority.MANDATORY
        ):
            clause_ref = f" ({r.tender_clause})" if r.tender_clause else ""
            critical_issues.append(f"{r.rule_id}{clause_ref}: {r.message}")

    # Mention HIGH severity findings
    for f in findings:
        if f.severity == Severity.HIGH:
            critical_issues.append(f"{f.type}: {f.message}")

    if not critical_issues:
        if has_mandatory_failure:
            return (
                "One or more mandatory compliance checks failed. "
                "Officer review required."
            )
        return "Risk level is elevated. Officer review required."

    # Take top 3 critical issues
    summary_items = critical_issues[:3]
    result = " | ".join(summary_items)

    if len(critical_issues) > 3:
        result += f" | ... and {len(critical_issues) - 3} more critical issue(s)."

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_recommendation(
    rule_results: list[RuleResult],
    findings: list[Finding],
    match_results: list[MatchResult],
    risk_level: RiskLevel,
    has_mandatory_failure: bool,
) -> tuple[str, str]:
    """
    Generate a deterministic compliance recommendation and summary.

    Args:
        rule_results: Results from rule engine evaluation.
        findings: Findings from conflict detector.
        match_results: Match results from entity matcher.
        risk_level: Calculated risk level.
        has_mandatory_failure: Whether any mandatory rule failed.

    Returns:
        Tuple of (recommendation_string, recommendation_summary).
        The recommendation_string is one of the three allowed values.
    """

    has_blocker = any(f.severity == Severity.BLOCKER for f in findings)
    has_medium_or_higher = any(
        f.severity in (Severity.BLOCKER, Severity.HIGH, Severity.MEDIUM)
        for f in findings
    )
    has_needs_clarification = any(
        r.result == RuleResultStatus.NEEDS_CLARIFICATION
        for r in rule_results
    )
    has_mandatory_source_unavailable = any(
        r.result == RuleResultStatus.SOURCE_UNAVAILABLE
        and r.priority == RulePriority.MANDATORY
        for r in rule_results
    )

    # --- Decision tree ---

    # 1. Mandatory failure with BLOCKER → High-Risk
    if has_mandatory_failure and has_blocker:
        return (
            RECOMMENDATION_HIGH_RISK,
            _build_high_risk_summary(
                rule_results, findings, has_mandatory_failure
            ),
        )

    # 2. Mandatory failure OR elevated risk → High-Risk
    if has_mandatory_failure or risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
        return (
            RECOMMENDATION_HIGH_RISK,
            _build_high_risk_summary(
                rule_results, findings, has_mandatory_failure
            ),
        )

    # 3. Needs clarification or source issues or medium+ findings
    if (
        has_needs_clarification
        or has_mandatory_source_unavailable
        or has_medium_or_higher
    ):
        return (
            RECOMMENDATION_CLARIFICATION,
            _build_clarification_summary(rule_results, findings),
        )

    # 4. All mandatory pass and low/moderate risk → Compliant
    all_mandatory_pass = all(
        r.result in (RuleResultStatus.PASS, RuleResultStatus.NOT_APPLICABLE)
        for r in rule_results
        if r.priority == RulePriority.MANDATORY
    )

    if all_mandatory_pass and risk_level in (RiskLevel.LOW, RiskLevel.MODERATE):
        return (
            RECOMMENDATION_COMPLIANT,
            _build_compliant_summary(rule_results, findings),
        )

    # 5. Safe default → Clarification
    return (
        RECOMMENDATION_CLARIFICATION,
        _build_clarification_summary(rule_results, findings),
    )
