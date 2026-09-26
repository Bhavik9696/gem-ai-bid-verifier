# ComplianceOS — Connector Service (Member 6)

> Dynamic demo source connectors for the ComplianceOS prototype.  
> Port **8001** · FastAPI + Python · Owner: **Member 6**

---

## What this service does

The connector service acts as the **source-integration boundary**. It behaves exactly like a production API gateway would, except that it searches small controlled source datasets instead of calling live government portals.

Every response carries `"mode": "DEMO"` so prototype data is never mistaken for a live government result.

```
Core API (port 8000)
        │
        ▼
Connector Service (port 8001)   ← this service
        │
        ▼
backend/demo-data/*.json        ← seed source records
```

---

## Endpoints

| Endpoint | Source simulated |
|----------|-----------------|
| `GET /health` | — |
| `GET /api/v1/gst/{gstin}` | GSTN / GST portal |
| `GET /api/v1/pan/{pan}` | Income Tax / PAN database |
| `GET /api/v1/udyam/{udyamNumber}` | Udyam/MSME portal |
| `GET /api/v1/mca/{cin}` | MCA21 company registry |
| `GET /api/v1/oem/{authorisationNumber}` | OEM issuer records |
| `GET /api/v1/digilocker/{documentId}` | DigiLocker issuer verification |
| `GET /api/v1/blacklist?pan={pan}` | Debarment/blacklist registry |
| `GET /api/v1/statutory/{source}/{identifier}` | EPFO / ESIC / NSIC / Startup India |

Interactive docs: **http://localhost:8001/docs**

---

## Demo bidder scenarios

| Bidder | Connector result | Expected outcome |
|--------|-----------------|-----------------|
| Aster Tech Pvt Ltd | All VERIFIED | Compliant / Low Risk |
| Bharat Supplies Pvt Ltd | GST + PAN → MISMATCH | High Risk / Officer Review |
| Crest Systems Pvt Ltd | Udyam NOT_FOUND · OEM EXPIRED | Needs Clarification |

---

## Running locally

```bash
# From repo root
cd connector-service
pip install -r requirements.txt
uvicorn run:app --reload --port 8001
```

Or via Docker Compose (from repo root):

```bash
docker compose up connector-service
```

---

## Running tests

```bash
cd connector-service
pip install -r requirements.txt
pytest tests/ -v
```

Expected: **30+ tests passing**, all with `mode=DEMO`.

---

## File structure

```
connector-service/
├── run.py                    # Uvicorn entry point (port 8001)
├── Dockerfile
├── requirements.txt
├── pytest.ini
├── app/
│   ├── main.py               # FastAPI app factory + router registration
│   ├── data/
│   │   └── loader.py         # Reads backend/demo-data/*.json; dynamic lookups
│   ├── schemas/
│   │   └── connector.py      # Standard ConnectorResponse Pydantic model
│   └── api/v1/
│       ├── health.py
│       ├── gst.py
│       ├── pan.py
│       ├── udyam.py
│       ├── mca.py
│       ├── oem.py
│       ├── digilocker.py
│       ├── blacklist.py
│       └── statutory.py
└── tests/
    └── test_connectors.py    # Full test suite — all 3 bidder scenarios
```

---

## Demo data (backend/demo-data/)

| File | Contents |
|------|----------|
| `tender.json` | Single demo tender (GeM IT Equipment supply) |
| `bidders.json` | Three bidder profiles with PAN/GSTIN/Udyam/CIN |
| `gem-bids.json` | Bid submissions linking bidders to the tender |
| `gst-records.json` | GST source records (Bharat has name mismatch) |
| `pan-records.json` | PAN/IT records |
| `udyam-records.json` | Udyam records (Crest Systems absent) |
| `mca-records.json` | MCA21 company records |
| `oem-authorisations.json` | OEM letters (Crest's letter expired 2025-05-09) |
| `digilocker-records.json` | DigiLocker-ready document origin records |
| `statutory-records.json` | EPFO / ESIC / NSIC / Startup India records |
| `blacklist-records.json` | Debarment registry (demo bidders are clean) |

---

## Handoff to Member 3

To integrate the connector service into the Core API orchestrator, call:

```python
import httpx

CONNECTOR_BASE = "http://localhost:8001"  # or http://connector-service:8001 in Docker

async def verify_gst(gstin: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CONNECTOR_BASE}/api/v1/gst/{gstin}")
        return resp.json()
```

Expected response fields: `source`, `mode`, `identifier`, `status`, `verifiedFacts`, `checkedAt`, `evidenceReference`.

`status` values: `VERIFIED` · `NOT_FOUND` · `MISMATCH` · `EXPIRED` · `BLACKLISTED` · `NOT_APPLICABLE`
