"""
Compliance Engine — Database Adapter

Conversion utilities between the SQLAlchemy database models owned by
Member 3 (``app.models.entities``) and the Pydantic models used inside
the compliance engine (``app.services.compliance.schemas``).

This module exists so the orchestrator can:
    1. Convert DB rows → ``BidComplianceInput``
    2. Call ``evaluate_bid_compliance(input_data)``
    3. Convert ``ComplianceAssessment`` → DB rows to persist

Member 5 does NOT own the database models or the orchestrator.
This adapter is a suggested integration helper that Member 3 can import.

Usage example for Member 3's orchestrator::

    from app.services.compliance.adapters import (
        build_compliance_input,
        persist_compliance_assessment,
    )
    from app.services.compliance import evaluate_bid_compliance

    # In _evaluate_compliance():
    compliance_input = build_compliance_input(
        bid,
        bidder,
        tender,
        extracted_facts_rows,
        verification_rows,
    )
    assessment = evaluate_bid_compliance(compliance_input)
    persist_compliance_assessment(assessment, bid.bid_id, db)

Design constraints:
    - No business logic — only data mapping.
    - Imports from ``app.models.entities`` are guarded so the compliance
      engine remains independently testable without a database.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .schemas import (
    BidComplianceInput,
    BidderProfile,
    ComplianceAssessment,
    ExtractedFact,
    TenderContext,
    VerificationResult,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# ---------------------------------------------------------------------------
# DB → Pydantic: build the input bundle for evaluate_bid_compliance()
# ---------------------------------------------------------------------------

def build_compliance_input(
    bid: Any,
    bidder: Any,
    tender: Any,
    extracted_facts_rows: list[Any],
    verification_rows: list[Any],
) -> BidComplianceInput:
    """
    Convert SQLAlchemy DB rows into a ``BidComplianceInput`` bundle.

    Args:
        bid: A ``models.entities.Bid`` row.
        bidder: A ``models.entities.Bidder`` row.
        tender: A ``models.entities.Tender`` row.
        extracted_facts_rows: List of ``models.entities.ExtractedFact`` rows.
        verification_rows: List of ``models.entities.VerificationResult`` rows.

    Returns:
        A ``BidComplianceInput`` ready to pass to ``evaluate_bid_compliance()``.
    """
    eligibility = tender.eligibility_conditions or {}

    tender_context = TenderContext(
        tender_id=tender.tender_id,
        title=tender.title,
        closing_date=tender.bid_closing_date or "",
        category=tender.category,
        rulebook_id=_derive_rulebook_id(tender),
        make_in_india_required=bool(eligibility.get("makeInIndiaRequired", False)),
        local_content_threshold=float(eligibility.get("localContentThreshold", 0)) or None,
        msme_mandatory=bool(eligibility.get("msmeRequired", False)),
        oem_required=bool(eligibility.get("oemRequired", False)),
        mandatory_documents=tender.mandatory_documents or [],
    )

    bidder_profile = BidderProfile(
        bidder_id=bidder.bidder_id,
        legal_name=bidder.legal_name,
        pan=bidder.pan,
        gstin=bidder.gstin,
        udyam_number=bidder.udyam_number,
        cin=bidder.cin,
        authorised_signatory=bidder.authorised_signatory,
    )

    facts = [
        ExtractedFact(
            field=ef.field,
            value=ef.value,
            confidence=ef.confidence if ef.confidence is not None else 1.0,
            document_id=ef.document_id or "",
            page=ef.page,
            document_type=None,
        )
        for ef in extracted_facts_rows
    ]

    verifications = [
        VerificationResult(
            source=vr.source,
            mode=vr.mode or "DEMO",
            identifier=vr.identifier,
            status=vr.status,
            verified_facts=vr.verified_facts or {},
            checked_at=vr.checked_at or "",
            evidence_reference=vr.evidence_reference,
        )
        for vr in verification_rows
    ]

    return BidComplianceInput(
        bid_id=bid.bid_id,
        tender=tender_context,
        bidder=bidder_profile,
        extracted_facts=facts,
        verification_results=verifications,
    )


def _derive_rulebook_id(tender: Any) -> str:
    """
    Derive the YAML rulebook ID from the tender.

    The naming convention is ``{tender_id}_v{version}``.
    Falls back to the demo rulebook if no match is found.
    """
    tender_id = getattr(tender, "tender_id", "TENDER-2026-IT-001")
    version = getattr(tender, "rulebook_version", "v1.0")

    # Normalise version: "v1.0" → "1"
    version_num = version.lstrip("v").split(".")[0] if version else "1"

    rulebook_id = f"{tender_id}_v{version_num}"

    # Check if the rulebook file exists; fall back to demo
    from pathlib import Path
    rules_dir = Path(__file__).parent / "rules"
    if (rules_dir / f"{rulebook_id}.yaml").is_file():
        return rulebook_id

    # Fall back to the demo rulebook
    return "TENDER-2026-IT-001_v1"


# ---------------------------------------------------------------------------
# Pydantic → DB: persist assessment results
# ---------------------------------------------------------------------------

def persist_compliance_assessment(
    assessment: ComplianceAssessment,
    bid_id: str,
    db: "Session",
) -> Any:
    """
    Convert a ``ComplianceAssessment`` into DB model rows and persist them.

    This function imports ``app.models.entities`` at call time to avoid
    making the compliance engine depend on the database at import time.

    Args:
        assessment: The compliance engine's output.
        bid_id: The bid identifier to associate rows with.
        db: An active SQLAlchemy session.

    Returns:
        The persisted ``Assessment`` DB row.
    """
    # Late import to keep the compliance module independently testable.
    from app.models.entities import (  # type: ignore[import-untyped]
        Assessment as AssessmentModel,
        Finding as FindingModel,
        RuleResult as RuleResultModel,
    )

    # --- Persist Findings ---
    for finding in assessment.findings:
        db.add(FindingModel(
            bid_id=bid_id,
            finding_type=finding.type,
            severity=finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity),
            message=finding.message,
            evidence_reference=(
                finding.source
                or (finding.evidence.get("source_id") if finding.evidence else None)
                or finding.rule_id
            ),
        ))

    # --- Persist Rule Results ---
    for rule_result in assessment.rule_results:
        db.add(RuleResultModel(
            bid_id=bid_id,
            rule_id=rule_result.rule_id,
            rule_name=rule_result.rule_name,
            clause=rule_result.tender_clause,
            status=rule_result.result.value if hasattr(rule_result.result, "value") else str(rule_result.result),
            details=rule_result.message,
            is_mandatory=(rule_result.priority.value == "mandatory"),
        ))

    # --- Persist Assessment ---
    # Build score_breakdown in the format the API contract expects
    api_breakdown = []
    for bd in assessment.score_breakdown:
        cat_name = bd.category.value if hasattr(bd.category, "value") else str(bd.category)
        api_breakdown.append({
            "category": cat_name,
            "weight": bd.weight,
            "fulfilled": bd.fulfilled,
            "rulesPassed": bd.rules_passed,
            "rulesTotal": bd.rules_total,
        })

    # Calculate verification coverage from the input data's verification results
    verification_coverage = assessment.verification_coverage

    assessment_row = AssessmentModel(
        bid_id=bid_id,
        compliance_score=assessment.compliance_score,
        verification_coverage=verification_coverage,
        risk_level=assessment.risk_level.value if hasattr(assessment.risk_level, "value") else str(assessment.risk_level),
        recommendation=assessment.recommendation,
        recommendation_summary=assessment.recommendation_summary,
        has_mandatory_failure=assessment.has_mandatory_failure,
        score_breakdown=api_breakdown,
        evaluated_at=assessment.evaluated_at,
    )
    db.add(assessment_row)
    db.flush()

    return assessment_row
