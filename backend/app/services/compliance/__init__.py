"""
Compliance Engine — Public API

This module is the single entry point for the compliance engine.
The orchestrator (Member 3) imports and calls ``evaluate_bid_compliance()``
with a ``BidComplianceInput`` bundle and receives a ``ComplianceAssessment``.

Architecture::

    BidComplianceInput
        → entity_matcher.match_entities()         → MatchResult[]
        → conflict_detector.detect_conflicts()    → Finding[]
        → rule_engine.evaluate_rules()            → RuleResult[]
        → scoring.calculate_scores()              → ComplianceScore, RiskScore
        → recommendation.generate_recommendation  → Recommendation
        → ComplianceAssessment

Integration with Member 3 orchestrator::

    # Option A: Direct Pydantic call (if already have Pydantic inputs)
    from app.services.compliance import evaluate_bid_compliance
    result = evaluate_bid_compliance(input_data)

    # Option B: Using the DB adapter (converts DB rows ↔ Pydantic)
    from app.services.compliance.adapters import (
        build_compliance_input,
        persist_compliance_assessment,
    )
    input_data = build_compliance_input(bid, bidder, tender, facts, verifs)
    result = evaluate_bid_compliance(input_data)
    persist_compliance_assessment(result, bid.bid_id, db)

Design constraints:
    - Pure function: no database access, no HTTP calls, no side effects.
    - The orchestrator passes in ALL data and persists the returned assessment.
    - All results are data/rule-driven — never hardcoded per bidder name.
    - Deterministic: same inputs always produce same outputs.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .schemas import (
    BidComplianceInput,
    ComplianceAssessment,
    # Re-export key types for convenience
    BidderProfile,
    ExtractedFact,
    Finding,
    MatchResult,
    RiskLevel,
    RuleResult,
    ScoreBreakdown,
    TenderContext,
    VerificationResult,
    # Recommendation constants
    RECOMMENDATION_CLARIFICATION,
    RECOMMENDATION_COMPLIANT,
    RECOMMENDATION_HIGH_RISK,
    ALLOWED_RECOMMENDATIONS,
)
from .entity_matcher import match_entities
from .conflict_detector import detect_conflicts
from .rule_engine import evaluate_rules
from .scoring import calculate_scores
from .recommendation import generate_recommendation


__all__ = [
    # Entry point
    "evaluate_bid_compliance",
    # Input/output models
    "BidComplianceInput",
    "ComplianceAssessment",
    # Key types re-exported for convenience
    "BidderProfile",
    "ExtractedFact",
    "Finding",
    "MatchResult",
    "RiskLevel",
    "RuleResult",
    "ScoreBreakdown",
    "TenderContext",
    "VerificationResult",
    # Recommendation constants
    "RECOMMENDATION_CLARIFICATION",
    "RECOMMENDATION_COMPLIANT",
    "RECOMMENDATION_HIGH_RISK",
    "ALLOWED_RECOMMENDATIONS",
    # Pipeline components (for advanced usage / testing)
    "match_entities",
    "detect_conflicts",
    "evaluate_rules",
    "calculate_scores",
    "generate_recommendation",
]


def evaluate_bid_compliance(input_data: BidComplianceInput) -> ComplianceAssessment:
    """
    Main entry point for the compliance engine.

    Accepts all extracted facts and verification results for one bid,
    evaluates entity matching, conflicts, tender rules, scores, and
    recommendation. Returns a complete ``ComplianceAssessment``.

    This is a **pure function** — no database access, no HTTP calls, no
    side effects. It receives all data from the orchestrator and returns
    a fully populated assessment.

    Pipeline stages:
        1. Entity matching (PAN, GSTIN, Udyam, CIN, legal name)
        2. Conflict detection (evidence-backed findings)
        3. Tender rule evaluation (YAML-driven, deterministic)
        4. Compliance + risk scoring (weighted categories)
        5. Recommendation generation (decision tree → 3 allowed values)

    Args:
        input_data: Bundle containing tender context, bidder profile,
                    extracted facts, and verification results.

    Returns:
        A ``ComplianceAssessment`` with scores, findings, rule results,
        breakdowns, recommendation, and metadata.

    Raises:
        pydantic.ValidationError: If the input data fails validation.
    """
    tender = input_data.tender
    bidder = input_data.bidder
    extracted_facts = input_data.extracted_facts
    verification_results = input_data.verification_results

    # --- Phase 2: Entity matching ---
    match_results = match_entities(
        bidder, extracted_facts, verification_results,
    )

    # --- Phase 3: Conflict detection ---
    findings = detect_conflicts(
        bidder, extracted_facts, verification_results,
        match_results, tender,
    )

    # --- Phase 4: Rule evaluation ---
    rule_results = evaluate_rules(
        tender, bidder, extracted_facts, verification_results,
    )

    # --- Phase 5: Scoring ---
    compliance_score, risk_score, risk_level, has_mandatory_failure, score_breakdown = (
        calculate_scores(rule_results, findings, match_results)
    )

    # --- Phase 6: Recommendation ---
    recommendation, recommendation_summary = generate_recommendation(
        rule_results, findings, match_results,
        risk_level, has_mandatory_failure,
    )

    # --- Verification coverage ---
    # Percentage of connector sources that returned VERIFIED.
    verified_count = sum(
        1 for v in verification_results
        if v.status == "VERIFIED"
    )
    total_sources = max(len(verification_results), 1)
    verification_coverage = round((verified_count / total_sources) * 100.0, 1)

    # --- Assemble final assessment ---
    return ComplianceAssessment(
        bid_id=input_data.bid_id,
        bidder_id=bidder.bidder_id,
        tender_id=tender.tender_id,
        compliance_score=compliance_score,
        risk_score=risk_score,
        verification_coverage=verification_coverage,
        risk_level=risk_level,
        recommendation=recommendation,
        recommendation_summary=recommendation_summary,
        match_results=match_results,
        findings=findings,
        rule_results=rule_results,
        score_breakdown=score_breakdown,
        has_mandatory_failure=has_mandatory_failure,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
