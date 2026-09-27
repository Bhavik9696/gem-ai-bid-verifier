from typing import Any, Optional
from pydantic import BaseModel, Field


# --- Health ---
class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "complianceos-core-api"
    port: int = 8000
    version: str = "1.0.0"


# --- Tender Schemas ---
class TenderSummary(BaseModel):
    tenderId: str
    title: str
    referenceNumber: str
    category: str
    buyerOrganisation: str
    publishedDate: Optional[str] = None
    bidClosingDate: Optional[str] = None
    estimatedValue: Optional[float] = None
    currency: str = "INR"
    status: str = "ACTIVE"


class TenderDetail(TenderSummary):
    eligibilityConditions: dict[str, Any] = Field(default_factory=dict)
    mandatoryDocuments: list[str] = Field(default_factory=list)
    rulebookVersion: str = "v1.0"


# --- Bidder Schemas ---
class BidderResponse(BaseModel):
    bidderId: str
    legalName: str
    tradeName: Optional[str] = None
    pan: str
    gstin: Optional[str] = None
    udyamNumber: Optional[str] = None
    cin: Optional[str] = None
    authorisedSignatory: Optional[str] = None
    registeredAddress: Optional[str] = None
    category: str = "MSME"
    scenario: Optional[str] = None


# --- Document Schemas ---
class DocumentResponse(BaseModel):
    docId: str
    docType: str
    filename: str
    fileHash: Optional[str] = None
    status: str = "UPLOADED"


# --- Bid Schemas ---
class BidSummary(BaseModel):
    bidId: str
    tenderId: str
    bidderId: str
    bidderName: str
    submittedAt: Optional[str] = None
    bidAmount: float
    currency: str = "INR"
    status: str = "SUBMITTED"
    complianceScore: Optional[float] = None
    riskLevel: Optional[str] = None
    recommendation: Optional[str] = None


class BidDetail(BidSummary):
    bidder: BidderResponse
    documents: list[DocumentResponse] = Field(default_factory=list)
    notes: Optional[str] = None


# --- Verification Sub-Schemas ---
class ExtractedFactResponse(BaseModel):
    id: str
    field: str
    value: Optional[str] = None
    confidence: float
    documentId: Optional[str] = None
    page: int = 1
    evidence: Optional[str] = None


class VerificationResultResponse(BaseModel):
    id: str
    source: str
    mode: str = "DEMO"
    identifier: str
    status: str
    verifiedFacts: dict[str, Any] = Field(default_factory=dict)
    evidenceReference: Optional[str] = None
    checkedAt: str


class FindingResponse(BaseModel):
    id: str
    findingType: str
    severity: str
    message: str
    evidenceReference: Optional[str] = None


class RuleResultResponse(BaseModel):
    id: str
    ruleId: str
    ruleName: str
    clause: Optional[str] = None
    status: str
    details: Optional[str] = None
    isMandatory: bool = True


class AuditEventResponse(BaseModel):
    id: str
    bidId: str
    eventType: str
    actor: str
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: str


# --- Core Assessment Response ---
class AssessmentResponse(BaseModel):
    bidId: str
    complianceScore: float
    verificationCoverage: float
    riskLevel: str
    recommendation: str
    recommendationSummary: Optional[str] = None
    hasMandatoryFailure: bool = False
    scoreBreakdown: list[dict[str, Any]] = Field(default_factory=list)
    evaluatedAt: str
    ruleResults: list[RuleResultResponse] = Field(default_factory=list)
    findings: list[FindingResponse] = Field(default_factory=list)
    verificationResults: list[VerificationResultResponse] = Field(default_factory=list)
    extractedFacts: list[ExtractedFactResponse] = Field(default_factory=list)
    auditEvents: list[AuditEventResponse] = Field(default_factory=list)


# --- Decision Schemas ---
class DecisionRequest(BaseModel):
    decision: str = Field(..., description="CONFIRM | REQUEST_CLARIFICATION | OVERRIDE")
    reason: Optional[str] = Field(None, description="Mandatory when overriding or requesting clarification")
    notes: Optional[str] = None
    officerId: str = Field(default="OFFICER-001")


class DecisionResponse(BaseModel):
    id: str
    bidId: str
    officerId: str
    decision: str
    reason: Optional[str] = None
    notes: Optional[str] = None
    decidedAt: str
    bidStatus: str
