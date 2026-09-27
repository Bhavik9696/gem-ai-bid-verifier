
# ComplianceOS — Frontend

AI-powered bid compliance verification and decision-support frontend for **GeM-style government procurement**.

Built with:

* **Next.js 14**
* **React**
* **TypeScript**
* **Next.js App Router**
* **Vanilla CSS**
* SVG-based charts and visualizations
* Mock data during prototype development

The frontend provides the complete procurement-officer workflow:

```text
Login
  ↓
Dashboard
  ↓
Tender
  ↓
Bidders
  ↓
Bidder Profile
  ↓
Documents
  ↓
Verification
  ↓
Conflicts
  ↓
Compliance Rules
  ↓
AI Recommendation
  ↓
Officer Review
  ↓
Audit Trail
  ↓
Reports
```

The current frontend uses typed demo data from `src/lib/mockData.ts`. The backend developer should replace this mock-data layer with API calls without changing the overall UI/route structure. 

---

# 1. Project Structure

```text
frontend/
│
├── public/
│
├── src/
│   │
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── globals.css
│   │
│   │   ├── login/
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │
│   │   ├── dashboard/
│   │   │   └── page.tsx
│   │
│   │   ├── tenders/
│   │   │   ├── page.tsx
│   │   │   └── import/
│   │   │       └── page.tsx
│   │
│   │   ├── bidders/
│   │   │   ├── page.tsx
│   │   │   └── [bidderId]/
│   │   │       ├── page.tsx
│   │   │       ├── documents/
│   │   │       ├── verification/
│   │   │       ├── conflicts/
│   │   │       ├── compliance/
│   │   │       ├── recommendation/
│   │   │       └── review/
│   │
│   │   ├── audit/
│   │   │   └── page.tsx
│   │
│   │   └── reports/
│   │       └── page.tsx
│   │
│   ├── components/
│   │   ├── Sidebar.tsx
│   │   └── TopBar.tsx
│   │
│   └── lib/
│       └── mockData.ts
│
├── package.json
├── tsconfig.json
├── next.config.ts
└── README.md
```

The implemented route structure includes dashboard, tender management/import, bidder evaluation, document intelligence, verification, conflicts, compliance, recommendation, review, audit, and reports. 

---

# 2. Running the Frontend

```bash
cd frontend
npm install
npm run dev -- --port 3001
```

Open:

```text
http://localhost:3001
```

The current login is mocked. Any credentials can be used and the user is taken to the dashboard. 

---

# 3. Frontend Routes

| Route                               | Purpose               |
| ----------------------------------- | --------------------- |
| `/login`                            | Authentication        |
| `/dashboard`                        | Procurement dashboard |
| `/tenders`                          | Tender list           |
| `/tenders/import`                   | Tender/bid import     |
| `/bidders`                          | Bidder list           |
| `/bidders/:bidderId`                | Bidder profile        |
| `/bidders/:bidderId/documents`      | Document intelligence |
| `/bidders/:bidderId/verification`   | External verification |
| `/bidders/:bidderId/conflicts`      | Conflict detection    |
| `/bidders/:bidderId/compliance`     | Compliance rules      |
| `/bidders/:bidderId/recommendation` | AI recommendation     |
| `/bidders/:bidderId/review`         | Officer decision      |
| `/audit`                            | Audit trail           |
| `/reports`                          | Reports               |

---

# 4. Important IDs

The frontend currently uses bidder IDs such as:

```text
BID-001
BID-002
BID-003
```

These IDs are used in dynamic routes:

```text
/bidders/BID-001
/bidders/BID-002
/bidders/BID-003
```

The current prototype scenarios are:

| Bidder    | Scenario                                                        |
| --------- | --------------------------------------------------------------- |
| `BID-001` | Fully compliant                                                 |
| `BID-002` | High risk — GST/PAN identity mismatch                           |
| `BID-003` | Needs clarification — missing Udyam / expired OEM authorization |

These scenarios are currently represented in the mock dataset. 

When integrating the backend, **do not hardcode these IDs**. The backend should return the actual bidder IDs.

---

# 5. Current Mock Data

All current prototype data is in:

```text
src/lib/mockData.ts
```

The main exports are:

```text
DEMO_TENDERS
DEMO_BIDDERS
DEMO_DOCUMENTS
DEMO_EXTRACTED_FIELDS

DEMO_GST_VERIFICATION
DEMO_PAN_VERIFICATION
DEMO_UDYAM_VERIFICATION
DEMO_OEM_VERIFICATION
DEMO_BLACKLIST_VERIFICATION

DEMO_CONFLICTS
DEMO_COMPLIANCE_RULES
DEMO_RECOMMENDATIONS
DEMO_AUDIT_EVENTS

CONNECTORS
```

The mock data contains typed examples for tenders, bidders, documents, OCR extraction, verification, conflicts, rules, AI recommendations, audit events, and connectors. 

**Backend integration should replace these values with API responses.**

---

# 6. Suggested Backend API Structure

The frontend does not currently enforce a backend API contract, so the following structure is the recommended integration contract.

Base URL:

```text
/api
```

For example:

```text
GET /api/tenders
GET /api/tenders/{tenderId}
GET /api/tenders/{tenderId}/bidders
GET /api/bidders/{bidderId}
```

---

# 7. Authentication API

## Login

```http
POST /api/auth/login
```

### Request

```json
{
  "email": "officer@example.com",
  "password": "password",
  "role": "PROCUREMENT_OFFICER"
}
```

### Response

```json
{
  "accessToken": "jwt-token",
  "refreshToken": "refresh-token",
  "user": {
    "id": "USR-001",
    "name": "Procurement Officer",
    "email": "officer@example.com",
    "role": "PROCUREMENT_OFFICER"
  }
}
```

The frontend should store the authenticated session/token and send it with protected API requests.

### Supported roles

```text
PROCUREMENT_OFFICER
REVIEWER
ADMIN
AUDITOR
```

The current prototype login provides these role choices but does not perform real authentication. 

---

# 8. Dashboard API

## Get dashboard statistics

```http
GET /api/dashboard
```

### Suggested response

```json
{
  "stats": {
    "totalTenders": 25,
    "bidsReceived": 86,
    "verifiedBidders": 61,
    "flaggedForReview": 12,
    "averageProcessingTime": "18m"
  },
  "tenderStatus": {
    "draft": 2,
    "underEvaluation": 8,
    "completed": 10,
    "cancelled": 1,
    "awarded": 4
  },
  "riskDistribution": {
    "high": 7,
    "medium": 15,
    "low": 51,
    "none": 13
  }
}
```

The current dashboard displays five statistics, tender-status visualization, risk indicators, recent tenders, quick actions, system health, bidder information, and audit events. 

---

# 9. Tender APIs

## Get tenders

```http
GET /api/tenders
```

Optional filters:

```text
?status=UNDER_EVALUATION
?search=solar
?page=1
&pageSize=20
```

### Response

```json
{
  "items": [
    {
      "id": "TND-001",
      "title": "Supply of Solar Panels",
      "department": "Department of Energy",
      "closingDate": "2026-10-15T17:00:00Z",
      "status": "UNDER_EVALUATION",
      "bidderCount": 12,
      "compliancePercentage": 82
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "total": 25
  }
}
```

---

## Get tender details

```http
GET /api/tenders/{tenderId}
```

### Response

```json
{
  "id": "TND-001",
  "title": "Supply of Solar Panels",
  "department": "Department of Energy",
  "closingDate": "2026-10-15T17:00:00Z",
  "status": "UNDER_EVALUATION",
  "eligibilityCriteria": [],
  "clauses": []
}
```

The frontend tender page displays tender metadata, eligibility requirements, key clauses and page references. 

---

# 10. Tender Import

```http
POST /api/tenders/import
```

Recommended:

```text
multipart/form-data
```

Possible fields:

```text
tenderFile
bidFiles[]
```

Response:

```json
{
  "importId": "IMP-001",
  "tenderId": "TND-001",
  "status": "PROCESSING"
}
```

The frontend currently represents import as a five-step workflow:

```text
Tender
  ↓
Bidders
  ↓
Documents
  ↓
Processing
  ↓
Done
```

The processing screen is currently simulated and should eventually be connected to the backend processing pipeline. 

---

# 11. Bidder APIs

## Get bidders

```http
GET /api/tenders/{tenderId}/bidders
```

Response:

```json
{
  "items": [
    {
      "id": "BID-001",
      "bidderId": "BID-001",
      "legalName": "Example Technologies Pvt Ltd",
      "pan": "ABCDE1234F",
      "gstin": "29ABCDE1234F1Z5",
      "complianceScore": 96,
      "verificationScore": 94,
      "riskLevel": "LOW",
      "status": "READY"
    }
  ]
}
```

The bidder list currently displays identity information, compliance score, verification score, risk level, flags, and review actions. 

---

# 12. Bidder Profile API

```http
GET /api/bidders/{bidderId}
```

### Response

```json
{
  "id": "BID-001",
  "tenderId": "TND-001",
  "legalName": "Example Technologies Pvt Ltd",
  "pan": "ABCDE1234F",
  "gstin": "29ABCDE1234F1Z5",
  "udyam": "UDYAM-KA-00-1234567",
  "cin": "U12345KA2020PTC000001",
  "signatory": "John Doe",
  "oemRelationship": "AUTHORIZED",
  "address": "Bengaluru, Karnataka",
  "complianceScore": 96,
  "verificationScore": 94,
  "riskScore": 12,
  "riskLevel": "LOW"
}
```

The bidder profile currently shows legal-entity details, identity relationships and weighted compliance breakdown. 

---

# 13. Document APIs

## Get bidder documents

```http
GET /api/bidders/{bidderId}/documents
```

Response:

```json
{
  "items": [
    {
      "id": "DOC-001",
      "name": "GST Certificate",
      "type": "GST_CERTIFICATE",
      "status": "EXTRACTED",
      "confidence": 98.4,
      "sha256": "..."
    }
  ]
}
```

---

## Get extracted fields

```http
GET /api/documents/{documentId}/extractions
```

Response:

```json
{
  "documentId": "DOC-001",
  "fields": [
    {
      "field": "GSTIN",
      "value": "29ABCDE1234F1Z5",
      "confidence": 98.4,
      "page": 1
    },
    {
      "field": "Legal Name",
      "value": "Example Technologies Pvt Ltd",
      "confidence": 96.7,
      "page": 1
    }
  ]
}
```

The document UI expects extracted field values, confidence percentages and page references. 

---

# 14. Verification APIs

## Run/get verification

```http
GET /api/bidders/{bidderId}/verification
```

Response:

```json
{
  "verificationPercentage": 94,
  "connectors": [
    {
      "type": "GST",
      "mode": "DEMO",
      "status": "VERIFIED",
      "fields": {
        "gstin": "29ABCDE1234F1Z5",
        "legalName": "Example Technologies Pvt Ltd",
        "status": "ACTIVE"
      }
    }
  ]
}
```

Possible connector status:

```text
VERIFIED
CONFLICT
MISSING
ERROR
NOT_APPLICABLE
```

Possible mode:

```text
LIVE
SANDBOX
DEMO
MANUAL
```

The current frontend displays GST, PAN, Udyam, OEM Authorisation and Blacklist/Debarment connectors, with several additional connectors displayed as not applicable. All prototype connector results currently show DEMO mode. 

---

# 15. Conflict API

```http
GET /api/bidders/{bidderId}/conflicts
```

Response:

```json
{
  "total": 1,
  "high": 1,
  "medium": 0,
  "conflicts": [
    {
      "id": "CON-001",
      "type": "IDENTITY_MISMATCH",
      "severity": "HIGH",
      "title": "GST legal name mismatch",
      "description": "Submitted GST details do not match source record.",
      "submission": {
        "field": "legalName",
        "value": "ABC Technologies"
      },
      "source": {
        "field": "legalName",
        "value": "ABC Trading Corporation"
      },
      "sourceName": "GST",
      "evidence": [
        "DOC-001"
      ],
      "ruleId": "RULE-004",
      "recommendation": "OFFICER_REVIEW"
    }
  ]
}
```

The conflict UI is designed around severity, submitted value versus source record, evidence, related rules and officer recommendation. 

---

# 16. Compliance Rules API

```http
GET /api/bidders/{bidderId}/compliance
```

Response:

```json
{
  "rulebookVersion": "RB-2026.09",
  "summary": {
    "total": 12,
    "passed": 9,
    "failed": 2,
    "needsClarification": 1
  },
  "rules": [
    {
      "id": "RULE-001",
      "name": "GST Active",
      "priority": "MANDATORY",
      "result": "PASS",
      "tenderClause": "4.2",
      "evidence": [
        "DOC-001"
      ]
    }
  ]
}
```

Possible rule results:

```text
PASS
FAIL
NEEDS_CLARIFICATION
```

The frontend displays rule ID, rule name, priority, result, tender clause and evidence. 

---

# 17. AI Recommendation API

```http
GET /api/bidders/{bidderId}/recommendation
```

Response:

```json
{
  "status": "HIGH_RISK",
  "score": 82,
  "reasons": [
    "GST legal name mismatch",
    "OEM authorization expired",
    "Mandatory compliance rule failed"
  ],
  "analysis": "The bidder requires officer review due to identity and eligibility conflicts.",
  "evidenceChain": [
    {
      "stage": "BID_DOCUMENT",
      "status": "COMPLETED"
    },
    {
      "stage": "OCR",
      "status": "COMPLETED"
    },
    {
      "stage": "CONNECTORS",
      "status": "COMPLETED"
    },
    {
      "stage": "CONFLICT_ENGINE",
      "status": "COMPLETED"
    },
    {
      "stage": "RULES_ENGINE",
      "status": "COMPLETED"
    },
    {
      "stage": "AI_RECOMMENDATION",
      "status": "COMPLETED"
    }
  ]
}
```

Possible recommendation:

```text
COMPLIANT
HIGH_RISK
NEEDS_CLARIFICATION
```

The recommendation page intentionally shows the reasoning and evidence chain from bid document through OCR, connectors, conflict/rules engines and AI recommendation. 

**Important:** the AI recommendation is advisory. It should not automatically make the final procurement decision.

---

# 18. Officer Review API

The review page provides three actions:

```text
CONFIRM
CLARIFY
OVERRIDE
```

The current UI requires a written reason for **Clarify** and **Override**, with Override specifically requiring a mandatory reason. 

## Submit decision

```http
POST /api/bidders/{bidderId}/review
```

Request:

```json
{
  "decision": "OVERRIDE",
  "reason": "Officer reviewed the submitted clarification and supporting evidence.",
  "comments": "Additional officer remarks."
}
```

Possible decisions:

```text
CONFIRM
CLARIFY
OVERRIDE
```

Response:

```json
{
  "success": true,
  "decisionId": "DEC-001",
  "bidderId": "BID-002",
  "decision": "OVERRIDE",
  "recordedAt": "2026-09-27T10:30:00Z",
  "recordedBy": {
    "id": "USR-001",
    "name": "Procurement Officer"
  }
}
```

The backend should create an audit event whenever this endpoint is called.

---

# 19. Audit Trail API

```http
GET /api/audit
```

Optional filters:

```text
?tenderId=TND-001
&bidderId=BID-001
&type=verification
&page=1
```

Response:

```json
{
  "events": [
    {
      "id": "AUD-001",
      "type": "verification",
      "label": "GST verification completed",
      "actor": "SYSTEM",
      "timestamp": "2026-09-27T10:20:00Z",
      "description": "GST verification returned ACTIVE status.",
      "tenderId": "TND-001",
      "bidderId": "BID-001"
    }
  ]
}
```

Current frontend event types include:

```text
import
security
ocr
extraction
verification
rules
conflict
recommendation
officer
```

The audit page renders these as a chronological vertical timeline. 

---

# 20. Reports API

## List reports

```http
GET /api/reports
```

## Generate report

```http
POST /api/reports
```

Request:

```json
{
  "type": "TENDER_COMPLIANCE",
  "tenderId": "TND-001"
}
```

Possible report types:

```text
TENDER_COMPLIANCE
BIDDER_EVALUATION
RISK_REPORT
VERIFICATION_REPORT
AUDIT_REPORT
```

Response:

```json
{
  "reportId": "REP-001",
  "status": "GENERATING"
}
```

Then:

```http
GET /api/reports/REP-001
```

Response:

```json
{
  "id": "REP-001",
  "status": "READY",
  "downloadUrl": "...",
  "createdAt": "2026-09-27T10:40:00Z"
}
```

The current report UI has predefined report cards and a simulated generation/download flow. Real report generation needs to be implemented by the backend. 

---

# 21. Backend → Frontend Data Flow

The expected architecture is:

```text
                    FRONTEND
                       │
                       │ REST API / JSON
                       ▼
                 BACKEND API
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Database     AI Engine    Rule Engine
          │            │            │
          └────────────┼────────────┘
                       ▼
                 Verification
                  Connectors
                       │
          ┌────────────┼─────────────┐
          ▼            ▼             ▼
         GST          PAN           Udyam
          │            │             │
          └────────────┼─────────────┘
                       ▼
                 Evidence Store
```

The frontend should **not directly communicate with government/external verification services**.

Instead:

```text
Frontend
   ↓
Backend
   ↓
Connector
   ↓
External source
   ↓
Backend
   ↓
Frontend
```

---

# 22. Recommended Backend Modules

The backend can be organized into:

```text
backend/
│
├── auth/
├── users/
│
├── tenders/
├── bidders/
├── documents/
│
├── ocr/
├── extraction/
│
├── verification/
│   ├── gst/
│   ├── pan/
│   ├── udyam/
│   ├── oem/
│   └── blacklist/
│
├── conflicts/
├── rules/
├── recommendations/
├── reviews/
├── audit/
└── reports/
```

---

# 23. Important Frontend/Backend Contract

The backend should **not return only a final score**.

For example, avoid:

```json
{
  "complianceScore": 82
}
```

Instead, return the evidence behind that score:

```json
{
  "complianceScore": 82,
  "rules": [],
  "conflicts": [],
  "verification": [],
  "evidence": []
}
```

The frontend is designed to explain:

```text
WHAT failed?
     ↓
WHICH rule?
     ↓
WHICH tender clause?
     ↓
WHAT evidence?
     ↓
WHICH source?
     ↓
WHAT recommendation?
     ↓
WHAT did the officer decide?
```

This is particularly important for the Recommendation, Conflict, Compliance and Audit pages.

---

# 24. Evidence Object

A common evidence structure is recommended across the backend.

```json
{
  "id": "EVD-001",
  "type": "DOCUMENT",
  "documentId": "DOC-001",
  "field": "GSTIN",
  "value": "29ABCDE1234F1Z5",
  "page": 1,
  "confidence": 98.4,
  "source": "GST_CERTIFICATE",
  "createdAt": "2026-09-27T10:20:00Z"
}
```

This allows the frontend to display:

```text
Evidence
GST Certificate
Page 1
GSTIN: 29ABCDE1234F1Z5
Confidence: 98.4%
```

---

# 25. Connector Response Standard

All verification connectors should preferably return a common structure.

```json
{
  "connector": "GST",
  "mode": "DEMO",
  "status": "VERIFIED",
  "verifiedAt": "2026-09-27T10:20:00Z",
  "fields": {},
  "matches": [],
  "conflicts": [],
  "evidence": []
}
```

This allows the same frontend `ConnectorCard` component to render different verification services.

The current UI already follows this pattern through a connector-card component. 

---

# 26. Status Values

To avoid frontend/backend mismatch, use consistent enums.

## Tender

```text
DRAFT
OPEN
UNDER_EVALUATION
COMPLETED
AWARDED
CANCELLED
```

## Bidder

```text
PROCESSING
READY
REVIEW
CLARIFICATION
HIGH_RISK
REJECTED
```

## Risk

```text
LOW
MEDIUM
HIGH
CRITICAL
NONE
```

## Verification

```text
VERIFIED
CONFLICT
MISSING
ERROR
NOT_APPLICABLE
```

## Compliance

```text
PASS
FAIL
NEEDS_CLARIFICATION
```

## Recommendation

```text
COMPLIANT
HIGH_RISK
NEEDS_CLARIFICATION
```

## Officer Decision

```text
CONFIRM
CLARIFY
OVERRIDE
```

---

# 27. Error Response Format

All backend APIs should preferably return errors consistently.

```json
{
  "success": false,
  "error": {
    "code": "BIDDER_NOT_FOUND",
    "message": "Bidder BID-001 was not found."
  }
}
```

Example HTTP statuses:

```text
200 — Success
201 — Created
400 — Bad request
401 — Unauthorized
403 — Forbidden
404 — Not found
409 — Conflict
422 — Validation error
500 — Internal server error
```

---

# 28. Loading States

The frontend should display loading states while backend requests are running.

Examples:

```text
Loading bidders...
Running GST verification...
Running compliance rules...
Generating recommendation...
Generating report...
```

The current import and report flows already contain simulated loading/progress states that can later be replaced with real backend job status. 

For long-running jobs, preferably use:

```text
POST /api/...
      ↓
jobId
      ↓
GET /api/jobs/{jobId}
```

Example:

```json
{
  "jobId": "JOB-001",
  "status": "PROCESSING",
  "progress": 65
}
```

---

# 29. Authentication Requirements

The backend should provide:

* JWT/session authentication
* Role-based access control
* Token expiration
* Refresh token if required
* Protected routes
* User identity for audit logging

The frontend currently supports:

```text
Procurement Officer
Reviewer
Admin
Auditor
```

but authentication is still mocked. 

---

# 30. CORS / Local Development

During development, the frontend may run at:

```text
http://localhost:3001
```

If the backend runs on:

```text
http://localhost:8000
```

configure CORS for:

```text
http://localhost:3001
```

Example:

```text
Frontend
localhost:3001
      │
      │ API requests
      ▼
Backend
localhost:8000
```

The exact backend port can be changed according to the team's setup.

---

# 31. Environment Variables

The frontend should eventually use:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

Then API calls can use:

```ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;
```

For production:

```env
NEXT_PUBLIC_API_URL=https://api.example.com/api
```

Do **not** put secret API keys in `NEXT_PUBLIC_*` variables.

---

# 32. Replacing Mock Data

Currently pages directly consume:

```text
src/lib/mockData.ts
```

The recommended migration is:

### Current

```text
Page
 ↓
mockData.ts
 ↓
UI
```

### Final

```text
Page
 ↓
API service
 ↓
Backend
 ↓
Database / AI / Rules / Connectors
```

A clean frontend structure would eventually be:

```text
src/
├── app/
├── components/
├── lib/
│   ├── api/
│   │   ├── auth.ts
│   │   ├── tenders.ts
│   │   ├── bidders.ts
│   │   ├── documents.ts
│   │   ├── verification.ts
│   │   ├── compliance.ts
│   │   ├── recommendations.ts
│   │   ├── reviews.ts
│   │   ├── audit.ts
│   │   └── reports.ts
│   │
│   └── types/
│       └── index.ts
```

---

# 33. Suggested Integration Order

Backend integration should happen in this order:

### Phase 1 — Authentication

```text
/login
      ↓
POST /auth/login
```

### Phase 2 — Tenders

```text
Dashboard
Tenders
Tender Import
```

### Phase 3 — Bidders

```text
Bidder List
Bidder Profile
```

### Phase 4 — Documents

```text
Documents
OCR
Extraction
Evidence
```

### Phase 5 — Verification

```text
GST
PAN
Udyam
OEM
Blacklist
```

### Phase 6 — Rules

```text
Compliance
Conflicts
```

### Phase 7 — AI

```text
Recommendation
```

### Phase 8 — Human Decision

```text
Officer Review
```

### Phase 9 — Audit

```text
Audit Trail
```

### Phase 10 — Reports

```text
Reports
PDF / CSV
```

---

# 34. What Is Currently Mocked?

The following are **not yet real backend functionality**:

* Authentication
* Government/external verification
* OCR
* Document processing
* Compliance rule execution
* Conflict detection
* AI recommendation
* Audit persistence
* Report generation
* PDF generation
* CSV export

The prototype currently uses mock data for connectors, accepts any login credentials, uses a placeholder document viewer and simulates report generation. 

---

# 35. What the Backend Developer Should NOT Change

Unless necessary, don't change:

```text
Route names
Bidder ID structure
Navigation structure
UI component names
Status concepts
Evidence presentation
Officer review workflow
```

If the backend API uses different names, map them in the frontend API layer rather than changing every page.

For example:

```text
Backend:
risk_status

Frontend:
riskLevel
```

can be mapped in:

```text
src/lib/api/
```

rather than modifying every component.

---

# 36. Frontend Integration Principle

The frontend should remain responsible for:

```text
UI
Navigation
Forms
Loading states
Error display
Visualization
User interaction
Officer decision input
```

The backend should be responsible for:

```text
Authentication
Authorization
Database
Tender processing
Document storage
OCR
Data extraction
External verification
Conflict detection
Rule execution
AI recommendation
Audit persistence
Report generation
```

---

# 37. Current Prototype Validation

The current frontend was verified with:

```bash
npx tsc --noEmit
```

with zero TypeScript errors, and the Next.js development server compiled successfully. The implemented dynamic bidder routes were tested for the prototype bidder IDs. 

---

# 38. Quick Integration Checklist

Backend developer should eventually provide:

```text
[ ] POST /auth/login
[ ] GET  /dashboard

[ ] GET  /tenders
[ ] GET  /tenders/{id}
[ ] POST /tenders/import

[ ] GET  /tenders/{id}/bidders
[ ] GET  /bidders/{id}

[ ] GET  /bidders/{id}/documents
[ ] GET  /documents/{id}/extractions

[ ] GET  /bidders/{id}/verification
[ ] GET  /bidders/{id}/conflicts
[ ] GET  /bidders/{id}/compliance

[ ] GET  /bidders/{id}/recommendation
[ ] POST /bidders/{id}/review

[ ] GET  /audit

[ ] GET  /reports
[ ] POST /reports
[ ] GET  /reports/{id}
```

Once these APIs are available, the frontend can progressively replace `mockData.ts` with real API responses.

---

# 39. Final Architecture

The intended end-to-end system is:

```text
                         ComplianceOS
                              │
             ┌────────────────┴────────────────┐
             │                                 │
        Next.js Frontend                  Backend API
             │                                 │
       ┌─────┼──────┐             ┌───────────┼───────────┐
       │     │      │             │           │           │
    Tenders Bidders Reports     Database    AI Engine   Rule Engine
       │     │      │             │           │           │
       │     │      │             └───────────┼───────────┘
       │     │      │                         │
       │     │      │                    Verification
       │     │      │                         │
       │     │      │              ┌──────────┼──────────┐
       │     │      │              │          │          │
       │     │      │             GST        PAN       Udyam
       │     │      │
       └─────┴──────┴────────────── Evidence + Audit
```

The frontend is therefore primarily an **evidence-driven officer interface**. It should receive structured results from the backend rather than implementing verification/business logic itself.

---

## Important note for the backend developer

**Do not treat the current `mockData.ts` values as the final database schema.** They exist to demonstrate the UI and workflow. The backend should provide production API responses following the concepts above, while the frontend maps those responses into the existing UI.

The most important integration requirement is maintaining the chain:

```text
Tender Clause
      ↓
Rule
      ↓
Evidence
      ↓
Verification
      ↓
Conflict
      ↓
Compliance Result
      ↓
AI Recommendation
      ↓
Officer Decision
      ↓
Audit Event
```

That chain is what makes the frontend useful as a procurement **decision-support and auditability system**, rather than simply displaying an AI-generated risk score.
