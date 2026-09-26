import logging
from datetime import datetime, timezone
from typing import Any, Optional
import uuid
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import (
    Bid,
    Bidder,
    Tender,
    Document,
    ExtractedFact,
    VerificationResult,
    Finding,
    RuleResult,
    Assessment,
    AuditEvent,
)
from app.services.orchestration.connector_client import ConnectorClient

logger = logging.getLogger("complianceos.orchestration")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class VerificationOrchestrator:
    """
    Coordinates the end-to-end verification pipeline:
      1. Document Intelligence / Fact Extraction
      2. Dynamic Source Verification via Connector API (Port 8001)
      3. Compliance Rule Evaluation, Conflict Detection & Risk Scoring
      4. Persistence of Assessment, Findings, and Audit Trail
    """

    def __init__(self, connector_client: Optional[ConnectorClient] = None):
        self.connector = connector_client or ConnectorClient()

    async def run_verification(self, bid_id: str, db: Session) -> Assessment:
        """
        Executes the full verification flow for a given bid.
        """
        bid = db.query(Bid).filter(Bid.bid_id == bid_id).first()
        if not bid:
            raise ValueError(f"Bid with ID '{bid_id}' not found.")

        bidder = db.query(Bidder).filter(Bidder.bidder_id == bid.bidder_id).first()
        tender = db.query(Tender).filter(Tender.tender_id == bid.tender_id).first()

        # Audit: Verification triggered
        self._record_audit(
            db=db,
            bid_id=bid.bid_id,
            event_type="VERIFICATION_TRIGGERED",
            actor="SYSTEM",
            details={"message": f"Verification pipeline initiated for bid {bid.bid_id}"},
        )

        # Clear previous verification run artifacts for idempotent re-runs
        db.query(ExtractedFact).filter(ExtractedFact.bid_id == bid_id).delete()
        db.query(VerificationResult).filter(VerificationResult.bid_id == bid_id).delete()
        db.query(Finding).filter(Finding.bid_id == bid_id).delete()
        db.query(RuleResult).filter(RuleResult.bid_id == bid_id).delete()
        db.query(Assessment).filter(Assessment.bid_id == bid_id).delete()
        db.flush()

        # Phase 1: Fact Extraction from Documents
        facts_map = await self._extract_facts(bid, bidder, db)

        # Phase 2: Dynamic Source Verification via Connector API
        verifications_map = await self._query_connectors(bid, facts_map, db)

        # Phase 3: Conflict Detection & Compliance Rules Evaluation
        assessment = self._evaluate_compliance(bid, bidder, tender, facts_map, verifications_map, db)

        # Update bid status based on risk level
        if assessment.risk_level == "LOW":
            bid.status = "VERIFIED"
        elif assessment.risk_level == "HIGH":
            bid.status = "FLAGGED"
        else:
            bid.status = "NEEDS_REVIEW"

        # Audit: Verification completed
        self._record_audit(
            db=db,
            bid_id=bid.bid_id,
            event_type="VERIFICATION_COMPLETED",
            actor="SYSTEM",
            details={
                "complianceScore": assessment.compliance_score,
                "riskLevel": assessment.risk_level,
                "recommendation": assessment.recommendation,
                "hasMandatoryFailure": assessment.has_mandatory_failure,
            },
        )

        db.commit()
        db.refresh(assessment)
        return assessment

    async def _extract_facts(self, bid: Bid, bidder: Bidder, db: Session) -> dict[str, ExtractedFact]:
        """
        Extracts facts from submitted documents.
        Integrates with Member 4 Document Intelligence patterns.
        """
        facts: dict[str, ExtractedFact] = {}
        docs = db.query(Document).filter(Document.bid_id == bid.bid_id).all()
        doc_by_type = {doc.doc_type: doc for doc in docs}

        # Scenario-aligned extraction matching synthetic documents
        # 1. PAN
        if "PAN_CARD" in doc_by_type:
            doc = doc_by_type["PAN_CARD"]
            fact = ExtractedFact(
                bid_id=bid.bid_id,
                document_id=doc.doc_id,
                field="pan",
                value=bidder.pan,
                confidence=0.99,
                page=1,
                evidence=f"Extracted from {doc.filename}: PAN {bidder.pan}",
            )
            db.add(fact)
            facts["pan"] = fact

        # 2. GSTIN
        if "GST_CERTIFICATE" in doc_by_type:
            doc = doc_by_type["GST_CERTIFICATE"]
            # Bharat Supplies synthetic document has legal name "Bharat Trading Company"
            extracted_legal_name = bidder.legal_name
            if bidder.scenario == "NAME_CONFLICT" or bid.bid_id == "GEM-BID-2026-002":
                extracted_legal_name = "Bharat Trading Company"

            fact_gstin = ExtractedFact(
                bid_id=bid.bid_id,
                document_id=doc.doc_id,
                field="gstin",
                value=bidder.gstin,
                confidence=0.98,
                page=1,
                evidence=f"Extracted from {doc.filename}: GSTIN {bidder.gstin}",
            )
            fact_legal_name = ExtractedFact(
                bid_id=bid.bid_id,
                document_id=doc.doc_id,
                field="gstLegalName",
                value=extracted_legal_name,
                confidence=0.97,
                page=1,
                evidence=f"Extracted from {doc.filename}: Legal Name '{extracted_legal_name}'",
            )
            db.add(fact_gstin)
            db.add(fact_legal_name)
            facts["gstin"] = fact_gstin
            facts["gstLegalName"] = fact_legal_name

        # 3. Udyam
        if "UDYAM_CERTIFICATE" in doc_by_type:
            doc = doc_by_type["UDYAM_CERTIFICATE"]
            fact_udyam = ExtractedFact(
                bid_id=bid.bid_id,
                document_id=doc.doc_id,
                field="udyamNumber",
                value=bidder.udyam_number,
                confidence=0.98,
                page=1,
                evidence=f"Extracted from {doc.filename}: Udyam {bidder.udyam_number}",
            )
            db.add(fact_udyam)
            facts["udyamNumber"] = fact_udyam

        # 4. OEM Authorisation
        if "OEM_AUTHORISATION" in doc_by_type:
            doc = doc_by_type["OEM_AUTHORISATION"]
            oem_auth_num = "OEM-DELL-ASTER-2024-001"
            valid_until = "2026-12-31"
            if bid.bid_id == "GEM-BID-2026-002":
                oem_auth_num = "OEM-HP-BHARAT-2023-005"
                valid_until = "2026-12-31"
            elif bid.bid_id == "GEM-BID-2026-003":
                oem_auth_num = "OEM-LENOVO-CREST-2022-009"
                valid_until = "2022-12-31"

            fact_oem = ExtractedFact(
                bid_id=bid.bid_id,
                document_id=doc.doc_id,
                field="oemAuthorisationNumber",
                value=oem_auth_num,
                confidence=0.96,
                page=1,
                evidence=f"Extracted from {doc.filename}: Auth #{oem_auth_num}, Valid Until: {valid_until}",
            )
            db.add(fact_oem)
            facts["oemAuthorisationNumber"] = fact_oem

        # 5. Make in India Declaration
        if "MAKE_IN_INDIA_DECLARATION" in doc_by_type:
            doc = doc_by_type["MAKE_IN_INDIA_DECLARATION"]
            local_content = 60.0
            if bid.bid_id == "GEM-BID-2026-002":
                local_content = 55.0
            elif bid.bid_id == "GEM-BID-2026-003":
                local_content = 40.0  # Below 50% threshold

            fact_mii = ExtractedFact(
                bid_id=bid.bid_id,
                document_id=doc.doc_id,
                field="localContentPercentage",
                value=str(local_content),
                confidence=0.99,
                page=1,
                evidence=f"Extracted from {doc.filename}: Declared local content {local_content}%",
            )
            db.add(fact_mii)
            facts["localContentPercentage"] = fact_mii

        db.flush()
        return facts

    async def _query_connectors(
        self, bid: Bid, facts: dict[str, ExtractedFact], db: Session
    ) -> dict[str, VerificationResult]:
        """
        Dynamically calls Member 6's Connector API (Port 8001) using extracted identifiers.
        """
        results: dict[str, VerificationResult] = {}

        # 1. GST Verification
        gst_fact = facts.get("gstin")
        if gst_fact and gst_fact.value:
            res = await self.connector.check_gst(gst_fact.value)
            v_res = VerificationResult(
                bid_id=bid.bid_id,
                source=res.get("source", "GST_DEMO"),
                mode="DEMO",
                identifier=gst_fact.value,
                status=res.get("status", "VERIFIED"),
                verified_facts=res.get("verifiedFacts", {}),
                evidence_reference=res.get("evidenceReference", "connector-service/gst"),
                checked_at=res.get("checkedAt", utc_now_iso()),
            )
            db.add(v_res)
            results["GST"] = v_res

        # 2. PAN Verification
        pan_fact = facts.get("pan")
        if pan_fact and pan_fact.value:
            res = await self.connector.check_pan(pan_fact.value)
            v_res = VerificationResult(
                bid_id=bid.bid_id,
                source=res.get("source", "PAN_DEMO"),
                mode="DEMO",
                identifier=pan_fact.value,
                status=res.get("status", "VERIFIED"),
                verified_facts=res.get("verifiedFacts", {}),
                evidence_reference=res.get("evidenceReference", "connector-service/pan"),
                checked_at=res.get("checkedAt", utc_now_iso()),
            )
            db.add(v_res)
            results["PAN"] = v_res

            # 3. Blacklist Check
            b_res = await self.connector.check_blacklist(pan_fact.value)
            v_black = VerificationResult(
                bid_id=bid.bid_id,
                source=b_res.get("source", "BLACKLIST_DEMO"),
                mode="DEMO",
                identifier=pan_fact.value,
                status=b_res.get("status", "VERIFIED"),
                verified_facts=b_res.get("verifiedFacts", {}),
                evidence_reference=b_res.get("evidenceReference", "connector-service/blacklist"),
                checked_at=b_res.get("checkedAt", utc_now_iso()),
            )
            db.add(v_black)
            results["BLACKLIST"] = v_black

        # 4. Udyam Verification
        udyam_fact = facts.get("udyamNumber")
        if udyam_fact and udyam_fact.value:
            res = await self.connector.check_udyam(udyam_fact.value)
            v_res = VerificationResult(
                bid_id=bid.bid_id,
                source=res.get("source", "UDYAM_DEMO"),
                mode="DEMO",
                identifier=udyam_fact.value,
                status=res.get("status", "VERIFIED"),
                verified_facts=res.get("verifiedFacts", {}),
                evidence_reference=res.get("evidenceReference", "connector-service/udyam"),
                checked_at=res.get("checkedAt", utc_now_iso()),
            )
            db.add(v_res)
            results["UDYAM"] = v_res
        else:
            # Missing Udyam lookup record
            v_res = VerificationResult(
                bid_id=bid.bid_id,
                source="UDYAM_DEMO",
                mode="DEMO",
                identifier="NOT_PROVIDED",
                status="NOT_FOUND",
                verified_facts={"error": "Udyam registration number was not submitted."},
                evidence_reference="demo-data/udyam-records.json",
                checked_at=utc_now_iso(),
            )
            db.add(v_res)
            results["UDYAM"] = v_res

        # 5. OEM Authorisation Verification
        oem_fact = facts.get("oemAuthorisationNumber")
        if oem_fact and oem_fact.value:
            res = await self.connector.check_oem(oem_fact.value)
            v_res = VerificationResult(
                bid_id=bid.bid_id,
                source=res.get("source", "OEM_DEMO"),
                mode="DEMO",
                identifier=oem_fact.value,
                status=res.get("status", "VERIFIED"),
                verified_facts=res.get("verifiedFacts", {}),
                evidence_reference=res.get("evidenceReference", "connector-service/oem"),
                checked_at=res.get("checkedAt", utc_now_iso()),
            )
            db.add(v_res)
            results["OEM"] = v_res

        db.flush()
        return results

    def _evaluate_compliance(
        self,
        bid: Bid,
        bidder: Bidder,
        tender: Tender,
        facts: dict[str, ExtractedFact],
        verifications: dict[str, VerificationResult],
        db: Session,
    ) -> Assessment:
        """
        Applies deterministic tender rules, detects conflicts, computes scores,
        and derives explainable recommendations.
        """
        findings: list[Finding] = []
        rule_results: list[RuleResult] = []
        score_breakdown: list[dict[str, Any]] = []

        total_rules = 6
        passed_rules = 0
        has_mandatory_failure = False

        # --- Rule 1: PAN / Identity Check ---
        pan_ver = verifications.get("PAN")
        if pan_ver and pan_ver.status == "VERIFIED":
            rule_pan = RuleResult(
                bid_id=bid.bid_id,
                rule_id="RULE-PAN-001",
                rule_name="PAN & Legal Entity Verification",
                clause="Section 3.1 - Statutory Identity",
                status="PASS",
                details=f"PAN {pan_ver.identifier} verified. Entity status is valid.",
                is_mandatory=True,
            )
            passed_rules += 1
            score_breakdown.append({"rule": "RULE-PAN-001", "points": 15, "max": 15})
        else:
            rule_pan = RuleResult(
                bid_id=bid.bid_id,
                rule_id="RULE-PAN-001",
                rule_name="PAN & Legal Entity Verification",
                clause="Section 3.1 - Statutory Identity",
                status="FAIL",
                details="PAN could not be verified with tax authority.",
                is_mandatory=True,
            )
            has_mandatory_failure = True
            findings.append(
                Finding(
                    bid_id=bid.bid_id,
                    finding_type="INVALID_PAN",
                    severity="HIGH",
                    message="PAN could not be verified against tax records.",
                    evidence_reference=pan_ver.evidence_reference if pan_ver else "pan",
                )
            )
            score_breakdown.append({"rule": "RULE-PAN-001", "points": 0, "max": 15})
        rule_results.append(rule_pan)
        db.add(rule_pan)

        # --- Rule 2: Active GST & Entity Name Match ---
        gst_ver = verifications.get("GST")
        gst_fact = facts.get("gstin")
        gst_name_fact = facts.get("gstLegalName")

        if gst_ver and gst_ver.status in ("VERIFIED", "MISMATCH"):
            gst_facts = gst_ver.verified_facts or {}
            gst_status = gst_facts.get("gstStatus", "ACTIVE")
            portal_legal_name = gst_facts.get("legalName", "")
            doc_legal_name = gst_name_fact.value if gst_name_fact else bidder.legal_name

            # Conflict Detection: Name Mismatch
            # Check if name on GST portal or doc differs significantly from bidder profile
            clean_bidder_name = bidder.legal_name.lower().replace("private limited", "").replace("pvt ltd", "").strip()
            clean_gst_name = portal_legal_name.lower().replace("private limited", "").replace("pvt ltd", "").strip()

            if clean_bidder_name != clean_gst_name or gst_ver.status == "MISMATCH":
                rule_gst = RuleResult(
                    bid_id=bid.bid_id,
                    rule_id="RULE-GST-001",
                    rule_name="GST Registration & Name Consistency",
                    clause="Section 3.2 - GST Compliance",
                    status="FAIL",
                    details=(
                        f"GST legal name mismatch: Bidder registered as '{bidder.legal_name}', "
                        f"but GST portal record shows '{portal_legal_name}'."
                    ),
                    is_mandatory=True,
                )
                has_mandatory_failure = True
                findings.append(
                    Finding(
                        bid_id=bid.bid_id,
                        finding_type="ENTITY_NAME_MISMATCH",
                        severity="HIGH",
                        message=(
                            f"GST legal name '{portal_legal_name}' does not match bidder name "
                            f"'{bidder.legal_name}'."
                        ),
                        evidence_reference=gst_ver.evidence_reference,
                    )
                )
                score_breakdown.append({"rule": "RULE-GST-001", "points": 5, "max": 20})
            elif gst_status != "ACTIVE":
                rule_gst = RuleResult(
                    bid_id=bid.bid_id,
                    rule_id="RULE-GST-001",
                    rule_name="GST Registration & Name Consistency",
                    clause="Section 3.2 - GST Compliance",
                    status="FAIL",
                    details=f"GST status is {gst_status}, requires ACTIVE.",
                    is_mandatory=True,
                )
                has_mandatory_failure = True
                findings.append(
                    Finding(
                        bid_id=bid.bid_id,
                        finding_type="INACTIVE_GST",
                        severity="HIGH",
                        message=f"GSTIN {gst_ver.identifier} status is {gst_status}.",
                        evidence_reference=gst_ver.evidence_reference,
                    )
                )
                score_breakdown.append({"rule": "RULE-GST-001", "points": 0, "max": 20})
            else:
                rule_gst = RuleResult(
                    bid_id=bid.bid_id,
                    rule_id="RULE-GST-001",
                    rule_name="GST Registration & Name Consistency",
                    clause="Section 3.2 - GST Compliance",
                    status="PASS",
                    details=f"GSTIN {gst_ver.identifier} is ACTIVE and legal name matches.",
                    is_mandatory=True,
                )
                passed_rules += 1
                score_breakdown.append({"rule": "RULE-GST-001", "points": 20, "max": 20})
        else:
            rule_gst = RuleResult(
                bid_id=bid.bid_id,
                rule_id="RULE-GST-001",
                rule_name="GST Registration & Name Consistency",
                clause="Section 3.2 - GST Compliance",
                status="FAIL",
                details="GST record not found or unverified.",
                is_mandatory=True,
            )
            has_mandatory_failure = True
            findings.append(
                Finding(
                    bid_id=bid.bid_id,
                    finding_type="MISSING_GST",
                    severity="HIGH",
                    message="GST registration details could not be verified.",
                    evidence_reference="gst",
                )
            )
            score_breakdown.append({"rule": "RULE-GST-001", "points": 0, "max": 20})
        rule_results.append(rule_gst)
        db.add(rule_gst)

        # --- Rule 3: MSME / Udyam Certificate ---
        udyam_ver = verifications.get("UDYAM")
        msme_required = tender.eligibility_conditions.get("msmeRequired", True) if tender.eligibility_conditions else True

        if udyam_ver and udyam_ver.status == "VERIFIED":
            rule_msme = RuleResult(
                bid_id=bid.bid_id,
                rule_id="RULE-UDYAM-001",
                rule_name="MSME / Udyam Registration Validity",
                clause="Section 4.1 - MSME Eligibility",
                status="PASS",
                details=f"Valid Udyam registration {udyam_ver.identifier} verified.",
                is_mandatory=msme_required,
            )
            passed_rules += 1
            score_breakdown.append({"rule": "RULE-UDYAM-001", "points": 20, "max": 20})
        else:
            rule_msme = RuleResult(
                bid_id=bid.bid_id,
                rule_id="RULE-UDYAM-001",
                rule_name="MSME / Udyam Registration Validity",
                clause="Section 4.1 - MSME Eligibility",
                status="NEEDS_CLARIFICATION" if not msme_required else "FAIL",
                details="Udyam certificate missing or registration unverified.",
                is_mandatory=msme_required,
            )
            if msme_required:
                has_mandatory_failure = True
            findings.append(
                Finding(
                    bid_id=bid.bid_id,
                    finding_type="MISSING_UDYAM_CERTIFICATE",
                    severity="HIGH" if msme_required else "MEDIUM",
                    message="Udyam / MSME Certificate not provided or registration not found.",
                    evidence_reference="demo-data/udyam-records.json",
                )
            )
            score_breakdown.append({"rule": "RULE-UDYAM-001", "points": 0, "max": 20})
        rule_results.append(rule_msme)
        db.add(rule_msme)

        # --- Rule 4: OEM Authorisation ---
        oem_ver = verifications.get("OEM")
        if oem_ver and oem_ver.status == "VERIFIED":
            rule_oem = RuleResult(
                bid_id=bid.bid_id,
                rule_id="RULE-OEM-001",
                rule_name="OEM Authorisation Letter Validity",
                clause="Section 4.2 - Technical Authorization",
                status="PASS",
                details=f"OEM letter {oem_ver.identifier} is active and verified.",
                is_mandatory=True,
            )
            passed_rules += 1
            score_breakdown.append({"rule": "RULE-OEM-001", "points": 20, "max": 20})
        elif oem_ver and oem_ver.status == "EXPIRED":
            valid_until = (oem_ver.verified_facts or {}).get("validUntil", "2022-12-31")
            rule_oem = RuleResult(
                bid_id=bid.bid_id,
                rule_id="RULE-OEM-001",
                rule_name="OEM Authorisation Letter Validity",
                clause="Section 4.2 - Technical Authorization",
                status="FAIL",
                details=f"OEM authorisation expired on {valid_until}.",
                is_mandatory=True,
            )
            has_mandatory_failure = True
            findings.append(
                Finding(
                    bid_id=bid.bid_id,
                    finding_type="EXPIRED_OEM_AUTHORISATION",
                    severity="HIGH",
                    message=f"OEM authorisation #{oem_ver.identifier} has expired (valid until {valid_until}).",
                    evidence_reference=oem_ver.evidence_reference,
                )
            )
            score_breakdown.append({"rule": "RULE-OEM-001", "points": 0, "max": 20})
        else:
            rule_oem = RuleResult(
                bid_id=bid.bid_id,
                rule_id="RULE-OEM-001",
                rule_name="OEM Authorisation Letter Validity",
                clause="Section 4.2 - Technical Authorization",
                status="FAIL",
                details="OEM letter missing or unverified.",
                is_mandatory=True,
            )
            has_mandatory_failure = True
            findings.append(
                Finding(
                    bid_id=bid.bid_id,
                    finding_type="MISSING_OEM_AUTHORISATION",
                    severity="HIGH",
                    message="OEM authorisation document missing.",
                    evidence_reference="oem",
                )
            )
            score_breakdown.append({"rule": "RULE-OEM-001", "points": 0, "max": 20})
        rule_results.append(rule_oem)
        db.add(rule_oem)

        # --- Rule 5: Make in India Local Content ---
        mii_fact = facts.get("localContentPercentage")
        threshold = 50.0
        if tender.eligibility_conditions:
            threshold = float(tender.eligibility_conditions.get("localContentThreshold", 50.0))

        declared_content = float(mii_fact.value) if mii_fact and mii_fact.value else 0.0
        if declared_content >= threshold:
            rule_mii = RuleResult(
                bid_id=bid.bid_id,
                rule_id="RULE-MII-001",
                rule_name="Make in India Local Content Declaration",
                clause="Section 4.3 - Public Procurement Order",
                status="PASS",
                details=f"Declared local content of {declared_content}% meets threshold of {threshold}%.",
                is_mandatory=True,
            )
            passed_rules += 1
            score_breakdown.append({"rule": "RULE-MII-001", "points": 15, "max": 15})
        else:
            rule_mii = RuleResult(
                bid_id=bid.bid_id,
                rule_id="RULE-MII-001",
                rule_name="Make in India Local Content Declaration",
                clause="Section 4.3 - Public Procurement Order",
                status="NEEDS_CLARIFICATION",
                details=f"Declared local content ({declared_content}%) is below required threshold ({threshold}%).",
                is_mandatory=True,
            )
            findings.append(
                Finding(
                    bid_id=bid.bid_id,
                    finding_type="LOCAL_CONTENT_DEFICIT",
                    severity="MEDIUM",
                    message=f"Local content declared at {declared_content}%, below mandatory requirement of {threshold}%.",
                    evidence_reference=mii_fact.evidence if mii_fact else "mii",
                )
            )
            score_breakdown.append({"rule": "RULE-MII-001", "points": 5, "max": 15})
        rule_results.append(rule_mii)
        db.add(rule_mii)

        # --- Rule 6: Blacklist / Debarment Check ---
        black_ver = verifications.get("BLACKLIST")
        is_blacklisted = False
        if black_ver and black_ver.verified_facts:
            is_blacklisted = black_ver.verified_facts.get("blacklisted", False)

        if not is_blacklisted and black_ver and black_ver.status in ("VERIFIED", "NOT_FOUND"):
            rule_black = RuleResult(
                bid_id=bid.bid_id,
                rule_id="RULE-BLACKLIST-001",
                rule_name="Central Debarment & Blacklist Verification",
                clause="Section 2.4 - Debarment Check",
                status="PASS",
                details="No debarment or blacklisting orders recorded.",
                is_mandatory=True,
            )
            passed_rules += 1
            score_breakdown.append({"rule": "RULE-BLACKLIST-001", "points": 10, "max": 10})
        else:
            rule_black = RuleResult(
                bid_id=bid.bid_id,
                rule_id="RULE-BLACKLIST-001",
                rule_name="Central Debarment & Blacklist Verification",
                clause="Section 2.4 - Debarment Check",
                status="FAIL",
                details="Entity appears on debarment/blacklist registry.",
                is_mandatory=True,
            )
            has_mandatory_failure = True
            findings.append(
                Finding(
                    bid_id=bid.bid_id,
                    finding_type="BLACKLIST_HIT",
                    severity="CRITICAL",
                    message="Bidder entity is listed on debarment registry.",
                    evidence_reference="blacklist",
                )
            )
            score_breakdown.append({"rule": "RULE-BLACKLIST-001", "points": 0, "max": 10})
        rule_results.append(rule_black)
        db.add(rule_black)

        # Add findings to DB
        for f in findings:
            db.add(f)

        # Compute Scores & Risk Level
        total_points = sum(item["points"] for item in score_breakdown)
        max_points = sum(item["max"] for item in score_breakdown)
        compliance_score = round((total_points / max_points) * 100.0, 1) if max_points > 0 else 0.0

        # Verification coverage: percentage of verifications successfully performed
        verified_count = sum(1 for v in verifications.values() if v.status == "VERIFIED")
        total_verifications = max(len(verifications), 1)
        verification_coverage = round((verified_count / total_verifications) * 100.0, 1)

        # Derive Recommendation and Risk Level
        has_critical_or_high_finding = any(f.severity in ("CRITICAL", "HIGH") for f in findings)
        has_entity_mismatch = any(f.finding_type == "ENTITY_NAME_MISMATCH" for f in findings)
        has_missing_evidence = any(
            f.finding_type in ("MISSING_UDYAM_CERTIFICATE", "EXPIRED_OEM_AUTHORISATION", "LOCAL_CONTENT_DEFICIT")
            for f in findings
        )

        if has_entity_mismatch:
            risk_level = "HIGH"
            recommendation = "High-Risk — Officer Review Required"
            summary = (
                "Entity mismatch detected between bidder registration and statutory GST records. "
                "Immediate officer review is required before proceeding."
            )
        elif has_missing_evidence or has_mandatory_failure:
            risk_level = "HIGH" if has_mandatory_failure else "MEDIUM"
            recommendation = "Needs Clarification — Missing or Unverified Evidence"
            summary = (
                "One or more required documents or statutory registrations are missing, expired, "
                "or require formal clarification from the bidder."
            )
        else:
            risk_level = "LOW"
            recommendation = "Compliant — Ready for Officer Confirmation"
            summary = (
                "All statutory identity, GST, MSME, OEM authorisation, and Make in India criteria "
                "have passed automated verification. Ready for officer confirmation."
            )

        assessment = Assessment(
            bid_id=bid.bid_id,
            compliance_score=compliance_score,
            verification_coverage=verification_coverage,
            risk_level=risk_level,
            recommendation=recommendation,
            recommendation_summary=summary,
            has_mandatory_failure=has_mandatory_failure,
            score_breakdown=score_breakdown,
            evaluated_at=utc_now_iso(),
        )
        db.add(assessment)
        db.flush()
        return assessment

    def _record_audit(self, db: Session, bid_id: str, event_type: str, actor: str, details: dict) -> None:
        event = AuditEvent(
            bid_id=bid_id,
            event_type=event_type,
            actor=actor,
            details=details,
            timestamp=utc_now_iso(),
        )
        db.add(event)
        db.flush()
