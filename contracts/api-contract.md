# ComplianceOS API Contract

**Version:** 1.0  
**Owner:** Member 3 (Core API) · Member 6 (Connector API)

---

## Core API — Port 8000

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/tenders` | List all available tenders |
| GET | `/api/tenders/{tenderId}` | Tender detail + rulebook |
| GET | `/api/tenders/{tenderId}/bids` | All bids for a tender |
| POST | `/api/bids/{bidId}/run-verification` | Trigger end-to-end verification |
| GET | `/api/bids/{bidId}/assessment` | Fetch compliance assessment result |
| POST | `/api/bids/{bidId}/decision` | Record officer decision |
| GET | `/api/bids/{bidId}/audit-events` | Fetch full audit timeline |

### Core Assessment Response (minimum contract)

```json
{
  "bidId": "GEM-BID-2026-001",
  "complianceScore": 92,
  "verificationCoverage": 90,
  "riskLevel": "LOW",
  "recommendation": "Compliant — Ready for Officer Confirmation",
  "ruleResults": [],
  "findings": [],
  "verificationResults": [],
  "auditEvents": []
}
```

---

## Connector API — Port 8001

All responses follow the **standard connector envelope**:

```json
{
  "source":            "GST_DEMO",
  "mode":              "DEMO",
  "identifier":        "<queried identifier>",
  "status":            "VERIFIED | NOT_FOUND | MISMATCH | EXPIRED | BLACKLISTED | SOURCE_UNAVAILABLE | NOT_APPLICABLE",
  "verifiedFacts":     { },
  "checkedAt":         "2026-09-26T14:00:00+00:00",
  "evidenceReference": "demo-data/gst-records.json#<identifier>"
}
```

> **`mode` is always `DEMO` in the prototype.** Never present this as a live government API result.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |
| GET | `/api/v1/gst/{gstin}` | GST registration + status lookup |
| GET | `/api/v1/pan/{pan}` | PAN / Income Tax entity lookup |
| GET | `/api/v1/udyam/{udyamNumber}` | Udyam/MSME registration lookup |
| GET | `/api/v1/mca/{cin}` | MCA21/CIN company details |
| GET | `/api/v1/oem/{authorisationNumber}` | OEM authorisation letter validation |
| GET | `/api/v1/digilocker/{documentId}` | DigiLocker-ready document origin verification |
| GET | `/api/v1/blacklist?pan={pan}` | Blacklist / debarment registry check |
| GET | `/api/v1/statutory/{source}/{identifier}` | Generic statutory check (EPFO/ESIC/NSIC/etc.) |

### Status values

| Status | Meaning |
|--------|---------|
| `VERIFIED` | Identifier found; facts returned; no conflict detected |
| `NOT_FOUND` | Identifier not in demo source data |
| `MISMATCH` | Identifier found but a field conflict exists (e.g. legal name differs) |
| `EXPIRED` | Record found but a date-bound validity has lapsed |
| `BLACKLISTED` | Entity appears on debarment/blacklist registry |
| `SOURCE_UNAVAILABLE` | Source temporarily unavailable (graceful degradation) |
| `NOT_APPLICABLE` | Check not applicable for this entity type |

### Demo bidder scenarios

| Bidder | GSTIN | PAN | Udyam | OEM Ref | Expected result |
|--------|-------|-----|-------|---------|-----------------|
| Aster Tech Pvt Ltd | `33AABCA1234F1Z5` | `AABCA1234F` | `UDYAM-TN-01-0001234` | `OEM-DELL-ASTER-2024-001` | All VERIFIED → **Compliant / Low Risk** |
| Bharat Supplies Pvt Ltd | `07AADCB5432G1ZK` | `AADCB5432G` | `UDYAM-DL-02-0005678` | `OEM-HP-BHARAT-2023-005` | GST/PAN → MISMATCH → **High Risk** |
| Crest Systems Pvt Ltd | `29AAHCC7891H1ZT` | `AAHCC7891H` | *(not registered)* | `OEM-LENOVO-CREST-2022-009` | Udyam NOT_FOUND + OEM EXPIRED → **Needs Clarification** |

### Example: GST response

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

### Example: Blacklist clean

```json
{
  "source": "BLACKLIST_DEMO",
  "mode": "DEMO",
  "identifier": "AABCA1234F",
  "status": "VERIFIED",
  "verifiedFacts": { "blacklisted": false },
  "checkedAt": "2026-09-26T14:00:00+00:00",
  "evidenceReference": "demo-data/blacklist-records.json"
}
```