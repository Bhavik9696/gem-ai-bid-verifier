"""
Compliance Engine — Pydantic Schemas

All data models used by the compliance engine module. These define both
the input contract (what the orchestrator passes in) and the output
contract (what the engine returns).

Input models consume data from:
  - Member 4 (Document Intelligence) → ExtractedFact
  - Member 6 (Demo Connectors) → VerificationResult
  - Member 3 (Core API / Orchestration) → BidderProfile, TenderContext

Output models are consumed by:
  - Member 3 (Core API) → persists and forwards to the dashboard
  - Member 2 (Frontend) → renders in the officer dashboard
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class MatchType(str, Enum):
    """How a bid value compared against a source value."""
    EXACT = "EXACT"
    NORMALISED_MATCH = "NORMALISED_MATCH"
    MISMATCH = "MISMATCH"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class Severity(str, Enum):
    """Finding / rule-failure severity levels."""
    BLOCKER = "BLOCKER"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class RuleResultStatus(str, Enum):
    """Possible outcomes when a tender rule is evaluated."""
    PASS = "PASS"
    FAIL = "FAIL"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RulePriority(str, Enum):
    """Rule importance classification within a tender rulebook."""
    MANDATORY = "mandatory"
    RECOMMENDED = "recommended"
    INFORMATIONAL = "informational"


class RiskLevel(str, Enum):
    """Officer-facing risk classification for review prioritisation."""
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RuleCategory(str, Enum):
    """Scoring categories for weighted compliance calculation."""
    MANDATORY_ELIGIBILITY = "mandatory_eligibility"
    STATUTORY_COMPLIANCE = "statutory_compliance"
    DOCUMENTATION = "documentation"


# ---------------------------------------------------------------------------
# Allowed recommendation strings (exact values only)
# ---------------------------------------------------------------------------

RECOMMENDATION_COMPLIANT = "Compliant — Ready for Officer Confirmation"
RECOMMENDATION_CLARIFICATION = "Needs Clarification — Missing or Unverified Evidence"
RECOMMENDATION_HIGH_RISK = "High-Risk — Officer Review Required"

ALLOWED_RECOMMENDATIONS = frozenset([
    RECOMMENDATION_COMPLIANT,
    RECOMMENDATION_CLARIFICATION,
    RECOMMENDATION_HIGH_RISK,
])


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------

class ExtractedFact(BaseModel):
    """
    A single fact extracted from a bidder's uploaded document.
    Produced by the Document Intelligence service (Member 4).
    """
    field: str = Field(
        ...,
        description="Normalised field name, e.g. 'gstin', 'pan', 'legalName'",
    )
    value: str | None = Field(
        default=None,
        description="Extracted value, or None if the field was expected but not found",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Extraction confidence score (0.0 = no confidence, 1.0 = certain)",
    )
    document_id: str = Field(
        ...,
        description="ID of the source document from which this fact was extracted",
    )
    page: int | None = Field(
        default=None,
        description="Page number in the source document (1-indexed)",
    )
    document_type: str | None = Field(
        default=None,
        description="Classified document type, e.g. 'GST_CERTIFICATE', 'PAN_CARD'",
    )


class VerificationResult(BaseModel):
    """
    Response from a source connector (Member 6) after verifying an identifier.
    Every prototype result must have mode='DEMO'.
    """
    source: str = Field(
        ...,
        description="Connector source identifier, e.g. 'GST_DEMO', 'PAN_DEMO'",
    )
    mode: str = Field(
        default="DEMO",
        description="Connector mode — always 'DEMO' for the prototype",
    )
    identifier: str = Field(
        ...,
        description="The identifier that was verified (GSTIN, PAN, etc.)",
    )
    status: str = Field(
        ...,
        description="Verification outcome: 'VERIFIED', 'NOT_FOUND', 'ERROR'",
    )
    verified_facts: dict[str, Any] = Field(
        default_factory=dict,
        description="Source-specific key-value facts returned by the connector",
    )
    checked_at: str = Field(
        ...,
        description="ISO 8601 timestamp of when the verification was performed",
    )
    evidence_reference: str | None = Field(
        default=None,
        description="Human-readable reference to the verification source",
    )


class BidderProfile(BaseModel):
    """
    Core identity fields for a bidder, sourced from the GeM-style
    bid/bidder import (Member 3).
    """
    bidder_id: str
    legal_name: str
    pan: str | None = None
    gstin: str | None = None
    udyam_number: str | None = None
    cin: str | None = None
    authorised_signatory: str | None = None


class TenderContext(BaseModel):
    """
    Tender metadata relevant to compliance evaluation.
    Sourced from the tender import / seed data (Member 3).
    """
    tender_id: str
    title: str
    closing_date: str = Field(
        ...,
        description="ISO date (YYYY-MM-DD) — the tender bid closing date",
    )
    category: str | None = None
    rulebook_id: str = Field(
        ...,
        description="Identifies which YAML rule file to load, e.g. 'TENDER-2026-IT-001_v1'",
    )
    make_in_india_required: bool = False
    local_content_threshold: float | None = Field(
        default=None,
        description="Minimum local-content percentage (0–100) when Make in India applies",
    )
    msme_mandatory: bool = False
    oem_required: bool = Field(
        default=False,
        description="True if tender requires OEM authorisation from the bidder",
    )

    mandatory_documents: list[str] = Field(
        default_factory=list,
        description=(
            "List of document types that are mandatory for this tender, "
            "e.g. ['GST_CERTIFICATE', 'PAN_CARD', 'UDYAM_CERTIFICATE']"
        ),
    )


class BidComplianceInput(BaseModel):
    """
    The single input bundle that the orchestrator (Member 3) passes
    to the compliance engine's evaluate_bid_compliance() function.
    Contains everything needed to produce a ComplianceAssessment.
    """
    bid_id: str
    tender: TenderContext
    bidder: BidderProfile
    extracted_facts: list[ExtractedFact] = Field(default_factory=list)
    verification_results: list[VerificationResult] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Evidence provenance models
# ---------------------------------------------------------------------------

class ExtractedObservation(BaseModel):
    """
    A single document-extracted observation for an identity field.
    Preserves full provenance: value, confidence, document, and page.
    Multiple observations may exist for the same field across different
    documents or within the same document.
    """
    value: str | None = Field(
        default=None,
        description="Extracted value, or None if field was expected but not found",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Extraction confidence score",
    )
    document_id: str = Field(
        ...,
        description="ID of the source document",
    )
    page: int | None = Field(
        default=None,
        description="Page number (1-indexed)",
    )
    document_type: str | None = Field(
        default=None,
        description="Classified document type, e.g. 'PAN_CARD'",
    )


class VerificationObservation(BaseModel):
    """
    A single source-verified observation for an identity field.
    Preserves the full connector response provenance including status,
    verified facts, timestamp, and evidence reference.
    Multiple observations from the same source are preserved when they
    exist (e.g. different identifiers queried against the same connector).
    """
    source: str = Field(
        ...,
        description="Connector source identifier, e.g. 'PAN_DEMO'",
    )
    identifier: str = Field(
        ...,
        description="The identifier that was sent to the connector",
    )
    status: str = Field(
        ...,
        description="Verification outcome: 'VERIFIED', 'NOT_FOUND', 'ERROR'",
    )
    value: str | None = Field(
        default=None,
        description="The specific field value extracted from verified_facts",
    )
    verified_facts: dict[str, Any] = Field(
        default_factory=dict,
        description="Complete verified_facts payload from the connector",
    )
    checked_at: str | None = Field(
        default=None,
        description="ISO 8601 timestamp of when verification was performed",
    )
    evidence_reference: str | None = Field(
        default=None,
        description="Human-readable reference to the verification source",
    )


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------

class MatchResult(BaseModel):
    """
    Result of comparing one identity field between bid/document data
    and a source-verified value.
    """
    field: str = Field(
        ...,
        description="The identity field compared, e.g. 'pan', 'gstin', 'legalName'",
    )
    bid_value: str | None = Field(
        default=None,
        description="Value from the bidder profile or extracted document",
    )
    source_value: str | None = Field(
        default=None,
        description="Value returned by the source connector",
    )
    source: str = Field(
        ...,
        description="Which connector provided the source value",
    )
    match_type: MatchType = Field(
        ...,
        description="Classification of the comparison result",
    )
    is_confirmed: bool = Field(
        ...,
        description="True if identity is positively established; False if flagged for review",
    )
    notes: str | None = Field(
        default=None,
        description="Additional context about the comparison (e.g. similarity score)",
    )

    # --- Evidence provenance (backward-compatible, optional) ---
    extracted_observations: list[ExtractedObservation] = Field(
        default_factory=list,
        description=(
            "All document-extracted observations for this field. "
            "Preserves every observation including lower-confidence values."
        ),
    )

    verification_observations: list[VerificationObservation] = Field(
        default_factory=list,
        description=(
            "All source-verified observations relevant to this field and source. "
            "Preserves status, verified_facts, timestamps, and evidence references."
        ),
    )

class Finding(BaseModel):
    """
    A conflict, discrepancy, or notable observation detected during
    compliance evaluation. Every failed/flagged item must include
    enough context for an officer to understand and act.
    """
    finding_id: str = Field(
        ...,
        description="Unique identifier for this finding (UUID)",
    )
    type: str = Field(
        ...,
        description="Finding type code, e.g. 'ENTITY_NAME_MISMATCH', 'GST_INACTIVE'",
    )
    severity: Severity = Field(
        ...,
        description="How severe this finding is for compliance",
    )
    message: str = Field(
        ...,
        description="Human-readable explanation of the conflict or issue",
    )
    rule_id: str | None = Field(
        default=None,
        description="The tender rule ID that detected or relates to this finding",
    )
    tender_clause: str | None = Field(
        default=None,
        description="Tender clause reference, e.g. 'Clause 4.2, Page 7'",
    )
    source: str | None = Field(
        default=None,
        description="Which connector or data source is involved",
    )
    evidence: dict[str, Any] | None = Field(
        default=None,
        description="Structured evidence: documentId, page, extractedValue, sourceValue, etc.",
    )


class RuleResult(BaseModel):
    """
    The outcome of evaluating a single tender rule against bid data.
    """
    rule_id: str
    rule_name: str
    result: RuleResultStatus
    priority: RulePriority
    category: RuleCategory = Field(
        default=RuleCategory.MANDATORY_ELIGIBILITY,
        description="Scoring category this rule belongs to",
    )
    tender_clause: str | None = None
    message: str = Field(
        ...,
        description="Human-readable explanation of the rule result",
    )
    evidence: dict[str, Any] | None = Field(
        default=None,
        description="Supporting data: extracted values, source values, dates compared, etc.",
    )
    severity: Severity | None = Field(
        default=None,
        description="Only set when result is FAIL — indicates failure severity",
    )


class ScoreBreakdown(BaseModel):
    """
    Per-category breakdown of the compliance score, making the overall
    score explainable to the officer.
    """
    category: RuleCategory
    weight: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Category weight in the overall compliance score",
    )
    fulfilled: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Proportion of applicable rules in this category that passed (0.0–1.0)",
    )
    rules_passed: int = Field(
        ...,
        ge=0,
        description="Number of rules that passed in this category",
    )
    rules_total: int = Field(
        ...,
        ge=0,
        description="Total applicable rules in this category (excludes NOT_APPLICABLE)",
    )
    details: list[str] = Field(
        default_factory=list,
        description="Brief notes about each rule result in this category",
    )


class ComplianceAssessment(BaseModel):
    """
    The top-level output of the compliance engine.
    Returned to the orchestrator (Member 3), which persists it and
    forwards it to the frontend (Member 2) via GET /api/bids/{bidId}/assessment.
    """
    bid_id: str
    bidder_id: str
    tender_id: str

    # Scores
    compliance_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Weighted compliance completion percentage (0–100)",
    )
    risk_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Review-priority risk score (0–100)",
    )
    risk_level: RiskLevel = Field(
        ...,
        description="Categorised risk level derived from risk_score",
    )

    # Recommendation
    recommendation: str = Field(
        ...,
        description="One of the three allowed recommendation strings",
    )
    recommendation_summary: str = Field(
        ...,
        description="1–2 sentence plain-language explanation for the officer",
    )

    # Detailed results
    match_results: list[MatchResult] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    rule_results: list[RuleResult] = Field(default_factory=list)
    score_breakdown: list[ScoreBreakdown] = Field(default_factory=list)

    # Flags
    has_mandatory_failure: bool = Field(
        ...,
        description="True if any mandatory rule has result=FAIL",
    )

    # Metadata
    evaluated_at: str = Field(
        ...,
        description="ISO 8601 timestamp of when evaluation was performed",
    )
