"""
Phase 2 Tests — Entity Matcher

Tests the entity matching logic for all identity fields:
PAN, GSTIN, Udyam number, CIN, and legal/company name.

Uses reusable fixtures from tests/fixtures/entity_matching.py.
Does not test conflict detection, rule evaluation, scoring,
or recommendation — those belong to subsequent phases.
"""

from __future__ import annotations

import pytest

from backend.app.services.compliance.schemas import (
    BidderProfile,
    ExtractedFact,
    VerificationResult,
    MatchResult,
    MatchType,
)
from backend.app.services.compliance.entity_matcher import match_entities

from backend.app.services.compliance.tests.fixtures.entity_matching import (
    BIDDER_ASTER,
    BIDDER_BHARAT,
    BIDDER_CREST,
    BIDDER_MINIMAL,
    BIDDER_NONE_IDENTIFIERS,
    BIDDER_PROVENANCE,
    FACTS_ASTER,
    FACTS_BHARAT,
    FACTS_CREST,
    FACTS_DIVERGENT_PAN,
    FACTS_MULTI_CONFIDENCE_PAN,
    VERIFICATIONS_ASTER,
    VERIFICATIONS_BHARAT,
    VERIFICATIONS_CREST,
    VERIFICATIONS_MATCH_BIDDER_PAN,
    VERIFICATIONS_MIXED_STATUS,
    VERIFICATION_NOT_FOUND,
    VERIFICATION_ERROR,
    VERIFICATION_PAN_CONFLICT,
)


# ===================================================================
# Helper to find a specific match result by field (and optionally source)
# ===================================================================

def _find_match(
    results: list[MatchResult],
    field: str,
    source: str | None = None,
) -> MatchResult | None:
    """Find a MatchResult by field name and optional source."""
    for r in results:
        if r.field == field:
            if source is None or r.source == source:
                return r
    return None


def _find_all_matches(
    results: list[MatchResult],
    field: str,
) -> list[MatchResult]:
    """Find all MatchResults for a given field."""
    return [r for r in results if r.field == field]


# ===================================================================
# Test 1 — Exact PAN match
# ===================================================================

class TestExactPanMatch:
    """
    When bidder PAN matches the source-verified PAN exactly,
    the result should be EXACT with is_confirmed=True.
    """

    def test_pan_exact_match(self):
        results = match_entities(BIDDER_ASTER, FACTS_ASTER, VERIFICATIONS_ASTER)
        pan_match = _find_match(results, "pan")

        assert pan_match is not None
        assert pan_match.match_type == MatchType.EXACT
        assert pan_match.is_confirmed is True
        assert pan_match.bid_value == "ABCDE1234F"
        assert pan_match.source == "PAN_DEMO"

    def test_pan_values_preserved(self):
        """Bid and source values should be preserved in the result."""
        results = match_entities(BIDDER_ASTER, FACTS_ASTER, VERIFICATIONS_ASTER)
        pan_match = _find_match(results, "pan")

        assert pan_match is not None
        assert pan_match.bid_value is not None
        assert pan_match.source_value is not None


# ===================================================================
# Test 2 — Exact GSTIN match
# ===================================================================

class TestExactGstinMatch:
    """
    When bidder GSTIN matches the source-verified GSTIN exactly,
    the result should be EXACT with is_confirmed=True.
    """

    def test_gstin_exact_match(self):
        results = match_entities(BIDDER_ASTER, FACTS_ASTER, VERIFICATIONS_ASTER)
        gstin_match = _find_match(results, "gstin")

        assert gstin_match is not None
        assert gstin_match.match_type == MatchType.EXACT
        assert gstin_match.is_confirmed is True
        assert gstin_match.bid_value == "33ABCDE1234F1Z5"
        assert gstin_match.source == "GST_DEMO"


# ===================================================================
# Test 3 — Exact Udyam match after normalisation
# ===================================================================

class TestUdyamNormalisedMatch:
    """
    The Udyam number may appear with dashes in the bid ("UDYAM-TN-01-0001234")
    and without in the source ("UDYAMTN010001234"). After normalisation
    they should match exactly.
    """

    def test_udyam_normalised_exact(self):
        results = match_entities(BIDDER_ASTER, FACTS_ASTER, VERIFICATIONS_ASTER)
        udyam_match = _find_match(results, "udyamNumber")

        assert udyam_match is not None
        assert udyam_match.match_type == MatchType.EXACT
        assert udyam_match.is_confirmed is True
        assert udyam_match.source == "UDYAM_DEMO"

    def test_udyam_with_formatting_differences(self):
        """Test Udyam comparison with different formatting."""
        bidder = BidderProfile(
            bidder_id="BID-TEST",
            legal_name="Test Corp",
            udyam_number="UDYAM-KA-02-0005678",
        )
        verifications = [
            VerificationResult(
                source="UDYAM_DEMO",
                mode="DEMO",
                identifier="UDYAMKA020005678",  # no dashes
                status="VERIFIED",
                verified_facts={
                    "udyamNumber": "UDYAMKA020005678",
                    "enterpriseName": "Test Corp",
                    "status": "ACTIVE",
                },
                checked_at="2026-09-25T10:00:00Z",
            ),
        ]
        results = match_entities(bidder, [], verifications)
        udyam_match = _find_match(results, "udyamNumber")

        assert udyam_match is not None
        assert udyam_match.match_type == MatchType.EXACT
        assert udyam_match.is_confirmed is True


# ===================================================================
# Test 4 — Exact CIN match
# ===================================================================

class TestExactCinMatch:
    """
    When bidder CIN matches the source CIN exactly,
    the result should be EXACT with is_confirmed=True.
    """

    def test_cin_exact_match(self):
        results = match_entities(BIDDER_ASTER, FACTS_ASTER, VERIFICATIONS_ASTER)
        cin_match = _find_match(results, "cin")

        assert cin_match is not None
        assert cin_match.match_type == MatchType.EXACT
        assert cin_match.is_confirmed is True
        assert cin_match.bid_value == "U12345TN2022PTC000001"
        assert cin_match.source == "MCA_DEMO"


# ===================================================================
# Test 5 — Normalised legal-name match
# ===================================================================

class TestNormalisedNameMatch:
    """
    "Aster Tech Pvt Ltd" and "Aster Tech Private Limited" should
    produce a NORMALISED_MATCH with is_confirmed=True because
    after normalisation they become identical ("aster tech").
    """

    def test_pvt_vs_private(self):
        """Bidder uses 'Pvt Ltd', source uses 'Private Limited'."""
        results = match_entities(BIDDER_ASTER, FACTS_ASTER, VERIFICATIONS_ASTER)
        name_matches = _find_all_matches(results, "legalName")

        # Should have name comparisons from multiple sources
        assert len(name_matches) > 0

        # At least one should be a confirmed normalised match
        confirmed = [m for m in name_matches if m.is_confirmed]
        assert len(confirmed) > 0
        assert all(m.match_type == MatchType.NORMALISED_MATCH for m in confirmed)

    def test_case_insensitive_name_match(self):
        """Bidder uses mixed case, source uses UPPERCASE."""
        # MCA_DEMO returns "ASTER TECH PRIVATE LIMITED" — should normalise-match
        results = match_entities(BIDDER_ASTER, FACTS_ASTER, VERIFICATIONS_ASTER)
        mca_name = _find_match(results, "legalName", source="MCA_DEMO")

        assert mca_name is not None
        assert mca_name.match_type == MatchType.NORMALISED_MATCH
        assert mca_name.is_confirmed is True

    def test_crest_pvt_vs_private(self):
        """Crest Systems 'Pvt Ltd' vs 'Private Limited' should normalise-match."""
        results = match_entities(BIDDER_CREST, FACTS_CREST, VERIFICATIONS_CREST)
        name_matches = _find_all_matches(results, "legalName")

        confirmed = [m for m in name_matches if m.is_confirmed]
        assert len(confirmed) > 0


# ===================================================================
# Test 6 — Legal-name mismatch
# ===================================================================

class TestNameMismatch:
    """
    "Bharat Supplies Pvt Ltd" vs GST source "Bharat Trading Corp"
    should produce MISMATCH with is_confirmed=False.
    """

    def test_gst_name_mismatch(self):
        results = match_entities(BIDDER_BHARAT, FACTS_BHARAT, VERIFICATIONS_BHARAT)
        gst_name = _find_match(results, "legalName", source="GST_DEMO")

        assert gst_name is not None
        assert gst_name.match_type == MatchType.MISMATCH
        assert gst_name.is_confirmed is False
        assert gst_name.bid_value == "Bharat Supplies Pvt Ltd"
        assert gst_name.source_value == "Bharat Trading Corp"

    def test_bharat_pan_name_matches(self):
        """PAN source returns 'Bharat Supplies Private Limited' — should normalise-match."""
        results = match_entities(BIDDER_BHARAT, FACTS_BHARAT, VERIFICATIONS_BHARAT)
        pan_name = _find_match(results, "legalName", source="PAN_DEMO")

        assert pan_name is not None
        assert pan_name.match_type == MatchType.NORMALISED_MATCH
        assert pan_name.is_confirmed is True


# ===================================================================
# Test 7 — Fuzzy name similarity (never confirms identity)
# ===================================================================

class TestFuzzyNameSimilarity:
    """
    Names with high similarity but without normalised exact equality
    should never have is_confirmed=True. They may include a review note.
    """

    def test_high_similarity_not_confirmed(self):
        """Use names that are similar but not normalised-equal."""
        bidder = BidderProfile(
            bidder_id="BID-FUZZY",
            legal_name="Infra Solutions India",
        )
        verifications = [
            VerificationResult(
                source="PAN_DEMO",
                mode="DEMO",
                identifier="XYZAB1234C",
                status="VERIFIED",
                verified_facts={
                    "pan": "XYZAB1234C",
                    "name": "Infra Solution India",  # "Solution" vs "Solutions"
                },
                checked_at="2026-09-25T10:00:00Z",
            ),
        ]
        results = match_entities(bidder, [], verifications)
        name_match = _find_match(results, "legalName", source="PAN_DEMO")

        assert name_match is not None
        # Fuzzy match must NEVER confirm identity
        assert name_match.is_confirmed is False
        assert name_match.match_type == MatchType.MISMATCH
        # Should have a review note with similarity score
        assert name_match.notes is not None

    def test_completely_different_names_not_confirmed(self):
        """Completely different names are definitely not confirmed."""
        bidder = BidderProfile(
            bidder_id="BID-DIFF",
            legal_name="Alpha Technologies",
        )
        verifications = [
            VerificationResult(
                source="PAN_DEMO",
                mode="DEMO",
                identifier="QQQQQ1111Q",
                status="VERIFIED",
                verified_facts={
                    "pan": "QQQQQ1111Q",
                    "name": "Omega Industries",
                },
                checked_at="2026-09-25T10:00:00Z",
            ),
        ]
        results = match_entities(bidder, [], verifications)
        name_match = _find_match(results, "legalName", source="PAN_DEMO")

        assert name_match is not None
        assert name_match.is_confirmed is False
        assert name_match.match_type == MatchType.MISMATCH


# ===================================================================
# Test 8 — Missing source value
# ===================================================================

class TestMissingSourceValue:
    """
    When a source does not return a verification for an identifier,
    the result should be NOT_AVAILABLE with is_confirmed=False.
    """

    def test_no_verification_results(self):
        """No verifications at all → all identifiers NOT_AVAILABLE."""
        results = match_entities(BIDDER_ASTER, FACTS_ASTER, [])

        for field in ["pan", "gstin", "udyamNumber", "cin"]:
            match = _find_match(results, field)
            assert match is not None, f"Missing match for field '{field}'"
            assert match.match_type == MatchType.NOT_AVAILABLE
            assert match.is_confirmed is False

    def test_not_found_status(self):
        """A source with NOT_FOUND status should not provide a match."""
        results = match_entities(
            BIDDER_ASTER,
            FACTS_ASTER,
            [VERIFICATION_NOT_FOUND],
        )
        pan_match = _find_match(results, "pan")
        assert pan_match is not None
        # NOT_FOUND status means the source didn't verify — should be NOT_AVAILABLE
        assert pan_match.match_type == MatchType.NOT_AVAILABLE
        assert pan_match.is_confirmed is False

    def test_error_status(self):
        """A source with ERROR status should not provide a match."""
        results = match_entities(
            BIDDER_ASTER,
            FACTS_ASTER,
            [VERIFICATION_ERROR],
        )
        gstin_match = _find_match(results, "gstin")
        assert gstin_match is not None
        assert gstin_match.match_type == MatchType.NOT_AVAILABLE
        assert gstin_match.is_confirmed is False


# ===================================================================
# Test 9 — Missing bidder identifier
# ===================================================================

class TestMissingBidderIdentifier:
    """
    When the bidder did not provide an identifier (e.g. pan=None),
    the matcher must not crash or invent a match.
    """

    def test_minimal_bidder(self):
        """Bidder with only legal_name — all identifiers NOT_AVAILABLE."""
        results = match_entities(BIDDER_MINIMAL, [], [])

        for field in ["pan", "gstin", "udyamNumber", "cin"]:
            match = _find_match(results, field)
            assert match is not None, f"Missing match for field '{field}'"
            assert match.match_type == MatchType.NOT_AVAILABLE
            assert match.is_confirmed is False

    def test_none_identifiers_with_verifications(self):
        """Bidder has None identifiers but verifications exist — should not crash."""
        results = match_entities(
            BIDDER_NONE_IDENTIFIERS,
            [],
            VERIFICATIONS_ASTER,
        )

        for field in ["pan", "gstin", "udyamNumber", "cin"]:
            match = _find_match(results, field)
            assert match is not None
            assert match.is_confirmed is False

    def test_no_crash_on_empty_inputs(self):
        """Minimal bidder with no facts and no verifications — no crash."""
        results = match_entities(BIDDER_MINIMAL, [], [])
        assert isinstance(results, list)
        assert len(results) > 0  # should still have NOT_AVAILABLE entries

    def test_bidder_missing_udyam_crest(self):
        """Crest has no Udyam number — should produce NOT_AVAILABLE."""
        results = match_entities(BIDDER_CREST, FACTS_CREST, VERIFICATIONS_CREST)
        udyam_match = _find_match(results, "udyamNumber")

        assert udyam_match is not None
        assert udyam_match.match_type == MatchType.NOT_AVAILABLE
        assert udyam_match.is_confirmed is False


# ===================================================================
# Test 10 — Multiple source records
# ===================================================================

class TestMultipleSourceRecords:
    """
    The matcher must handle multiple verification results deterministically.
    Name comparisons may produce multiple MatchResults (one per source).
    """

    def test_multiple_name_sources(self):
        """Aster has PAN, GST, UDYAM, MCA sources — all return names."""
        results = match_entities(BIDDER_ASTER, FACTS_ASTER, VERIFICATIONS_ASTER)
        name_matches = _find_all_matches(results, "legalName")

        # Should have at least 2 name comparisons from different sources
        assert len(name_matches) >= 2
        sources = {m.source for m in name_matches}
        assert len(sources) == len(name_matches), "Each name match should be from a unique source"

    def test_bharat_multiple_name_sources(self):
        """
        Bharat has PAN name match but GST name mismatch.
        Both should be present and distinguishable.
        """
        results = match_entities(BIDDER_BHARAT, FACTS_BHARAT, VERIFICATIONS_BHARAT)
        name_matches = _find_all_matches(results, "legalName")

        # Should have at least 2 name comparisons
        assert len(name_matches) >= 2

        # GST source should be a MISMATCH
        gst_names = [m for m in name_matches if m.source == "GST_DEMO"]
        assert len(gst_names) == 1
        assert gst_names[0].match_type == MatchType.MISMATCH
        assert gst_names[0].is_confirmed is False

        # PAN source should be a NORMALISED_MATCH
        pan_names = [m for m in name_matches if m.source == "PAN_DEMO"]
        assert len(pan_names) == 1
        assert pan_names[0].match_type == MatchType.NORMALISED_MATCH
        assert pan_names[0].is_confirmed is True

    def test_conflicting_identifiers_preserved(self):
        """
        When a source returns a different PAN in verified_facts than the
        bidder's PAN, the mismatch should be captured, not silently ignored.
        """
        results = match_entities(
            BIDDER_ASTER,
            FACTS_ASTER,
            [VERIFICATION_PAN_CONFLICT],
        )
        pan_match = _find_match(results, "pan")

        assert pan_match is not None
        assert pan_match.match_type == MatchType.MISMATCH
        assert pan_match.is_confirmed is False

    def test_deterministic_output(self):
        """Same inputs should always produce same outputs."""
        results_1 = match_entities(BIDDER_ASTER, FACTS_ASTER, VERIFICATIONS_ASTER)
        results_2 = match_entities(BIDDER_ASTER, FACTS_ASTER, VERIFICATIONS_ASTER)

        assert len(results_1) == len(results_2)
        for r1, r2 in zip(results_1, results_2):
            assert r1.field == r2.field
            assert r1.match_type == r2.match_type
            assert r1.is_confirmed == r2.is_confirmed
            assert r1.source == r2.source


# ===================================================================
# Additional edge-case tests
# ===================================================================

class TestEdgeCases:
    """Extra tests for robustness."""

    def test_return_type(self):
        """match_entities returns a list of MatchResult objects."""
        results = match_entities(BIDDER_ASTER, FACTS_ASTER, VERIFICATIONS_ASTER)
        assert isinstance(results, list)
        for r in results:
            assert isinstance(r, MatchResult)

    def test_all_identifier_fields_covered(self):
        """Every identity field should have at least one MatchResult."""
        results = match_entities(BIDDER_ASTER, FACTS_ASTER, VERIFICATIONS_ASTER)
        fields = {r.field for r in results}
        assert "pan" in fields
        assert "gstin" in fields
        assert "udyamNumber" in fields
        assert "cin" in fields
        assert "legalName" in fields

    def test_empty_extracted_facts(self):
        """Matching works with no extracted facts (bidder profile is primary)."""
        results = match_entities(BIDDER_ASTER, [], VERIFICATIONS_ASTER)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_aster_all_confirmed(self):
        """Aster Tech: all identifiers and name should match."""
        results = match_entities(BIDDER_ASTER, FACTS_ASTER, VERIFICATIONS_ASTER)

        for field in ["pan", "gstin", "udyamNumber", "cin"]:
            match = _find_match(results, field)
            assert match is not None, f"Missing match for '{field}'"
            assert match.is_confirmed is True, f"'{field}' should be confirmed"
            assert match.match_type == MatchType.EXACT, f"'{field}' should be EXACT"

    def test_bharat_identifiers_match(self):
        """Bharat's PAN, GSTIN, CIN should still match — only name mismatches."""
        results = match_entities(BIDDER_BHARAT, FACTS_BHARAT, VERIFICATIONS_BHARAT)

        pan = _find_match(results, "pan")
        assert pan is not None
        assert pan.match_type == MatchType.EXACT
        assert pan.is_confirmed is True

        gstin = _find_match(results, "gstin")
        assert gstin is not None
        assert gstin.match_type == MatchType.EXACT
        assert gstin.is_confirmed is True

        cin = _find_match(results, "cin")
        assert cin is not None
        assert cin.match_type == MatchType.EXACT
        assert cin.is_confirmed is True


# ===================================================================
# Evidence Provenance Regression Tests
# ===================================================================


class TestProvenanceDivergentPan:
    """
    Regression test 1: Bidder PAN differs from extracted PAN,
    while verified PAN matches the bidder.
    All three observations must remain available.
    """

    def test_bidder_pan_matches_verified_pan(self):
        """The match result compares bidder PAN against source PAN."""
        results = match_entities(
            BIDDER_PROVENANCE, FACTS_DIVERGENT_PAN, VERIFICATIONS_MATCH_BIDDER_PAN
        )
        pan = _find_match(results, "pan")
        assert pan is not None
        # Bidder PAN (ABCDE1234F) matches verified PAN (ABCDE1234F)
        assert pan.match_type == MatchType.EXACT
        assert pan.is_confirmed is True
        assert pan.bid_value == "ABCDE1234F"

    def test_divergent_extracted_pan_preserved(self):
        """The extracted PAN (ABCDE1234G) must be preserved in observations."""
        results = match_entities(
            BIDDER_PROVENANCE, FACTS_DIVERGENT_PAN, VERIFICATIONS_MATCH_BIDDER_PAN
        )
        pan = _find_match(results, "pan")
        assert pan is not None

        # Extracted observations should contain the divergent OCR value
        assert len(pan.extracted_observations) >= 1
        extracted_values = {obs.value for obs in pan.extracted_observations}
        assert "ABCDE1234G" in extracted_values  # divergent extracted value preserved

    def test_all_three_sources_available(self):
        """Bid value, extracted observation, and verification observation all present."""
        results = match_entities(
            BIDDER_PROVENANCE, FACTS_DIVERGENT_PAN, VERIFICATIONS_MATCH_BIDDER_PAN
        )
        pan = _find_match(results, "pan")
        assert pan is not None

        # Bid value from bidder profile
        assert pan.bid_value == "ABCDE1234F"
        # Extracted observations from documents
        assert len(pan.extracted_observations) >= 1
        # Verification observations from connectors
        assert len(pan.verification_observations) >= 1
        assert pan.verification_observations[0].source == "PAN_DEMO"


class TestProvenanceMultiConfidence:
    """
    Regression test 3: Multiple extracted facts with different confidence
    values must all be preserved.
    """

    def test_all_confidence_levels_preserved(self):
        """All three extracted PAN observations are retained."""
        results = match_entities(
            BIDDER_PROVENANCE, FACTS_MULTI_CONFIDENCE_PAN, VERIFICATIONS_MATCH_BIDDER_PAN
        )
        pan = _find_match(results, "pan")
        assert pan is not None

        # All 3 extracted facts for PAN must be preserved
        assert len(pan.extracted_observations) == 3

        # Sorted by confidence descending
        confidences = [obs.confidence for obs in pan.extracted_observations]
        assert confidences == sorted(confidences, reverse=True)

    def test_divergent_value_not_discarded(self):
        """The lower-confidence ABCDE1234G must not be discarded."""
        results = match_entities(
            BIDDER_PROVENANCE, FACTS_MULTI_CONFIDENCE_PAN, VERIFICATIONS_MATCH_BIDDER_PAN
        )
        pan = _find_match(results, "pan")
        assert pan is not None

        extracted_values = {obs.value for obs in pan.extracted_observations}
        assert "ABCDE1234F" in extracted_values
        assert "ABCDE1234G" in extracted_values  # divergent value preserved

    def test_document_provenance_preserved(self):
        """Each observation retains document_id, page, and document_type."""
        results = match_entities(
            BIDDER_PROVENANCE, FACTS_MULTI_CONFIDENCE_PAN, VERIFICATIONS_MATCH_BIDDER_PAN
        )
        pan = _find_match(results, "pan")
        assert pan is not None

        doc_ids = {obs.document_id for obs in pan.extracted_observations}
        assert "doc-pan-high" in doc_ids
        assert "doc-pan-low" in doc_ids
        assert "doc-pan-diff" in doc_ids

        for obs in pan.extracted_observations:
            assert obs.document_id is not None
            assert obs.confidence is not None


class TestProvenanceConflictingVerifications:
    """
    Regression test 4: Conflicting verification values remain visible.
    """

    def test_conflicting_verified_facts_visible(self):
        """When source returns conflicting PAN, the mismatch is captured."""
        results = match_entities(
            BIDDER_ASTER, FACTS_ASTER, [VERIFICATION_PAN_CONFLICT]
        )
        pan = _find_match(results, "pan")
        assert pan is not None
        assert pan.match_type == MatchType.MISMATCH
        assert pan.is_confirmed is False

        # The conflicting verification observation must be preserved
        assert len(pan.verification_observations) >= 1
        conflict_obs = pan.verification_observations[0]
        assert conflict_obs.status == "VERIFIED"
        # The actual verified_facts with conflicting PAN are preserved
        assert conflict_obs.verified_facts.get("pan") == "XXXXX9999Y"


class TestProvenanceVerificationStatus:
    """
    Regression tests 5 & 6: Source status and evidence references are
    retained. Missing and ERROR responses are not confirmed.
    """

    def test_verified_status_and_evidence_retained(self):
        """VERIFIED results preserve checked_at and evidence_reference."""
        results = match_entities(
            BIDDER_ASTER, FACTS_ASTER, VERIFICATIONS_ASTER
        )
        pan = _find_match(results, "pan")
        assert pan is not None

        assert len(pan.verification_observations) >= 1
        obs = pan.verification_observations[0]
        assert obs.status == "VERIFIED"
        assert obs.checked_at is not None
        assert obs.evidence_reference is not None

    def test_not_found_preserved_in_observations(self):
        """NOT_FOUND status is preserved, not silently dropped."""
        results = match_entities(
            BIDDER_ASTER, FACTS_ASTER, [VERIFICATION_NOT_FOUND]
        )
        pan = _find_match(results, "pan")
        assert pan is not None
        assert pan.is_confirmed is False

        # The NOT_FOUND verification observation should be preserved
        assert len(pan.verification_observations) >= 1
        statuses = {obs.status for obs in pan.verification_observations}
        assert "NOT_FOUND" in statuses

    def test_error_preserved_in_observations(self):
        """ERROR status is preserved, not silently dropped."""
        results = match_entities(
            BIDDER_ASTER, FACTS_ASTER, [VERIFICATION_ERROR]
        )
        gstin = _find_match(results, "gstin")
        assert gstin is not None
        assert gstin.is_confirmed is False

        # The ERROR verification observation should be preserved
        assert len(gstin.verification_observations) >= 1
        statuses = {obs.status for obs in gstin.verification_observations}
        assert "ERROR" in statuses

    def test_mixed_status_both_preserved(self):
        """When same source has VERIFIED and NOT_FOUND, both are preserved."""
        results = match_entities(
            BIDDER_PROVENANCE, FACTS_DIVERGENT_PAN, VERIFICATIONS_MIXED_STATUS
        )
        pan = _find_match(results, "pan")
        assert pan is not None

        # Both PAN_DEMO responses should be in observations
        assert len(pan.verification_observations) == 2
        statuses = {obs.status for obs in pan.verification_observations}
        assert "VERIFIED" in statuses
        assert "NOT_FOUND" in statuses


class TestProvenanceDeterminism:
    """
    Regression test 7: Output including provenance remains deterministic.
    """

    def test_provenance_deterministic(self):
        """Same inputs produce identical provenance output."""
        results_1 = match_entities(
            BIDDER_PROVENANCE, FACTS_MULTI_CONFIDENCE_PAN, VERIFICATIONS_MIXED_STATUS
        )
        results_2 = match_entities(
            BIDDER_PROVENANCE, FACTS_MULTI_CONFIDENCE_PAN, VERIFICATIONS_MIXED_STATUS
        )
        assert len(results_1) == len(results_2)
        for r1, r2 in zip(results_1, results_2):
            assert r1.field == r2.field
            assert r1.match_type == r2.match_type
            assert r1.is_confirmed == r2.is_confirmed
            assert len(r1.extracted_observations) == len(r2.extracted_observations)
            assert len(r1.verification_observations) == len(r2.verification_observations)
            for e1, e2 in zip(r1.extracted_observations, r2.extracted_observations):
                assert e1.value == e2.value
                assert e1.confidence == e2.confidence
                assert e1.document_id == e2.document_id
            for v1, v2 in zip(r1.verification_observations, r2.verification_observations):
                assert v1.source == v2.source
                assert v1.status == v2.status
                assert v1.identifier == v2.identifier


class TestProvenanceBackwardCompatibility:
    """
    Regression test 8: Existing Phase 2 behavior remains compatible.
    The new provenance fields default to empty lists when not populated.
    """

    def test_existing_match_result_construction_works(self):
        """MatchResult without provenance fields still constructs correctly."""
        mr = MatchResult(
            field="pan",
            bid_value="ABCDE1234F",
            source_value="ABCDE1234F",
            source="PAN_DEMO",
            match_type=MatchType.EXACT,
            is_confirmed=True,
        )
        assert mr.extracted_observations == []
        assert mr.verification_observations == []
        assert mr.match_type == MatchType.EXACT
        assert mr.is_confirmed is True

    def test_aster_all_confirmed_with_provenance(self):
        """Aster Tech still produces correct results with provenance attached."""
        results = match_entities(BIDDER_ASTER, FACTS_ASTER, VERIFICATIONS_ASTER)

        for field in ["pan", "gstin", "udyamNumber", "cin"]:
            match = _find_match(results, field)
            assert match is not None, f"Missing match for '{field}'"
            assert match.is_confirmed is True, f"'{field}' should be confirmed"
            assert match.match_type == MatchType.EXACT, f"'{field}' should be EXACT"
            # Provenance should now be populated
            assert len(match.extracted_observations) >= 1, (
                f"'{field}' should have extracted observations"
            )
            assert len(match.verification_observations) >= 1, (
                f"'{field}' should have verification observations"
            )
