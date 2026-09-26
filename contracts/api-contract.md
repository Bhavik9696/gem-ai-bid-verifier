# ComplianceOS API Contract

**Version:** 1.0  
**Locked Ports:**
- Core API (FastAPI): `http://localhost:8000` (Owner: Member 3)
- Connector API (FastAPI): `http://localhost:8001` (Owner: Member 6)
- Frontend Dashboard (Next.js): `http://localhost:3000` (Owner: Member 2)

---

## 1. Core API (Port 8000)

### 1.1 Health Check
- **Endpoint:** `GET /health`
- **Response:** `200 OK`
```json
{
  "status": "ok",
  "service": "complianceos-core-api",
  "port": 8000,
  "version": "1.0.0"
}
```

---

### 1.2 Tenders

#### `GET /api/tenders`
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

#### `GET /api/tenders/{tenderId}`
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

#### `GET /api/tenders/{tenderId}/bids`
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

---

### 1.3 Verification & Assessment

#### `POST /api/bids/{bidId}/run-verification`
Triggers the multi-phase orchestration pipeline:
1. Document extraction (Member 4 Document AI integration)
2. Dynamic source connector calls at port 8001 (Member 6 Connector API)
3. Conflict detection, rulebook evaluation, scoring, and recommendation
4. Persistence and audit trail recording

**Response `200 OK`:** Returns full `AssessmentResponse` (see schema below).

#### `GET /api/bids/{bidId}/assessment`
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
      "details": { "message": "Verification pipeline initiated for bid GEM-BID-2026-001" },
      "timestamp": "2026-09-26T15:00:00+00:00"
    }
  ]
}
```

---

### 1.4 Officer Decisions

#### `POST /api/bids/{bidId}/decision`
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

*Note: `reason` is strictly required when decision is `OVERRIDE` or `REQUEST_CLARIFICATION`.*

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

---

### 1.5 Audit Timeline

#### `GET /api/bids/{bidId}/audit-events`
Returns the append-only audit trail of all automated actions and officer decisions.

**Response `200 OK`:**
```json
[
  {
    "id": "ae-001",
    "bidId": "GEM-BID-2026-001",
    "eventType": "BID_INGESTED",
    "actor": "SYSTEM",
    "details": { "message": "Bid GEM-BID-2026-001 imported from GeM data source." },
    "timestamp": "2026-09-26T14:00:00+00:00"
  },
  {
    "id": "ae-002",
    "bidId": "GEM-BID-2026-001",
    "eventType": "OFFICER_DECISION_RECORDED",
    "actor": "OFFICER-001",
    "details": { "decision": "CONFIRM", "newBidStatus": "CONFIRMED" },
    "timestamp": "2026-09-26T15:20:00+00:00"
  }
]
```

---

## 2. Connector API (Port 8001)

All responses carry `mode="DEMO"` in the prototype.

| Method | Endpoint | Query / Param | Description |
|---|---|---|---|
| GET | `/health` | - | Health check |
| GET | `/api/v1/gst/{gstin}` | Path: `gstin` | GST status and registered name |
| GET | `/api/v1/pan/{pan}` | Path: `pan` | Tax entity verification |
| GET | `/api/v1/udyam/{udyamNumber}` | Path: `udyamNumber` | MSME registration check |
| GET | `/api/v1/mca/{cin}` | Path: `cin` | MCA company details |
| GET | `/api/v1/oem/{authorisationNumber}` | Path: `authorisationNumber` | OEM authorization validity |
| GET | `/api/v1/digilocker/{documentId}` | Path: `documentId` | DigiLocker document origin check |
| GET | `/api/v1/blacklist` | Query: `pan={pan}` | Debarment / blacklist check |
| GET | `/api/v1/statutory/{source}/{id}` | Path: `source`, `id` | Statutory registration check |

---

## 3. Demo Bidder Scenarios & Expectations

| Bidder ID | Name | Expected Risk | Recommendation | Key Driver |
|---|---|---|---|---|
| `GEM-BID-2026-001` | Aster Tech Private Limited | `LOW` | `Compliant — Ready for Officer Confirmation` | All statutory, GST, MSME, OEM, and MII checks pass. |
| `GEM-BID-2026-002` | Bharat Supplies Private Limited | `HIGH` | `High-Risk — Officer Review Required` | Legal name mismatch: GST shows "Bharat Trading Company". |
| `GEM-BID-2026-003` | Crest Systems Private Limited | `HIGH` | `Needs Clarification — Missing or Unverified Evidence` | Udyam certificate missing; OEM authorisation letter expired (2022-12-31). |