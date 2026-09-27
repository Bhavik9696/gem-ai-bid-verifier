
# ComplianceOS API Contract

**Version:** 1.0  
**Owners:** Member 3 (Core API), Member 6 (Connector API)

---

## Locked Ports

| Service | Technology | Port | Owner |
|---|---|---:|---|
| Core API | FastAPI | 8000 | Member 3 |
| Connector API | FastAPI | 8001 | Member 6 |
| Frontend Dashboard | Next.js | 3000 | Member 2 |

---

# 1. Core API — Port 8000

The Core API manages tenders, bids, verification orchestration, compliance assessments, officer decisions, and audit events.

## 1.1 Health Check

**Endpoint:** `GET /health`

**Response:** `200 OK`

```json
{
  "status": "ok",
  "service": "complianceos-core-api",
  "port": 8000,
  "version": "1.0.0"
}
```

## 1.2 Tenders

### `GET /api/tenders`

Returns a list of all imported GeM tenders.

**Response `200 OK`:**

```json
[
  {
    "tenderId": "TENDER-GEM-2026-001",
    "title": "Supply of IT Equipment and Accessories",
    "referenceNumber": "GeM-2026-IT-001",
    "category": "IT Equipment",
    "buyerOrganisation": "Ministry of Electronics and IT",
    "publishedDate": "2026-08-01",
    "bidClosingDate": "2026-09-30",
    "estimatedValue": 5000000.0,
    "currency": "INR",
    "status": "ACTIVE"
  }
]
```

### `GET /api/tenders/{tenderId}`

Returns detailed tender metadata and eligibility conditions.

**Response `200 OK`:**

```json
{
  "tenderId": "TENDER-GEM-2026-001",
  "title": "Supply of IT Equipment and Accessories",
  "referenceNumber": "GeM-2026-IT-001",
  "category": "IT Equipment",
  "buyerOrganisation": "Ministry of Electronics and IT",
  "publishedDate": "2026-08-01",
  "bidClosingDate": "2026-09-30",
  "estimatedValue": 5000000.0,
  "currency": "INR",
  "status": "ACTIVE",
  "eligibilityConditions": {
    "msmeRequired": true,
    "makeInIndiaRequired": true,
    "localContentThreshold": 50,
    "oemRequired": true,
    "minimumTurnover": 2000000
  },
  "mandatoryDocuments": [
    "GST Registration Certificate",
    "PAN Card",
    "Udyam/MSME Certificate",
    "OEM Authorisation Letter",
    "Make in India Declaration"
  ],
  "rulebookVersion": "v1.0"
}
```

### `GET /api/tenders/{tenderId}/bids`

Returns all bids submitted for a specific tender.

**Response `200 OK`:**

```json
[
  {
    "bidId": "GEM-BID-2026-001",
    "tenderId": "TENDER-GEM-2026-001",
    "bidderId": "BID-001",
    "bidderName": "Aster Tech Private Limited",
    "submittedAt": "2026-09-10T14:30:00Z",
    "bidAmount": 4750000.0,
    "currency": "INR",
    "status": "SUBMITTED",
    "complianceScore": null,
    "riskLevel": null,
    "recommendation": null
  }
]
```

## 1.3 Verification and Assessment

### `POST /api/bids/{bidId}/run-verification`

Triggers the end-to-end verification pipeline:

1. Document extraction and fact identification.
2. Source connector calls to the Connector API on port 8001.
3. Conflict detection, rulebook evaluation, scoring, and recommendation.
4. Persistence of results and audit trail recording.

**Response `200 OK`:** Returns the full assessment response.

### `GET /api/bids/{bidId}/assessment`

Fetches the latest compliance assessment for a bid.

**Response `200 OK`:**

```json
{
  "bidId": "GEM-BID-2026-001",
  "complianceScore": 100.0,
  "verificationCoverage": 100.0,
  "riskLevel": "LOW",
  "recommendation": "Compliant — Ready for Officer Confirmation",
  "recommendationSummary": "All statutory identity, GST, MSME, OEM authorisation, and Make in India criteria have passed automated verification. Ready for officer confirmation.",
  "hasMandatoryFailure": false,
  "scoreBreakdown": [
    { "rule": "RULE-PAN-001", "points": 15, "max": 15 },
    { "rule": "RULE-GST-001", "points": 20, "max": 20 },
    { "rule": "RULE-UDYAM-001", "points": 20, "max": 20 },
    { "rule": "RULE-OEM-001", "points": 20, "max": 20 },
    { "rule": "RULE-MII-001", "points": 15, "max": 15 },
    { "rule": "RULE-BLACKLIST-001", "points": 10, "max": 10 }
  ],
  "evaluatedAt": "2026-09-26T15:00:00+00:00",
  "ruleResults": [
    {
      "id": "rule-res-001",
      "ruleId": "RULE-GST-001",
      "ruleName": "GST Registration & Name Consistency",
      "clause": "Section 3.2 - GST Compliance",
      "status": "PASS",
      "details": "GSTIN 33AABCA1234F1Z5 is ACTIVE and legal name matches.",
      "isMandatory": true
    }
  ],
  "findings": [],
  "verificationResults": [
    {
      "id": "ver-001",
      "source": "GST_DEMO",
      "mode": "DEMO",
      "identifier": "33AABCA1234F1Z5",
      "status": "VERIFIED",
      "verifiedFacts": {
        "legalName": "Aster Tech Private Limited",
        "gstStatus": "ACTIVE",
        "registrationDate": "2018-06-15",
        "returnFilingStatus": "CURRENT"
      },
      "evidenceReference": "demo-data/gst-records.json#33AABCA1234F1Z5",
      "checkedAt": "2026-09-26T15:00:00+00:00"
    }
  ],
  "extractedFacts": [
    {
      "id": "fact-001",
      "field": "gstin",
      "value": "33AABCA1234F1Z5",
      "confidence": 0.98,
      "documentId": "DOC-001-01",
      "page": 1,
      "evidence": "Extracted from aster_gst_cert.pdf: GSTIN 33AABCA1234F1Z5"
    }
  ],
  "auditEvents": [
    {
      "id": "audit-001",
      "bidId": "GEM-BID-2026-001",
      "eventType": "VERIFICATION_TRIGGERED",
      "actor": "SYSTEM",
      "details": {
        "message": "Verification pipeline initiated for bid GEM-BID-2026-001"
      },
      "timestamp": "2026-09-26T15:00:00+00:00"
    }
  ]
}
```

## 1.4 Officer Decisions

### `POST /api/bids/{bidId}/decision`

Allows the procurement officer to confirm, request clarification, or override evaluation results.

**Request Body:**

```json
{
  "decision": "OVERRIDE",
  "reason": "Clarification provided by OEM via physical verification.",
  "notes": "Verified directly with OEM regional office.",
  "officerId": "OFFICER-001"
}
```

**Validation:** `reason` is required when the decision is `OVERRIDE` or `REQUEST_CLARIFICATION`.

**Response `200 OK`:**

```json
{
  "id": "dec-001",
  "bidId": "GEM-BID-2026-001",
  "officerId": "OFFICER-001",
  "decision": "OVERRIDE",
  "reason": "Clarification provided by OEM via physical verification.",
  "notes": "Verified directly with OEM regional office.",
  "decidedAt": "2026-09-26T15:15:00+00:00",
  "bidStatus": "OVERRIDDEN"
}
```

## 1.5 Audit Timeline

### `GET /api/bids/{bidId}/audit-events`

Returns the append-only audit trail of automated actions and officer decisions.

**Response `200 OK`:**

```json
[
  {
    "id": "ae-001",
    "bidId": "GEM-BID-2026-001",
    "eventType": "BID_INGESTED",
    "actor": "SYSTEM",
    "details": {
      "message": "Bid GEM-BID-2026-001 imported from GeM data source."
    },
    "timestamp": "2026-09-26T14:00:00+00:00"
  },
  {
    "id": "ae-002",
    "bidId": "GEM-BID-2026-001",
    "eventType": "OFFICER_DECISION_RECORDED",
    "actor": "OFFICER-001",
    "details": {
      "decision": "CONFIRM",
      "newBidStatus": "CONFIRMED"
    },
    "timestamp": "2026-09-26T15:20:00+00:00"
  }
]
```

---

# 2. Connector API — Port 8001

The Connector API provides verification responses to the Core API.

**Prototype limitation:** All connector responses use `mode: "DEMO"`. They are based on local demo datasets and must not be represented as live government API results.

## 2.1 Standard Connector Response Envelope

All connector responses follow this structure:

```json
{
  "source": "GST_DEMO",
  "mode": "DEMO",
  "identifier": "<queried identifier>",
  "status": "VERIFIED",
  "verifiedFacts": {},
  "checkedAt": "2026-09-26T14:00:00+00:00",
  "evidenceReference": "demo-data/gst-records.json#<identifier>"
}
```

### Connector Status Values

| Status | Meaning |
|---|---|
| `VERIFIED` | Identifier found; facts returned; no conflict detected |
| `NOT_FOUND` | Identifier not present in the demo source data |
| `MISMATCH` | Identifier found, but a field conflict exists |
| `EXPIRED` | Record found, but date-bound validity has lapsed |
| `BLACKLISTED` | Entity appears on the demo debarment/blacklist registry |
| `SOURCE_UNAVAILABLE` | Source unavailable; verification could not be completed |
| `NOT_APPLICABLE` | Check is not applicable for this entity type |

A missing record must not be interpreted as proof of compliance or non-compliance without considering the check's status and evidence.

## 2.2 Connector Endpoints

| Method | Endpoint | Query / Parameter | Description |
|---|---|---|---|
| GET | `/health` | — | Connector service health check |
| GET | `/api/v1/gst/{gstin}` | Path: `gstin` | GST registration and status lookup |
| GET | `/api/v1/pan/{pan}` | Path: `pan` | PAN / tax entity verification |
| GET | `/api/v1/udyam/{udyamNumber}` | Path: `udyamNumber` | Udyam/MSME registration lookup |
| GET | `/api/v1/mca/{cin}` | Path: `cin` | MCA company details |
| GET | `/api/v1/oem/{authorisationNumber}` | Path: `authorisationNumber` | OEM authorisation validation |
| GET | `/api/v1/digilocker/{documentId}` | Path: `documentId` | DigiLocker document-origin verification |
| GET | `/api/v1/blacklist?pan={pan}` | Query: `pan` | Blacklist/debarment check |
| GET | `/api/v1/statutory/{source}/{identifier}` | Path: `source`, `identifier` | Generic statutory check, such as EPFO/ESIC/NSIC |

## 2.3 Connector Health Check

**Endpoint:** `GET /health`

**Response:** `200 OK`

```json
{
  "status": "ok",
  "service": "connector-service",
  "port": 8001,
  "mode": "DEMO",
  "checkedAt": "2026-09-26T14:00:00+00:00"
}
```

## 2.4 Example: GST Response

```json
{
  "source": "GST_DEMO",
  "mode": "DEMO",
  "identifier": "33AABCA1234F1Z5",
  "status": "VERIFIED",
  "verifiedFacts": {
    "legalName": "Aster Tech Private Limited",
    "gstStatus": "ACTIVE",
    "registrationDate": "2018-06-15",
    "returnFilingStatus": "CURRENT"
  },
  "checkedAt": "2026-09-26T14:00:00+00:00",
  "evidenceReference": "demo-data/gst-records.json#33AABCA1234F1Z5"
}
```

## 2.5 Example: Blacklist Clean

```json
{
  "source": "BLACKLIST_DEMO",
  "mode": "DEMO",
  "identifier": "AABCA1234F",
  "status": "VERIFIED",
  "verifiedFacts": {
    "blacklisted": false
  },
  "checkedAt": "2026-09-26T14:00:00+00:00",
  "evidenceReference": "demo-data/blacklist-records.json"
}
```

---

# 3. Demo Bidder Scenarios and Expectations

| Bidder ID | Name | Expected Risk | Recommendation | Key Driver |
|---|---|---|---|---|
| `GEM-BID-2026-001` | Aster Tech Private Limited | `LOW` | Compliant — Ready for Officer Confirmation | All statutory, GST, MSME, OEM, and MII checks pass |
| `GEM-BID-2026-002` | Bharat Supplies Private Limited | `HIGH` | High-Risk — Officer Review Required | Legal name mismatch: GST shows "Bharat Trading Company" |
| `GEM-BID-2026-003` | Crest Systems Private Limited | `HIGH` | Needs Clarification — Missing or Unverified Evidence | Udyam certificate missing; OEM authorisation letter expired on 2022-12-31 |

## 3.1 Demo Identifier Reference

| Bidder | GSTIN | PAN | Udyam | OEM Reference | Expected Result |
|---|---|---|---|---|---|
| Aster Tech Pvt Ltd | `33AABCA1234F1Z5` | `AABCA1234F` | `UDYAM-TN-01-0001234` | `OEM-DELL-ASTER-2024-001` | All VERIFIED; compliant / low risk |
| Bharat Supplies Pvt Ltd | `07AADCB5432G1ZK` | `AADCB5432G` | `UDYAM-DL-02-0005678` | `OEM-HP-BHARAT-2023-005` | GST/PAN mismatch; high risk |
| Crest Systems Pvt Ltd | `29AAHCC7891H1ZT` | `AAHCC7891H` | Not registered | `OEM-LENOVO-CREST-2022-009` | Udyam NOT_FOUND and OEM EXPIRED; needs clarification |

---

**Important:** ComplianceOS is a decision-support system. Automated verification results and recommendations are presented for procurement-officer review and confirmation.
