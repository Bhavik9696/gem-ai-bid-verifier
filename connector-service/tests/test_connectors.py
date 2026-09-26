"""
Tests for the ComplianceOS Demo Connector Service.

Run from the connector-service/ directory:
    pytest tests/ -v

Coverage:
  - All three bidder scenarios (compliant, name-conflict, missing/expired)
  - Health endpoint
  - Known-identifier lookups (VERIFIED / MISMATCH / EXPIRED)
  - Unknown-identifier lookups (NOT_FOUND)
  - Blacklist clean and blacklisted cases
  - Statutory known/unknown lookups
  - mode=DEMO enforced on every response
"""

import pytest
from fastapi.testclient import TestClient
from app.main import create_app

app = create_app()
client = TestClient(app)


# ── Helpers ────────────────────────────────────────────────────────────────────

def assert_demo_envelope(data: dict, expected_status: str | None = None):
    """Assert the standard connector envelope contract."""
    assert data["mode"] == "DEMO", "mode must always be DEMO"
    assert "source" in data
    assert "identifier" in data
    assert "status" in data
    assert "verifiedFacts" in data
    assert "checkedAt" in data
    assert "evidenceReference" in data
    if expected_status:
        assert data["status"] == expected_status, (
            f"Expected status={expected_status}, got {data['status']}"
        )


# ── Health ─────────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["mode"] == "DEMO"
        assert data["port"] == 8001


# ── GST Connector ──────────────────────────────────────────────────────────────

class TestGSTConnector:
    # Bidder 1 — Aster Tech — ACTIVE GST, no conflict → VERIFIED
    def test_aster_tech_gst_verified(self):
        resp = client.get("/api/v1/gst/33AABCA1234F1Z5")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "VERIFIED")
        assert data["verifiedFacts"]["legalName"] == "Aster Tech Private Limited"
        assert data["verifiedFacts"]["gstStatus"] == "ACTIVE"
        assert data["source"] == "GST_DEMO"

    # Bidder 2 — Bharat Supplies — GST name ≠ bid name → MISMATCH
    def test_bharat_supplies_gst_name_mismatch(self):
        resp = client.get("/api/v1/gst/07AADCB5432G1ZK")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "MISMATCH")
        # GST record has different legal name than bid entity
        assert "Bharat Enterprises" in data["verifiedFacts"]["legalName"]

    # Bidder 3 — Crest Systems — GST active → VERIFIED
    def test_crest_systems_gst_verified(self):
        resp = client.get("/api/v1/gst/29AAHCC7891H1ZT")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "VERIFIED")
        assert data["verifiedFacts"]["gstStatus"] == "ACTIVE"

    # Unknown GSTIN → NOT_FOUND
    def test_unknown_gstin_not_found(self):
        resp = client.get("/api/v1/gst/99ZZZZZ9999Z9Z9")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "NOT_FOUND")
        assert data["verifiedFacts"] == {}


# ── PAN Connector ──────────────────────────────────────────────────────────────

class TestPANConnector:
    def test_aster_tech_pan_verified(self):
        resp = client.get("/api/v1/pan/AABCA1234F")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "VERIFIED")
        assert "Aster Tech" in data["verifiedFacts"]["entityName"]

    def test_bharat_supplies_pan_mismatch(self):
        resp = client.get("/api/v1/pan/AADCB5432G")
        assert resp.status_code == 200
        data = resp.json()
        # PAN name differs from GST name — surfaced as MISMATCH
        assert_demo_envelope(data, "MISMATCH")

    def test_unknown_pan_not_found(self):
        resp = client.get("/api/v1/pan/ZZZZZ9999Z")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "NOT_FOUND")


# ── Udyam Connector ────────────────────────────────────────────────────────────

class TestUdyamConnector:
    def test_aster_tech_udyam_verified(self):
        resp = client.get("/api/v1/udyam/UDYAM-TN-01-0001234")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "VERIFIED")
        assert data["verifiedFacts"]["udyamStatus"] == "ACTIVE"

    def test_bharat_supplies_udyam_verified(self):
        resp = client.get("/api/v1/udyam/UDYAM-DL-02-0005678")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "VERIFIED")

    # Crest Systems has NO Udyam number — querying any unknown number → NOT_FOUND
    def test_crest_systems_udyam_missing(self):
        resp = client.get("/api/v1/udyam/UDYAM-KA-03-UNKNOWN")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "NOT_FOUND")


# ── MCA Connector ──────────────────────────────────────────────────────────────

class TestMCAConnector:
    def test_aster_tech_cin_verified(self):
        resp = client.get("/api/v1/mca/U72900TN2018PTC122345")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "VERIFIED")
        assert data["verifiedFacts"]["companyStatus"] == "ACTIVE"

    def test_crest_systems_cin_verified(self):
        resp = client.get("/api/v1/mca/U72200KA2020PTC135678")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "VERIFIED")

    def test_unknown_cin_not_found(self):
        resp = client.get("/api/v1/mca/U99999XX9999XXX999999")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "NOT_FOUND")


# ── OEM Connector ──────────────────────────────────────────────────────────────

class TestOEMConnector:
    # Aster Tech — valid OEM letter → VERIFIED
    def test_aster_tech_oem_valid(self):
        resp = client.get("/api/v1/oem/OEM-DELL-ASTER-2024-001")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "VERIFIED")
        assert data["verifiedFacts"]["oemStatus"] == "VALID"

    # Crest Systems — expired OEM letter → EXPIRED
    def test_crest_systems_oem_expired(self):
        resp = client.get("/api/v1/oem/OEM-LENOVO-CREST-2022-009")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "EXPIRED")
        assert data["verifiedFacts"]["oemStatus"] == "EXPIRED"
        assert data["verifiedFacts"]["expiryDate"] == "2025-05-09"

    def test_unknown_oem_not_found(self):
        resp = client.get("/api/v1/oem/OEM-UNKNOWN-9999")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "NOT_FOUND")


# ── DigiLocker Connector ───────────────────────────────────────────────────────

class TestDigiLockerConnector:
    def test_aster_gst_digilocker_verified(self):
        resp = client.get("/api/v1/digilocker/DL-ASTER-GST-2024-001")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "VERIFIED")
        assert data["verifiedFacts"]["digilockerReady"] is True

    def test_bharat_gst_digilocker_name_mismatch(self):
        resp = client.get("/api/v1/digilocker/DL-BHARAT-GST-2015-002")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "MISMATCH")
        assert "conflictNote" in data["verifiedFacts"]

    def test_unknown_document_not_found(self):
        resp = client.get("/api/v1/digilocker/DL-UNKNOWN-9999")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "NOT_FOUND")


# ── Blacklist Connector ────────────────────────────────────────────────────────

class TestBlacklistConnector:
    # All three demo bidders are clean
    def test_aster_tech_not_blacklisted(self):
        resp = client.get("/api/v1/blacklist?pan=AABCA1234F")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "VERIFIED")
        assert data["verifiedFacts"]["blacklisted"] is False

    def test_bharat_supplies_not_blacklisted(self):
        resp = client.get("/api/v1/blacklist?pan=AADCB5432G")
        assert resp.status_code == 200
        data = resp.json()
        assert data["verifiedFacts"]["blacklisted"] is False

    def test_crest_systems_not_blacklisted(self):
        resp = client.get("/api/v1/blacklist?pan=AAHCC7891H")
        assert resp.status_code == 200
        data = resp.json()
        assert data["verifiedFacts"]["blacklisted"] is False

    # Fictional blacklisted PAN to test BLACKLISTED flow
    def test_blacklisted_entity_detected(self):
        resp = client.get("/api/v1/blacklist?pan=AAZBD9999X")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "BLACKLISTED")
        assert data["verifiedFacts"]["blacklisted"] is True
        assert data["verifiedFacts"]["listType"] == "DEBARRED"


# ── Statutory Connector ────────────────────────────────────────────────────────

class TestStatutoryConnector:
    def test_aster_epfo_compliant(self):
        resp = client.get("/api/v1/statutory/EPFO/AABCA1234F")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "VERIFIED")

    def test_aster_startup_india_not_applicable(self):
        resp = client.get("/api/v1/statutory/STARTUP_INDIA/AABCA1234F")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "NOT_APPLICABLE")

    def test_bharat_nsic_registered(self):
        resp = client.get("/api/v1/statutory/NSIC/AADCB5432G")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "VERIFIED")

    def test_unknown_statutory_not_found(self):
        resp = client.get("/api/v1/statutory/EPFO/ZZZZZ9999Z")
        assert resp.status_code == 200
        data = resp.json()
        assert_demo_envelope(data, "NOT_FOUND")


# ── Mode enforcement ───────────────────────────────────────────────────────────

class TestModeEnforcement:
    """Every endpoint must return mode=DEMO. Never LIVE."""

    ENDPOINTS = [
        "/api/v1/gst/33AABCA1234F1Z5",
        "/api/v1/pan/AABCA1234F",
        "/api/v1/udyam/UDYAM-TN-01-0001234",
        "/api/v1/mca/U72900TN2018PTC122345",
        "/api/v1/oem/OEM-DELL-ASTER-2024-001",
        "/api/v1/digilocker/DL-ASTER-GST-2024-001",
        "/api/v1/blacklist?pan=AABCA1234F",
        "/api/v1/statutory/EPFO/AABCA1234F",
    ]

    @pytest.mark.parametrize("endpoint", ENDPOINTS)
    def test_all_endpoints_return_demo_mode(self, endpoint):
        resp = client.get(endpoint)
        assert resp.status_code == 200
        assert resp.json()["mode"] == "DEMO", (
            f"Endpoint {endpoint} returned non-DEMO mode"
        )
