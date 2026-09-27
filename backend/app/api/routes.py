from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import (
    Tender,
    Bidder,
    Bid,
    Document,
    ExtractedFact,
    VerificationResult,
    Finding,
    RuleResult,
    Assessment,
    OfficerDecision,
    AuditEvent,
)
from app.services.orchestration.orchestrator import VerificationOrchestrator
from app.api.schemas import (
    HealthResponse,
    TenderSummary,
    TenderDetail,
    BidSummary,
    BidDetail,
    BidderResponse,
    DocumentResponse,
    AssessmentResponse,
    ExtractedFactResponse,
    VerificationResultResponse,
    FindingResponse,
    RuleResultResponse,
    AuditEventResponse,
    DecisionRequest,
    DecisionResponse,
)

router = APIRouter()
orchestrator = VerificationOrchestrator()


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


# --- Health Check ---
@router.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    return HealthResponse()


# --- Tenders ---
@router.get("/api/tenders", response_model=list[TenderSummary], tags=["Tenders"])
def list_tenders(db: Session = Depends(get_db)):
    tenders = db.query(Tender).all()
    return [
        TenderSummary(
            tenderId=t.tender_id,
            title=t.title,
            referenceNumber=t.reference_number,
            category=t.category,
            buyerOrganisation=t.buyer_organisation,
            publishedDate=t.published_date,
            bidClosingDate=t.bid_closing_date,
            estimatedValue=t.estimated_value,
            currency=t.currency or "INR",
            status=t.status or "ACTIVE",
        )
        for t in tenders
    ]


@router.get("/api/tenders/{tender_id}", response_model=TenderDetail, tags=["Tenders"])
def get_tender(tender_id: str, db: Session = Depends(get_db)):
    t = db.query(Tender).filter(Tender.tender_id == tender_id).first()
    if not t:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tender with ID '{tender_id}' not found.",
        )
    return TenderDetail(
        tenderId=t.tender_id,
        title=t.title,
        referenceNumber=t.reference_number,
        category=t.category,
        buyerOrganisation=t.buyer_organisation,
        publishedDate=t.published_date,
        bidClosingDate=t.bid_closing_date,
        estimatedValue=t.estimated_value,
        currency=t.currency or "INR",
        status=t.status or "ACTIVE",
        eligibilityConditions=t.eligibility_conditions or {},
        mandatoryDocuments=t.mandatory_documents or [],
        rulebookVersion=t.rulebook_version or "v1.0",
    )


@router.get("/api/tenders/{tender_id}/bids", response_model=list[BidSummary], tags=["Bids"])
def list_tender_bids(tender_id: str, db: Session = Depends(get_db)):
    t = db.query(Tender).filter(Tender.tender_id == tender_id).first()
    if not t:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tender with ID '{tender_id}' not found.",
        )

    bids = db.query(Bid).filter(Bid.tender_id == tender_id).all()
    summaries = []
    for b in bids:
        bidder = db.query(Bidder).filter(Bidder.bidder_id == b.bidder_id).first()
        assessment = db.query(Assessment).filter(Assessment.bid_id == b.bid_id).first()
        summaries.append(
            BidSummary(
                bidId=b.bid_id,
                tenderId=b.tender_id,
                bidderId=b.bidder_id,
                bidderName=bidder.legal_name if bidder else "Unknown",
                submittedAt=b.submitted_at,
                bidAmount=b.bid_amount,
                currency=b.currency or "INR",
                status=b.status or "SUBMITTED",
                complianceScore=assessment.compliance_score if assessment else None,
                riskLevel=assessment.risk_level if assessment else None,
                recommendation=assessment.recommendation if assessment else None,
            )
        )
    return summaries


# --- Verification Orchestration ---
@router.post(
    "/api/bids/{bid_id}/run-verification",
    response_model=AssessmentResponse,
    tags=["Verification"],
)
async def run_bid_verification(bid_id: str, db: Session = Depends(get_db)):
    bid = db.query(Bid).filter(Bid.bid_id == bid_id).first()
    if not bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bid with ID '{bid_id}' not found.",
        )

    try:
        await orchestrator.run_verification(bid_id=bid_id, db=db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {exc}",
        )

    return get_bid_assessment(bid_id=bid_id, db=db)


# --- Assessment ---
@router.get(
    "/api/bids/{bid_id}/assessment",
    response_model=AssessmentResponse,
    tags=["Assessment"],
)
def get_bid_assessment(bid_id: str, db: Session = Depends(get_db)):
    bid = db.query(Bid).filter(Bid.bid_id == bid_id).first()
    if not bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bid with ID '{bid_id}' not found.",
        )

    assessment = db.query(Assessment).filter(Assessment.bid_id == bid_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No verification assessment has been performed yet for bid '{bid_id}'. Run POST /api/bids/{bid_id}/run-verification first.",
        )

    rule_results = db.query(RuleResult).filter(RuleResult.bid_id == bid_id).all()
    findings = db.query(Finding).filter(Finding.bid_id == bid_id).all()
    verifications = db.query(VerificationResult).filter(VerificationResult.bid_id == bid_id).all()
    extracted_facts = db.query(ExtractedFact).filter(ExtractedFact.bid_id == bid_id).all()
    audit_events = (
        db.query(AuditEvent)
        .filter(AuditEvent.bid_id == bid_id)
        .order_by(AuditEvent.timestamp.asc())
        .all()
    )

    return AssessmentResponse(
        bidId=assessment.bid_id,
        complianceScore=assessment.compliance_score,
        verificationCoverage=assessment.verification_coverage,
        riskLevel=assessment.risk_level,
        recommendation=assessment.recommendation,
        recommendationSummary=assessment.recommendation_summary,
        hasMandatoryFailure=assessment.has_mandatory_failure,
        scoreBreakdown=assessment.score_breakdown or [],
        evaluatedAt=assessment.evaluated_at,
        ruleResults=[
            RuleResultResponse(
                id=r.id,
                ruleId=r.rule_id,
                ruleName=r.rule_name,
                clause=r.clause,
                status=r.status,
                details=r.details,
                isMandatory=r.is_mandatory,
            )
            for r in rule_results
        ],
        findings=[
            FindingResponse(
                id=f.id,
                findingType=f.finding_type,
                severity=f.severity,
                message=f.message,
                evidenceReference=f.evidence_reference,
            )
            for f in findings
        ],
        verificationResults=[
            VerificationResultResponse(
                id=v.id,
                source=v.source,
                mode=v.mode or "DEMO",
                identifier=v.identifier,
                status=v.status,
                verifiedFacts=v.verified_facts or {},
                evidenceReference=v.evidence_reference,
                checkedAt=v.checked_at,
            )
            for v in verifications
        ],
        extractedFacts=[
            ExtractedFactResponse(
                id=ef.id,
                field=ef.field,
                value=ef.value,
                confidence=ef.confidence,
                documentId=ef.document_id,
                page=ef.page,
                evidence=ef.evidence,
            )
            for ef in extracted_facts
        ],
        auditEvents=[
            AuditEventResponse(
                id=ae.id,
                bidId=ae.bid_id,
                eventType=ae.event_type,
                actor=ae.actor,
                details=ae.details or {},
                timestamp=ae.timestamp,
            )
            for ae in audit_events
        ],
    )


# --- Officer Decision ---
@router.post(
    "/api/bids/{bid_id}/decision",
    response_model=DecisionResponse,
    tags=["Decision"],
)
def record_officer_decision(
    bid_id: str,
    payload: DecisionRequest,
    db: Session = Depends(get_db),
):
    bid = db.query(Bid).filter(Bid.bid_id == bid_id).first()
    if not bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bid with ID '{bid_id}' not found.",
        )

    valid_decisions = ("CONFIRM", "REQUEST_CLARIFICATION", "OVERRIDE")
    norm_decision = payload.decision.upper().strip()
    if norm_decision not in valid_decisions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid decision '{payload.decision}'. Must be one of {valid_decisions}",
        )

    if norm_decision in ("OVERRIDE", "REQUEST_CLARIFICATION") and not payload.reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A reason is mandatory when choosing '{norm_decision}'.",
        )

    # Persist decision
    decision_record = OfficerDecision(
        bid_id=bid.bid_id,
        officer_id=payload.officerId,
        decision=norm_decision,
        reason=payload.reason,
        notes=payload.notes,
        decided_at=utc_now_iso(),
    )
    db.add(decision_record)

    # Update bid status
    if norm_decision == "CONFIRM":
        bid.status = "CONFIRMED"
    elif norm_decision == "REQUEST_CLARIFICATION":
        bid.status = "CLARIFICATION_REQUESTED"
    elif norm_decision == "OVERRIDE":
        bid.status = "OVERRIDDEN"

    # Append Audit Event
    audit = AuditEvent(
        bid_id=bid.bid_id,
        event_type="OFFICER_DECISION_RECORDED",
        actor=payload.officerId,
        details={
            "decision": norm_decision,
            "reason": payload.reason,
            "notes": payload.notes,
            "newBidStatus": bid.status,
        },
        timestamp=utc_now_iso(),
    )
    db.add(audit)

    db.commit()
    db.refresh(decision_record)

    return DecisionResponse(
        id=decision_record.id,
        bidId=decision_record.bid_id,
        officerId=decision_record.officer_id,
        decision=decision_record.decision,
        reason=decision_record.reason,
        notes=decision_record.notes,
        decidedAt=decision_record.decided_at,
        bidStatus=bid.status,
    )


# --- Audit Events ---
@router.get(
    "/api/bids/{bid_id}/audit-events",
    response_model=list[AuditEventResponse],
    tags=["Audit"],
)
def get_bid_audit_events(bid_id: str, db: Session = Depends(get_db)):
    bid = db.query(Bid).filter(Bid.bid_id == bid_id).first()
    if not bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bid with ID '{bid_id}' not found.",
        )

    events = (
        db.query(AuditEvent)
        .filter(AuditEvent.bid_id == bid_id)
        .order_by(AuditEvent.timestamp.asc())
        .all()
    )
    return [
        AuditEventResponse(
            id=e.id,
            bidId=e.bid_id,
            eventType=e.event_type,
            actor=e.actor,
            details=e.details or {},
            timestamp=e.timestamp,
        )
        for e in events
    ]
