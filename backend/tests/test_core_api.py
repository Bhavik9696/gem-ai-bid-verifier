import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app




def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["port"] == 8000


def test_list_tenders_and_detail(client: TestClient):
    res_list = client.get("/api/tenders")
    assert res_list.status_code == 200
    tenders = res_list.json()
    assert len(tenders) >= 1
    tender_id = tenders[0]["tenderId"]

    res_detail = client.get(f"/api/tenders/{tender_id}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["tenderId"] == tender_id
    assert "mandatoryDocuments" in detail
    assert "eligibilityConditions" in detail


def test_list_tender_bids(client: TestClient):
    res_list = client.get("/api/tenders")
    tender_id = res_list.json()[0]["tenderId"]

    res_bids = client.get(f"/api/tenders/{tender_id}/bids")
    assert res_bids.status_code == 200
    bids = res_bids.json()
    assert len(bids) == 3
    bid_ids = [b["bidId"] for b in bids]
    assert "GEM-BID-2026-001" in bid_ids
    assert "GEM-BID-2026-002" in bid_ids
    assert "GEM-BID-2026-003" in bid_ids


def test_verify_aster_tech_compliant(client: TestClient):
    res = client.post("/api/bids/GEM-BID-2026-001/run-verification")
    assert res.status_code == 200
    data = res.json()
    assert data["bidId"] == "GEM-BID-2026-001"
    assert data["riskLevel"] == "LOW"
    assert "Ready for Officer Confirmation" in data["recommendation"]
    assert len(data["findings"]) == 0
    assert data["complianceScore"] >= 90.0


def test_verify_bharat_supplies_name_conflict(client: TestClient):
    res = client.post("/api/bids/GEM-BID-2026-002/run-verification")
    assert res.status_code == 200
    data = res.json()
    assert data["bidId"] == "GEM-BID-2026-002"
    assert data["riskLevel"] == "HIGH"
    assert "Officer Review Required" in data["recommendation"]
    finding_types = [f["findingType"] for f in data["findings"]]
    assert "ENTITY_NAME_MISMATCH" in finding_types


def test_verify_crest_systems_missing_expired(client: TestClient):
    res = client.post("/api/bids/GEM-BID-2026-003/run-verification")
    assert res.status_code == 200
    data = res.json()
    assert data["bidId"] == "GEM-BID-2026-003"
    assert "Needs Clarification" in data["recommendation"]
    finding_types = [f["findingType"] for f in data["findings"]]
    assert "EXPIRED_OEM_AUTHORISATION" in finding_types
    assert "MISSING_UDYAM_CERTIFICATE" in finding_types


def test_officer_decision_and_audit_timeline(client: TestClient):
    # Confirm on compliant bid
    res_confirm = client.post(
        "/api/bids/GEM-BID-2026-001/decision",
        json={
            "decision": "CONFIRM",
            "notes": "Verified all documents and statutory records.",
            "officerId": "OFFICER-TEST",
        },
    )
    assert res_confirm.status_code == 200
    assert res_confirm.json()["bidStatus"] == "CONFIRMED"

    # Override on high-risk bid with reason
    res_override = client.post(
        "/api/bids/GEM-BID-2026-002/decision",
        json={
            "decision": "OVERRIDE",
            "reason": "Name discrepancy resolved via gazette notification amendment.",
            "notes": "Original certificate physically reviewed.",
            "officerId": "OFFICER-TEST",
        },
    )
    assert res_override.status_code == 200
    assert res_override.json()["bidStatus"] == "OVERRIDDEN"

    # Audit events
    res_audit = client.get("/api/bids/GEM-BID-2026-001/audit-events")
    assert res_audit.status_code == 200
    events = res_audit.json()
    event_types = [e["eventType"] for e in events]
    assert "BID_INGESTED" in event_types
    assert "VERIFICATION_TRIGGERED" in event_types
    assert "OFFICER_DECISION_RECORDED" in event_types
