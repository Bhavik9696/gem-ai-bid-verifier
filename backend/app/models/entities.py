from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


class Tender(Base):
    __tablename__ = "tenders"

    tender_id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    reference_number = Column(String(128), nullable=False, unique=True)
    category = Column(String(128), nullable=False)
    buyer_organisation = Column(String(255), nullable=False)
    published_date = Column(String(32), nullable=True)
    bid_closing_date = Column(String(32), nullable=True)
    estimated_value = Column(Float, nullable=True)
    currency = Column(String(16), default="INR")
    eligibility_conditions = Column(JSON, default=dict)
    mandatory_documents = Column(JSON, default=list)
    rulebook_version = Column(String(32), default="v1.0")
    status = Column(String(32), default="ACTIVE")
    created_at = Column(String(64), default=utc_now_iso)

    bids = relationship("Bid", back_populates="tender", cascade="all, delete-orphan")


class Bidder(Base):
    __tablename__ = "bidders"

    bidder_id = Column(String(64), primary_key=True, index=True)
    legal_name = Column(String(255), nullable=False)
    trade_name = Column(String(255), nullable=True)
    pan = Column(String(16), nullable=False, index=True)
    gstin = Column(String(20), nullable=True, index=True)
    udyam_number = Column(String(64), nullable=True)
    cin = Column(String(64), nullable=True)
    authorised_signatory = Column(String(128), nullable=True)
    registered_address = Column(Text, nullable=True)
    category = Column(String(64), default="MSME")
    scenario = Column(String(64), nullable=True)
    created_at = Column(String(64), default=utc_now_iso)

    bids = relationship("Bid", back_populates="bidder", cascade="all, delete-orphan")


class Bid(Base):
    __tablename__ = "bids"

    bid_id = Column(String(64), primary_key=True, index=True)
    tender_id = Column(String(64), ForeignKey("tenders.tender_id"), nullable=False, index=True)
    bidder_id = Column(String(64), ForeignKey("bidders.bidder_id"), nullable=False, index=True)
    submitted_at = Column(String(64), nullable=True)
    bid_amount = Column(Float, nullable=False)
    currency = Column(String(16), default="INR")
    status = Column(String(64), default="SUBMITTED")  # SUBMITTED, VERIFIED, FLAGGED, CONFIRMED, etc.
    notes = Column(Text, nullable=True)
    created_at = Column(String(64), default=utc_now_iso)

    tender = relationship("Tender", back_populates="bids")
    bidder = relationship("Bidder", back_populates="bids")
    documents = relationship("Document", back_populates="bid", cascade="all, delete-orphan")
    extracted_facts = relationship("ExtractedFact", back_populates="bid", cascade="all, delete-orphan")
    verification_results = relationship("VerificationResult", back_populates="bid", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="bid", cascade="all, delete-orphan")
    rule_results = relationship("RuleResult", back_populates="bid", cascade="all, delete-orphan")
    assessment = relationship("Assessment", uselist=False, back_populates="bid", cascade="all, delete-orphan")
    decisions = relationship("OfficerDecision", back_populates="bid", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="bid", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    doc_id = Column(String(64), nullable=False, index=True)
    bid_id = Column(String(64), ForeignKey("bids.bid_id"), nullable=False, index=True)
    doc_type = Column(String(64), nullable=False)
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(128), nullable=True)
    status = Column(String(32), default="UPLOADED")
    created_at = Column(String(64), default=utc_now_iso)

    bid = relationship("Bid", back_populates="documents")


class ExtractedFact(Base):
    __tablename__ = "extracted_facts"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    bid_id = Column(String(64), ForeignKey("bids.bid_id"), nullable=False, index=True)
    document_id = Column(String(64), nullable=True)
    field = Column(String(64), nullable=False)  # pan, gstin, udyamNumber, legalName, etc.
    value = Column(String(255), nullable=True)
    confidence = Column(Float, default=1.0)
    page = Column(Integer, default=1)
    evidence = Column(Text, nullable=True)
    created_at = Column(String(64), default=utc_now_iso)

    bid = relationship("Bid", back_populates="extracted_facts")


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    bid_id = Column(String(64), ForeignKey("bids.bid_id"), nullable=False, index=True)
    source = Column(String(64), nullable=False)  # GST_DEMO, PAN_DEMO, etc.
    mode = Column(String(32), default="DEMO")  # Always DEMO in prototype
    identifier = Column(String(128), nullable=False)
    status = Column(String(64), nullable=False)  # VERIFIED, NOT_FOUND, MISMATCH, EXPIRED, etc.
    verified_facts = Column(JSON, default=dict)
    evidence_reference = Column(String(255), nullable=True)
    checked_at = Column(String(64), default=utc_now_iso)

    bid = relationship("Bid", back_populates="verification_results")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    bid_id = Column(String(64), ForeignKey("bids.bid_id"), nullable=False, index=True)
    finding_type = Column(String(128), nullable=False)  # ENTITY_NAME_MISMATCH, EXPIRED_OEM_AUTHORISATION, etc.
    severity = Column(String(32), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    message = Column(Text, nullable=False)
    evidence_reference = Column(String(255), nullable=True)
    created_at = Column(String(64), default=utc_now_iso)

    bid = relationship("Bid", back_populates="findings")


class RuleResult(Base):
    __tablename__ = "rule_results"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    bid_id = Column(String(64), ForeignKey("bids.bid_id"), nullable=False, index=True)
    rule_id = Column(String(64), nullable=False)
    rule_name = Column(String(128), nullable=False)
    clause = Column(String(128), nullable=True)
    status = Column(String(32), nullable=False)  # PASS, FAIL, NEEDS_CLARIFICATION, etc.
    details = Column(Text, nullable=True)
    is_mandatory = Column(Boolean, default=True)
    evaluated_at = Column(String(64), default=utc_now_iso)

    bid = relationship("Bid", back_populates="rule_results")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    bid_id = Column(String(64), ForeignKey("bids.bid_id"), nullable=False, unique=True, index=True)
    compliance_score = Column(Float, nullable=False, default=0.0)
    verification_coverage = Column(Float, nullable=False, default=0.0)
    risk_level = Column(String(32), nullable=False, default="LOW")  # LOW, MEDIUM, HIGH
    recommendation = Column(String(128), nullable=False)
    recommendation_summary = Column(Text, nullable=True)
    has_mandatory_failure = Column(Boolean, default=False)
    score_breakdown = Column(JSON, default=list)
    evaluated_at = Column(String(64), default=utc_now_iso)

    bid = relationship("Bid", back_populates="assessment")


class OfficerDecision(Base):
    __tablename__ = "officer_decisions"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    bid_id = Column(String(64), ForeignKey("bids.bid_id"), nullable=False, index=True)
    officer_id = Column(String(64), default="OFFICER-001")
    decision = Column(String(64), nullable=False)  # CONFIRM, REQUEST_CLARIFICATION, OVERRIDE
    reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    decided_at = Column(String(64), default=utc_now_iso)

    bid = relationship("Bid", back_populates="decisions")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    bid_id = Column(String(64), ForeignKey("bids.bid_id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)  # VERIFICATION_RUN, DECISION_RECORDED, etc.
    actor = Column(String(64), default="SYSTEM")
    details = Column(JSON, default=dict)
    timestamp = Column(String(64), default=utc_now_iso)

    bid = relationship("Bid", back_populates="audit_events")
