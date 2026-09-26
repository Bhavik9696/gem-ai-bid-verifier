"""
Tests for identifier format validation (validators.py).

Invalid formats must return HTTP 422 with:
  - error code in detail.error
  - human-readable message in detail.message
  - example of a valid format
"""

import pytest
from fastapi.testclient import TestClient
from app.main import create_app

app = create_app()
client = TestClient(app)


class TestGSTINValidation:
    def test_too_short_gstin_422(self):
        resp = client.get("/api/v1/gst/123")
        assert resp.status_code == 422
        assert resp.json()["detail"]["error"] == "INVALID_GSTIN_FORMAT"

    def test_too_long_gstin_422(self):
        resp = client.get("/api/v1/gst/33AABCA1234F1Z5EXTRA")
        assert resp.status_code == 422

    def test_lowercase_gstin_still_validated(self):
        # Lowercase is normalised to upper; a valid GSTIN in lower should work
        resp = client.get("/api/v1/gst/33aabca1234f1z5")
        assert resp.status_code == 200

    def test_clearly_invalid_gstin_422(self):
        resp = client.get("/api/v1/gst/INVALID-GSTIN")
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert "INVALID_GSTIN_FORMAT" in detail["error"]
        assert "Example" in detail["message"]

    def test_valid_unknown_gstin_not_found(self):
        # Correct format but not in demo data → 200 NOT_FOUND
        resp = client.get("/api/v1/gst/27AABCA1234F1Z5")
        assert resp.status_code == 200
        assert resp.json()["status"] == "NOT_FOUND"


class TestPANValidation:
    def test_too_short_pan_422(self):
        resp = client.get("/api/v1/pan/ABC")
        assert resp.status_code == 422
        assert resp.json()["detail"]["error"] == "INVALID_PAN_FORMAT"

    def test_numeric_only_pan_422(self):
        resp = client.get("/api/v1/pan/1234567890")
        assert resp.status_code == 422

    def test_lowercase_pan_normalised(self):
        resp = client.get("/api/v1/pan/aabca1234f")
        assert resp.status_code == 200  # normalised → valid lookup

    def test_clearly_invalid_pan_422(self):
        resp = client.get("/api/v1/pan/INVALID-PAN")
        assert resp.status_code == 422
        assert "Example" in resp.json()["detail"]["message"]

    def test_valid_unknown_pan_not_found(self):
        resp = client.get("/api/v1/pan/ZZZZZ0000Z")
        assert resp.status_code == 200
        assert resp.json()["status"] == "NOT_FOUND"

    def test_blacklist_invalid_pan_422(self):
        resp = client.get("/api/v1/blacklist?pan=BADPAN")
        assert resp.status_code == 422
        assert resp.json()["detail"]["error"] == "INVALID_PAN_FORMAT"


class TestUdyamValidation:
    def test_missing_prefix_422(self):
        resp = client.get("/api/v1/udyam/TN-01-0001234")
        assert resp.status_code == 422
        assert "INVALID_UDYAM_FORMAT" in resp.json()["detail"]["error"]

    def test_wrong_separator_422(self):
        # Slashes in path would be routed differently by FastAPI; use a
        # different invalid format that stays as a single path segment.
        resp = client.get("/api/v1/udyam/UDYAM_TN_01_0001234")
        assert resp.status_code == 422

    def test_valid_unknown_udyam_not_found(self):
        resp = client.get("/api/v1/udyam/UDYAM-MH-05-0009999")
        assert resp.status_code == 200
        assert resp.json()["status"] == "NOT_FOUND"


class TestCINValidation:
    def test_invalid_cin_422(self):
        resp = client.get("/api/v1/mca/INVALIDCIN")
        assert resp.status_code == 422
        assert "INVALID_CIN_FORMAT" in resp.json()["detail"]["error"]

    def test_valid_unknown_cin_not_found(self):
        resp = client.get("/api/v1/mca/U99900MH2020PTC999999")
        assert resp.status_code == 200
        assert resp.json()["status"] == "NOT_FOUND"


class TestOEMRefValidation:
    def test_too_short_ref_422(self):
        resp = client.get("/api/v1/oem/AB")
        assert resp.status_code == 422
        assert "INVALID_OEM_REFERENCE" in resp.json()["detail"]["error"]

    def test_valid_unknown_oem_not_found(self):
        resp = client.get("/api/v1/oem/OEM-UNKNOWN-BRAND-2024-999")
        assert resp.status_code == 200
        assert resp.json()["status"] == "NOT_FOUND"
