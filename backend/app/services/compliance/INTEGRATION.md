# Compliance Engine — Integration Guide for Core API (Member 3)

This document describes how the Core API orchestrator invokes the Compliance Engine and interprets its output. All contracts documented here are grounded in the actual merged implementation.

---

## 1. How to Invoke the Compliance Engine

```python
from app.services.compliance import evaluate_bid_compliance
from app.services.compliance.schemas import (
    BidComplianceInput,
    BidderProfile,
    TenderContext,
    ExtractedFact,
    VerificationResult,
    ComplianceAssessment,
)

# Build the input bundle from orchestrated data
input_data = BidComplianceInput(
    bid_id="GEM-BID-2026-001",
    tender=TenderContext(
        tender_id="TENDER-2026-IT-001",
        title="Supply of IT Equipment",
        closing_date="2026-09-30",
        category="IT Equipment",
        rulebook_id="TENDER-2026-IT-001_v1",
        make_in_india_required=True,
        local_content_threshold=50.0,
        msme_mandatory=True,
        oem_required=True,
        mandatory_documents=[
            "GST_CERTIFICATE", "PAN_CARD",
            "UDYAM_CERTIFICATE", "OEM_AUTHORISATION",
        ],
    ),
    bidder=BidderProfile(
        bidder_id="BID-001",
        legal_name="Aster Tech Private Limited",
        pan="AABCA1234F",
        gstin="33AABCA1234F1Z5",
        udyam_number="UDYAM-TN-01-0001234",
        cin="U72200TN2015PTC123456",
    ),
    extracted_facts=[...],         # From Member 4
    verification_results=[...],    # From Member 6 connectors
)

# Call the engine — pure function, no side effects
assessment: ComplianceAssessment = evaluate_bid_compliance(input_data)
```

The function is **synchronous** and **pure**. It performs no database access, no HTTP calls, and no LLM calls. If you need async, wrap it:

```python
import asyncio
assessment = await asyncio.to_thread(evaluate_bid_compliance, input_data)
```

---

## 2. Input Data Requirements

### `TenderContext`

| Field                     | Type        | Required | Notes |
|---------------------------|-------------|----------|-------|
| `tender_id`               | `str`       | ✅       | |
| `title`                   | `str`       | ✅       | |
| `closing_date`            | `str`       | ✅       | ISO date `YYYY-MM-DD` |
| `category`                | `str`       | optional | |
| `rulebook_id`             | `str`       | ✅       | Must match a YAML file in `rules/` |
| `make_in_india_required`  | `bool`      | default `False` | |
| `local_content_threshold` | `float`     | optional | 0–100, used when `make_in_india_required=True` |
| `msme_mandatory`          | `bool`      | default `False` | |
| `oem_required`            | `bool`      | default `False` | |
| `mandatory_documents`     | `list[str]` | default `[]` | e.g. `["GST_CERTIFICATE", "PAN_CARD"]` |

### `BidderProfile`

| Field                  | Type  | Required | Notes |
|------------------------|-------|----------|-------|
| `bidder_id`            | `str` | ✅       | |
| `legal_name`           | `str` | ✅       | Used for name matching |
| `pan`                  | `str` | optional | |
| `gstin`                | `str` | optional | |
| `udyam_number`         | `str` | optional | |
| `cin`                  | `str` | optional | |
| `authorised_signatory` | `str` | optional | |

### `ExtractedFact` (from Member 4)

| Field           | Type       | Required |
|-----------------|------------|----------|
| `field`         | `str`      | ✅       | e.g. `"pan"`, `"gstin"`, `"legalName"` |
| `value`         | `str|None` | ✅       | `None` if field expected but not found |
| `confidence`    | `float`    | ✅       | 0.0–1.0 |
| `document_id`   | `str`      | ✅       | |
| `page`          | `int|None` | optional | 1-indexed |
| `document_type` | `str|None` | optional | e.g. `"GST_CERTIFICATE"` |

### `VerificationResult` (from Member 6 connectors)

| Field                | Type       | Required |
|----------------------|------------|----------|
| `source`             | `str`      | ✅       | e.g. `"GST_DEMO"`, `"PAN_DEMO"` |
| `mode`               | `str`      | default `"DEMO"` | |
| `identifier`         | `str`      | ✅       | The queried identifier |
| `status`             | `str`      | ✅       | `"VERIFIED"`, `"NOT_FOUND"`, `"ERROR"` |
| `verified_facts`     | `dict`     | default `{}` | Source-specific key-value facts |
| `checked_at`         | `str`      | ✅       | ISO 8601 timestamp |
| `evidence_reference` | `str|None` | optional | Human-readable source reference |

---

## 3. Output: `ComplianceAssessment`

### Top-Level Fields

| Field                    | Type                   | Officer-Facing | Notes |
|--------------------------|------------------------|:--------------:|-------|
| `bid_id`                 | `str`                  | ✅ | |
| `compliance_score`       | `float (0–100)`        | ✅ | Weighted score |
| `risk_score`             | `float (0–100)`        | ✅ | Additive risk |
| `risk_level`             | `RiskLevel`            | ✅ | `LOW` / `MODERATE` / `HIGH` / `CRITICAL` |
| `recommendation`         | `str`                  | ✅ | One of 3 exact strings |
| `recommendation_summary` | `str`                  | ✅ | Plain-language explanation |
| `has_mandatory_failure`  | `bool`                 | ✅ | True = cannot pass without review |
| `match_results`          | `list[MatchResult]`    | ✅ | Identity comparisons |
| `findings`               | `list[Finding]`        | ✅ | Conflicts and flags |
| `rule_results`           | `list[RuleResult]`     | ✅ | Per-rule outcomes |
| `score_breakdown`        | `list[ScoreBreakdown]` | ✅ | Per-category detail |
| `evaluated_at`           | `str`                  | ✅ | ISO 8601 |

### Interpreting `recommendation`

| Value | Meaning | Dashboard Action |
|-------|---------|-----------------|
| `"Compliant — Ready for Officer Confirmation"` | All mandatory checks passed, low/moderate risk | Show green; enable Confirm button |
| `"Needs Clarification — Missing or Unverified Evidence"` | Evidence gaps or unverified sources | Show amber; highlight missing items |
| `"High-Risk — Officer Review Required"` | Mandatory failures or critical risk | Show red; require detailed review |

### Interpreting `has_mandatory_failure`

When `True`, at least one **mandatory** rule has `result = FAIL`. This **overrides** the compliance score — even a high score does not make the bid compliant.

### Interpreting `rule_results[].result`

| Status                | Meaning | Dashboard Display |
|-----------------------|---------|-------------------|
| `PASS`                | Rule satisfied | ✅ |
| `FAIL`                | Rule not met | ❌ with severity |
| `NEEDS_CLARIFICATION` | Cannot evaluate — missing evidence | ⚠️ |
| `SOURCE_UNAVAILABLE`  | Connector error or absent | ⚠️ source issue |
| `NOT_APPLICABLE`      | Skipped (condition not met for this tender) | — |

### Interpreting `findings[].severity`

| Severity  | Meaning |
|-----------|---------|
| `BLOCKER` | Cannot proceed; disqualifying issue |
| `HIGH`    | Serious issue requiring review |
| `MEDIUM`  | Notable discrepancy |
| `LOW`     | Minor observation |
| `INFO`    | Informational only |

---

## 4. Source-Unavailable and Unverified Evidence

When a connector is absent, returns `ERROR`, or returns `NOT_FOUND`:
- The relevant rule produces `SOURCE_UNAVAILABLE` or `NEEDS_CLARIFICATION`
- The conflict detector emits a `SOURCE_UNAVAILABLE` finding
- The scoring module adds risk points (+15 for mandatory rules)
- **This is never treated as a positive confirmation**

The dashboard should show the connector status and explain that verification was not completed, not that the bidder failed.

---

## 5. Orchestrator Responsibilities (Member 3)

The compliance engine is a **pure function**. The orchestrator is responsible for:

1. **Assembling `BidComplianceInput`** from tender data, bidder profile, Member 4 extracted facts, and Member 6 connector responses.
2. **Calling `evaluate_bid_compliance()`** and receiving the `ComplianceAssessment`.
3. **Persisting** the assessment to the database.
4. **Forwarding** the assessment to the frontend via `GET /api/bids/{bidId}/assessment`.
5. **Recording audit events** (verification triggered, assessment completed, officer decisions).
6. **Handling errors**: If `evaluate_bid_compliance()` raises `FileNotFoundError` (missing rulebook) or `ValueError` (malformed rulebook), the orchestrator should return an appropriate error to the frontend and log the issue.

---

## 6. Illustrative Example (Demo Data)

> **Note:** This example uses the demo bidder "Aster Tech" from `demo-data/`. All connector responses are `mode: "DEMO"` and must not be represented as live government results.

### Input snippet

```python
input_data = BidComplianceInput(
    bid_id="GEM-BID-2026-001",
    tender=TenderContext(
        tender_id="TENDER-2026-IT-001",
        title="Supply of IT Equipment",
        closing_date="2026-09-30",
        rulebook_id="TENDER-2026-IT-001_v1",
        msme_mandatory=True,
        oem_required=True,
        make_in_india_required=True,
        local_content_threshold=50.0,
    ),
    bidder=BidderProfile(
        bidder_id="BID-001",
        legal_name="Aster Tech Private Limited",
        pan="AABCA1234F",
        gstin="33AABCA1234F1Z5",
    ),
    extracted_facts=[
        ExtractedFact(field="gstin", value="33AABCA1234F1Z5",
                      confidence=0.98, document_id="DOC-001"),
        ExtractedFact(field="pan", value="AABCA1234F",
                      confidence=0.99, document_id="DOC-002"),
    ],
    verification_results=[
        VerificationResult(
            source="GST_DEMO", identifier="33AABCA1234F1Z5",
            status="VERIFIED",
            verified_facts={"legalName": "Aster Tech Private Limited",
                            "gstStatus": "ACTIVE",
                            "returnFilingStatus": "CURRENT"},
            checked_at="2026-09-26T15:00:00+00:00"),
        VerificationResult(
            source="PAN_DEMO", identifier="AABCA1234F",
            status="VERIFIED",
            verified_facts={"pan": "AABCA1234F",
                            "name": "Aster Tech Private Limited"},
            checked_at="2026-09-26T15:00:00+00:00"),
    ],
)
```

### Output summary (Aster — Compliant)

```json
{
  "bid_id": "GEM-BID-2026-001",
  "compliance_score": 100.0,
  "risk_score": 0.0,
  "risk_level": "LOW",
  "recommendation": "Compliant — Ready for Officer Confirmation",
  "has_mandatory_failure": false,
  "rule_results": [
    {"rule_id": "GST_ACTIVE_ON_CLOSING_DATE", "result": "PASS"},
    {"rule_id": "PAN_ENTITY_MATCH", "result": "PASS"},
    {"rule_id": "BLACKLIST_CHECK", "result": "PASS"}
  ],
  "findings": [],
  "evaluated_at": "2026-09-27T..."
}
```

---

## 7. Dependencies and Unresolved Items

| Item | Status | Owner |
|------|--------|-------|
| `evaluate_bid_compliance()` entry point | ✅ Implemented and tested | Member 5 |
| Connector field-key mapping in `entity_matcher.py` | ✅ Aligned with Member 6 `verified_facts` keys | Member 5 |
| YAML rulebook `TENDER-2026-IT-001_v1` | ✅ Complete | Member 5 |
| Core API orchestration to assemble `BidComplianceInput` | Owned by Member 3 | Member 3 |
| Frontend assessment display | Owned by Member 2 | Member 2 |
| `pyyaml` dependency | Required in `requirements.txt` | Shared |

---

**Important:** ComplianceOS is a decision-support system. The compliance engine provides evidence-backed analysis. The Procurement Officer retains final decision-making authority.
