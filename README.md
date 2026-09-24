# ComplianceOS for GeM

> AI-powered bid compliance verification and decision-support platform for GeM procurement.

ComplianceOS helps Procurement Officers verify bidder eligibility and statutory compliance faster. It imports tender and bidder data, extracts information from submitted documents, verifies it through source connectors, detects conflicts, evaluates tender-specific rules, and produces an evidence-backed recommendation.

The platform is designed as a **decision-support system**. It does not silently qualify or disqualify a bidder—the final decision remains with the Procurement Officer.

---

## Problem Statement

Government procurement through the Government e-Marketplace (GeM) requires Procurement Officers to verify statutory, regulatory, and tender-specific eligibility requirements for every bidder. These checks may include:

- Udyam/MSME registration
- GST registration and return filing status
- PAN and Income Tax compliance
- MCA21/CIN/company details
- Make in India/local-content declarations
- EPFO/ESIC compliance
- Startup India and NSIC registration
- OEM authorisation
- DigiLocker/issuer document verification
- BIS/DPIIT and other applicable registrations
- Blacklisting/debarment status
- Tender-specific eligibility conditions

The existing process is document-intensive. Officers must read many PDFs, cross-check data across different portals, identify inconsistencies, and maintain an audit-ready evaluation record. This takes time, causes avoidable errors, and delays tender evaluation.

---

## Our Solution

ComplianceOS is an **Officer Compliance Dashboard integrated with GeM data**.

It does not replace GeM or create another seller/bidder marketplace. GeM already handles bidder registration, tender publication, bid submission, and procurement transactions. ComplianceOS acts as an intelligent verification layer after bidder submissions are available.

```text
GeM tender data + bidder details + bid documents
                         ↓
              ComplianceOS verification engine
                         ↓
Compliance, risk, evidence, missing items, and recommendation
                         ↓
       Procurement Officer reviews and confirms decision
```

### Core objective

> Convert bidder documents and distributed verification data into a repeatable, evidence-backed compliance assessment for a specific tender.

---

## Six-Day Prototype Scope

This repository targets a focused SIH prototype. We are building the high-value verification workflow, not the full production ecosystem.

### We will build

- GeM-style tender and bidder-data import.
- Bidder-document upload/import.
- OCR, document classification, and structured field extraction.
- Dynamic demo connectors for statutory/government data sources.
- Entity matching and conflict detection.
- Tender-specific rules engine.
- Compliance score and risk score.
- AI-assisted recommendation with evidence.
- Procurement Officer dashboard.
- Officer review/clarification/override actions.
- Complete audit timeline.

### We will not build

- New bidder signup or seller registration.
- A full GeM marketplace.
- Tender publication, bidding, payments, or order processing.
- Live integration with every government portal.
- CAPTCHA/OTP bypassing or portal scraping.
- A generic chatbot as the main feature.
- Enterprise production deployment, SSO, or full-scale microservices.

---

## End-to-End Workflow

```text
1. Procurement Officer selects/imports a GeM tender
        ↓
2. System imports bidder details and submitted documents
        ↓
3. OCR/AI extracts PAN, GSTIN, Udyam number, company name,
   CIN, dates, OEM details, and local-content information
        ↓
4. Verification engine calls relevant source connectors
        ↓
5. System compares submitted facts with source facts
        ↓
6. Conflict engine flags missing, expired, mismatched, or suspicious data
        ↓
7. Rules engine applies tender-specific eligibility conditions
        ↓
8. System calculates compliance score and risk level
        ↓
9. Dashboard displays evidence and recommendation
        ↓
10. Officer confirms, seeks clarification, or overrides with a reason
        ↓
11. Audit trail and compliance report are stored
```

---

## Main Architecture

```text
┌───────────────────────────────────────────────────────────────────────┐
│                         GeM DATA IMPORT                                │
│                                                                       │
│  Demo GeM tender data      Demo bidder data      Bidder documents     │
│  • Tender conditions       • Company details     • GST certificate    │
│  • Closing date            • PAN/GSTIN           • Udyam certificate  │
│  • Eligibility criteria    • Udyam/CIN           • PAN/OEM letter     │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│                    COMPLIANCEOS CORE PLATFORM                          │
│                                                                       │
│  ┌───────────────────┐     ┌──────────────────────────────────────┐ │
│  │ Tender Rulebook   │     │ Document Intelligence                 │ │
│  │ • Tender clauses  │     │ • OCR                                │ │
│  │ • Eligibility     │     │ • Document classification            │ │
│  │ • Mandatory rules │     │ • PAN/GSTIN/Udyam extraction         │ │
│  └─────────┬─────────┘     │ • Date/OEM/entity extraction         │ │
│            │               └────────────────┬─────────────────────┘ │
│            └────────────────┬───────────────┘                        │
│                             ▼                                        │
│                 ┌─────────────────────────┐                          │
│                 │ Verification Orchestrator│                          │
│                 │ Routes checks using IDs  │                          │
│                 └────────────┬────────────┘                          │
└──────────────────────────────┼────────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────────┐
│                      SOURCE CONNECTOR LAYER                            │
│                                                                       │
│ GST │ PAN/IT │ Udyam/MSME │ MCA/CIN │ OEM │ DigiLocker-ready         │
│ Startup/NSIC/EPFO/ESIC/BIS/DPIIT │ Make in India │ Blacklist           │
│                                                                       │
│ Every connector may operate in: Live / Sandbox / Demo / Manual mode  │
└──────────────────────────────┬────────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────────┐
│                 COMPLIANCE AND DECISION-SUPPORT LAYER                 │
│                                                                       │
│ Entity Matching      Conflict Detection        Rules Engine           │
│ • PAN ↔ GSTIN        • Name mismatch           • Mandatory gates      │
│ • Udyam ↔ PAN        • Cancelled GST            • Tender conditions   │
│ • CIN/company match  • Expired OEM letter       • Eligibility checks  │
│                      • Missing certificate                              │
│                                                                       │
│ Compliance Score + Risk Level + Evidence-backed Recommendation        │
└──────────────────────────────┬────────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────────┐
│                      PROCUREMENT OFFICER DASHBOARD                    │
│ Bidder results │ Risk │ Missing items │ Evidence │ Review │ Audit log │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Dynamic Demo Connector Design

The prototype uses small controlled datasets, but the platform workflow is dynamic. We do **not** hardcode outcomes such as `Bidder A = compliant`.

```text
Uploaded bidder document
        ↓
Extract identifier (GSTIN/PAN/Udyam/CIN)
        ↓
Call matching connector using extracted identifier
        ↓
Connector searches source data and returns a verification result
        ↓
Compare source data with bid details and extracted document facts
        ↓
Run tender rules
        ↓
Generate pass/fail/clarification result dynamically
```

The connector interface remains the same when the system moves from a demo environment to authorised production APIs.

```text
Prototype:  ComplianceOS → Demo GST API → Local verification dataset
Production: ComplianceOS → Approved GST API → Official GST system
```

### Connector modes

| Mode | Meaning |
|---|---|
| `LIVE` | Approved source/API verification. |
| `SANDBOX` | Official test environment response. |
| `DEMO` | Controlled prototype dataset response. |
| `MANUAL` | Officer-led portal verification with attached evidence. |

The dashboard must always show the connector mode. Demo data must never be presented as a live government result.

---

## Demo Dataset

The prototype uses one tender and three bidders. Every source record connects through identifiers such as PAN, GSTIN, Udyam number, CIN, authorisation number, or DigiLocker document ID.

```text
demo-data/
├── tender.json
├── bidders.json
├── gem-bids.json
├── gst-records.json
├── pan-records.json
├── udyam-records.json
├── mca-records.json
├── oem-authorisations.json
├── digilocker-records.json
├── statutory-records.json
├── blacklist-records.json
└── uploaded-documents/
```

### Bidder scenarios

| Bidder | Scenario | Expected result |
|---|---|---|
| Aster Tech Pvt Ltd | PAN, GSTIN, Udyam, CIN, OEM letter, and documents match. | `Compliant` / Low risk |
| Bharat Supplies Pvt Ltd | GST legal name conflicts with bid/PAN company identity. | `High-Risk` / Officer review |
| Crest Systems Pvt Ltd | Udyam missing or OEM authorisation expired. | `Needs Clarification` or non-compliance review |

### Example bidder profile

```json
{
  "bidderId": "BID-001",
  "legalName": "Aster Tech Private Limited",
  "pan": "ABCDE1234F",
  "gstin": "33ABCDE1234F1Z5",
  "udyamNumber": "UDYAM-TN-01-0001234",
  "cin": "U12345TN2022PTC000001",
  "authorisedSignatory": "Arun Kumar"
}
```

### Example GST connector result

```json
{
  "source": "GST_DEMO",
  "mode": "DEMO",
  "gstin": "33ABCDE1234F1Z5",
  "legalName": "Aster Tech Private Limited",
  "status": "ACTIVE",
  "registrationDate": "2022-04-10",
  "returnFilingStatus": "CURRENT",
  "lastReturnPeriod": "2026-08"
}
```

---

## AI Document Intelligence

AI is used to reduce manual reading, not to make an unsupported legal decision.

### Document processing pipeline

```text
Document upload/import
        ↓
File validation + malware scan + hash generation
        ↓
PDF text extraction or OCR
        ↓
Document classification
        ↓
Structured field extraction
        ↓
Normalisation + confidence score + page evidence
        ↓
Automatic processing or officer correction queue
```

### Priority document types

- GST registration certificate
- PAN certificate
- Udyam/MSME certificate
- Company incorporation/CIN document
- OEM authorisation letter
- Make in India/local-content declaration
- Startup India/NSIC certificate
- EPFO/ESIC compliance evidence
- Blacklisting/debarment declaration

### Fields to extract

- PAN, GSTIN, Udyam number, CIN/LLPIN
- Legal and trade name
- Registered address
- Certificate number, issue date, expiry date
- Authorised signatory
- OEM/manufacturer/product relationship
- Local-content percentage

Each important extracted value should include a confidence score and a page reference in the original document.

---

## Verification and Conflict Detection

ComplianceOS normalises records from all sources into one bidder identity profile.

```text
Bidder profile
├── Legal entity name
├── PAN
├── GSTIN
├── Udyam number
├── CIN/LLPIN
├── Registered address
├── Authorised signatory
└── OEM relationship
```

### Conflict examples

| Check | Example finding | Severity |
|---|---|---|
| PAN ↔ GSTIN | GST legal name differs materially from PAN/bid name. | High |
| GST status | GST registration was cancelled before bid close date. | Blocker |
| Udyam ↔ PAN | Udyam certificate belongs to another entity. | Blocker |
| OEM validity | OEM authorisation expired before bid closing date. | High |
| Make in India | Declared local content is below tender threshold. | High/Blocker |
| Completeness | Required certificate was not submitted. | Review/High |
| OCR confidence | Material identifier has low extraction confidence. | Review |

Fuzzy matching may flag possible name mismatches, but only exact/verified identifiers establish identity.

---

## Tender Compliance Rules Engine

Every tender has a versioned, officer-approved rulebook. Rules are deterministic; AI can suggest candidate requirements but does not silently create eligibility decisions.

```yaml
id: GST_ACTIVE_ON_CLOSING_DATE
name: Bidder GST registration must be active
priority: mandatory
source: Tender Clause 4.2, Page 7
conditions:
  - bidder.gstin exists
  - gst.verificationStatus == VERIFIED
  - gst.status == ACTIVE
  - gst.cancellationDate is null OR gst.cancellationDate > tender.bidClosingDate
onPass:
  result: PASS
onFail:
  result: FAIL
  severity: BLOCKER
  recommendation: Officer review required: GST inactive on bid closing date.
```

### Result states

```text
PASS
FAIL
NEEDS_CLARIFICATION
SOURCE_UNAVAILABLE
NOT_APPLICABLE
```

### Mandatory gates before score

```text
Mandatory rule failed
    → High-risk / Officer review required

Required verification unavailable
    → Needs clarification or manual verification

All mandatory rules pass
    → Compliant / Ready for officer confirmation
```

---

## Compliance Score and Risk Level

The compliance score summarises completion. The risk score prioritises what an officer should review first. Neither automatically makes the final legal/procurement decision.

```text
Compliance score = fulfilled weighted applicable requirements
                   / total weighted applicable requirements
```

Suggested weighting:

- Mandatory eligibility: 60%
- Statutory compliance: 25%
- Tender-specific documentation: 15%

Risk factors include:

- Mandatory-rule failures
- Identity conflicts
- Expired documents
- Source verification weakness or outage
- Document-integrity anomalies
- Missing requirements
- Low-confidence OCR

```text
0–24   Low
25–49  Moderate
50–74  High
75–100 Critical
```

---

## Explainable Recommendation

Every result must answer “Why did this pass or fail?”

```text
Status: Failed
Requirement: Active GST registration on bid closing date
Tender source: Clause 4.2, page 7
Bidder submission: GST certificate, page 1
Extracted GSTIN: 33ABCDE1234F1Z5
Verification: GST source reports cancelled on 12 Aug 2026
Bid closing date: 30 Aug 2026
Rule: GST_ACTIVE_ON_CLOSING_DATE v1.0
Recommendation: Seek clarification / officer review required
```

Allowed recommendations:

- `Compliant — Ready for Officer Confirmation`
- `Needs Clarification — Missing or Unverified Evidence`
- `High-Risk — Officer Review Required`

---

## Officer Dashboard

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Tender: Supply of IT Equipment | Closing date: 30 Sep 2026                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Bids: 3 | Ready: 1 | Review: 2 | Critical: 1                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ Bidder             Compliance  Verification  Risk      Status                │
│ Aster Tech         100%        96%           Low       Ready                 │
│ Bharat Supplies    82%         86%           High      Identity conflict     │
│ Crest Systems      74%         72%           Critical  OEM/Udyam issue       │
└─────────────────────────────────────────────────────────────────────────────┘
```

Officer actions:

- Open evidence and source verification record.
- See document-page and tender-clause references.
- Confirm recommendation.
- Request clarification.
- Attach manual verification evidence.
- Override recommendation with a mandatory reason.
- Export evaluation report.

---

## Audit Trail

Every important action is recorded for traceability.

```text
10:02 Bid imported
10:03 Document hash created
10:04 OCR completed
10:05 GSTIN extracted
10:06 GST connector executed
10:06 GST/PAN name mismatch detected
10:08 Rule evaluation completed
10:10 Officer requested clarification
```

Audit events include document version/hash, extraction result, connector source/mode, source result, rule version, model/prompt version, user action, decision, timestamp, and override reason.

---

## Technology Stack

| Area | Technology |
|---|---|
| Frontend | Next.js / React, TypeScript, Tailwind CSS or component library |
| Backend | FastAPI with Python |
| Database | PostgreSQL |
| Object storage | MinIO locally; S3-compatible encrypted storage for production |
| Background jobs | Celery with Redis or RabbitMQ |
| OCR | PaddleOCR or docTR; Tesseract baseline if needed |
| Document extraction | OCR + document-specific JSON schemas + validation |
| Local LLM | Ollama with a Qwen, Llama, Mistral, or Gemma-class instruct model |
| RAG, future extension | pgvector or Qdrant with cited tender/policy retrieval |
| Rules engine | Versioned JSON/YAML rules using JSONLogic, Open Policy Agent, or custom deterministic evaluator |
| Authentication | Role-based JWT for prototype; Keycloak/enterprise IdP-ready design later |
| Deployment | Docker Compose for prototype; containerised/VPC-ready deployment later |
| Observability | Structured logs, job status, metrics, and audit-event dashboard |

### AI policy

AI may classify documents, extract fields, identify likely conflicts, summarize findings, draft clarification questions, and explain evidence.

AI must not invent portal results, bypass verification, silently override rules, or make the final qualification/disqualification decision.

---

## Security and Privacy

Prototype controls:

- Role-based access: Procurement Officer, reviewer, admin, auditor.
- File validation, malware scanning, and quarantine before OCR.
- SHA-256 document hashing.
- Encryption in transit and at rest.
- Short-lived signed URLs for stored files.
- Mask PAN/GSTIN in broad dashboard views.
- Log every verification, review, and decision.
- Treat documents as untrusted input to prevent prompt-injection attacks.
- Never store Aadhaar or OTP data.
- Never scrape sources protected by CAPTCHA, OTP, login, or consent requirements.

---

## Repository Structure

```text
complianceos/
├── frontend/                 # Next.js/React officer dashboard
├── backend/                  # FastAPI APIs and orchestration
│   ├── app/
│   │   ├── api/              # REST endpoints
│   │   ├── models/           # Database models
│   │   ├── services/         # Verification/rules/conflict services
│   │   ├── connectors/       # GST, PAN, Udyam, MCA, OEM, blacklist adapters
│   │   ├── workers/          # OCR and background jobs
│   │   └── rules/            # Versioned compliance rules
├── demo-data/                # Seed tender/bidder/source records
├── uploaded-documents/       # Local demo documents; do not commit real PII
├── docker-compose.yml
└── README.md
```

---

## Development Plan

| Day | Deliverable |
|---|---|
| Day 1 | Project setup, database schema, demo tender/bidder/source data, basic dashboard layout. |
| Day 2 | GeM-style tender/bid import, document storage, bidder profile view. |
| Day 3 | OCR, document classification, PAN/GSTIN/Udyam/date extraction. |
| Day 4 | Dynamic GST, PAN, Udyam, MCA, OEM, and blacklist demo connectors. |
| Day 5 | Conflict detection, rules engine, score/risk calculation, explainable findings. |
| Day 6 | Officer review flow, audit timeline, reports, testing, and demo polish. |

---

## Demo Script

### Case 1: Valid bidder

1. Select tender.
2. Import Aster Tech’s bid.
3. Show document extraction and connector responses.
4. Show all mandatory rules passing.
5. Show `Compliant — Ready for Officer Confirmation`.

### Case 2: Identity conflict

1. Import Bharat Supplies’ bid.
2. Extract PAN/GSTIN/company name.
3. GST connector returns a different legal entity name.
4. Show conflict, failed/flagged rule, evidence, and high risk.
5. Officer requests clarification.

### Case 3: Missing or expired eligibility evidence

1. Import Crest Systems’ bid.
2. Detect missing Udyam certificate or expired OEM authorisation.
3. Show relevant tender clause and evidence.
4. Show `Needs Clarification` or `High-Risk` result.
5. Officer records final action.

---

## Alignment with SIH PS 26100

| Problem statement capability | ComplianceOS implementation |
|---|---|
| Multi-portal integration | Dynamic adapter framework with GST, PAN, Udyam, MCA, OEM, DigiLocker-ready, statutory, and blacklist connectors. |
| GeM integration | GeM-style tender/bidder import connector for prototype; authorised API-ready architecture for production. |
| AI document verification | OCR, document classification, structured extraction, source-page evidence, and cross-verification. |
| Automated compliance engine | Tender-specific, versioned deterministic rules and mandatory gates. |
| Risk and compliance score | Weighted compliance score and explainable risk classification. |
| AI recommendation | Evidence-backed compliant/clarification/high-risk recommendation. |
| Dashboard | Bidder-wise results, evidence, source status, missing items, and officer actions. |
| Audit trail | Immutable-style event timeline of document, connector, rules, review, and decision activity. |
| Human-in-the-loop | Officer approves rules, handles exceptions, and makes final decision. |

---

## Future Production Roadmap

- Authorised GeM API integration.
- Formal DigiLocker/EntityLocker requester onboarding.
- Approved GST, Income Tax/PAN, MCA, Udyam, EPFO, ESIC, Startup India, NSIC, BIS, and DPIIT integrations.
- Digital-signature and QR validation expansion.
- Multi-language OCR/model evaluation.
- RAG assistant over approved tender clauses and policies with citations.
- Enterprise SSO, MFA, VPC deployment, secrets vault, and advanced monitoring.
- Larger blacklisting/debarment and fraud-risk data feeds.
- Scholarship/document-verification domain pack using the same evidence/rules architecture.

---

## Key Principle

> Procurement Officers do not need another chatbot that summarises PDFs. They need a defensible system that shows which condition passed or failed, against which tender clause, based on which document and source result, at what time, and with what confidence.

ComplianceOS delivers that workflow while preserving the Procurement Officer’s final authority.
