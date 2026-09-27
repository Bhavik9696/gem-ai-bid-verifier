# Compliance Engine — Module Documentation (Member 5)

## Purpose

The Compliance Engine is the decision-support layer of ComplianceOS. It receives structured bid data — extracted document facts (from Member 4), source-verified data (from Member 6 connectors), bidder profiles, and tender context (from Member 3) — and produces a complete `ComplianceAssessment` for the Procurement Officer.

It **does not** replace the officer's final decision. It provides scored, evidence-backed, explainable compliance analysis.

## Ownership Boundary

```
backend/app/services/compliance/
├── __init__.py              # Public entry point: evaluate_bid_compliance()
├── schemas.py               # All Pydantic input/output models
├── entity_matcher.py        # Phase 2: Identity matching
├── conflict_detector.py     # Phase 3: Conflict/finding detection
├── rule_engine.py           # Phase 4: YAML-driven rule evaluation
├── scoring.py               # Phase 5: Compliance + risk scoring
├── recommendation.py        # Phase 6: Deterministic recommendation
├── utils.py                 # Pure helpers (normalisation, date parsing, IDs)
├── rules/
│   └── TENDER-2026-IT-001_v1.yaml   # Demo tender rulebook
└── tests/
    ├── fixtures/             # Shared test data
    ├── test_entity_matcher.py
    ├── test_conflict_detector.py
    ├── test_rule_engine.py
    ├── test_scoring.py
    ├── test_recommendation.py
    ├── test_integration.py   # End-to-end 3-bidder story tests
    └── test_phase1.py        # Schema/structure validation tests
```

## Design Constraints

1. **Pure function**: `evaluate_bid_compliance()` has no database access, no HTTP calls, no LLM calls, and no side effects. All data is passed in; the assessment is returned.
2. **Deterministic**: Identical inputs always produce identical outputs, including finding IDs (SHA-256 based).
3. **No hardcoded bidder outcomes**: Results are driven entirely by data and YAML rules — never by bidder name.
4. **Decision support only**: The engine produces recommendations, not final procurement decisions. The officer retains authority.

## Public Entry Point

```python
from app.services.compliance import evaluate_bid_compliance
from app.services.compliance.schemas import BidComplianceInput, ComplianceAssessment

assessment: ComplianceAssessment = evaluate_bid_compliance(input_data)
```

### Input: `BidComplianceInput`

| Field                  | Type                     | Source          |
|------------------------|--------------------------|-----------------|
| `bid_id`               | `str`                    | Core API        |
| `tender`               | `TenderContext`          | Core API        |
| `bidder`               | `BidderProfile`          | Core API        |
| `extracted_facts`      | `list[ExtractedFact]`    | Member 4 (Doc AI) |
| `verification_results` | `list[VerificationResult]` | Member 6 (Connectors) |

### Output: `ComplianceAssessment`

| Field                    | Type                   | Description |
|--------------------------|------------------------|-------------|
| `bid_id`                 | `str`                  | Echo of input |
| `bidder_id`              | `str`                  | From bidder profile |
| `tender_id`              | `str`                  | From tender context |
| `compliance_score`       | `float (0–100)`        | Weighted compliance percentage |
| `risk_score`             | `float (0–100)`        | Additive risk score (capped at 100) |
| `risk_level`             | `RiskLevel` enum       | LOW / MODERATE / HIGH / CRITICAL |
| `recommendation`         | `str`                  | One of 3 allowed values |
| `recommendation_summary` | `str`                  | Plain-language explanation |
| `match_results`          | `list[MatchResult]`    | Per-field identity comparisons |
| `findings`               | `list[Finding]`        | Conflicts, discrepancies, flags |
| `rule_results`           | `list[RuleResult]`     | Per-rule evaluation outcomes |
| `score_breakdown`        | `list[ScoreBreakdown]` | Per-category score detail |
| `has_mandatory_failure`  | `bool`                 | True if any mandatory rule FAILed |
| `evaluated_at`           | `str`                  | ISO 8601 timestamp |

## Pipeline Architecture

```
BidComplianceInput
    │
    ├─► entity_matcher.match_entities()         → MatchResult[]
    │     Compare PAN, GSTIN, Udyam, CIN, legalName
    │     against bidder profile + connector verified_facts
    │
    ├─► conflict_detector.detect_conflicts()    → Finding[]
    │     GST name mismatch, PAN mismatch, GST inactive,
    │     Udyam missing/unverified, OEM expired, blacklist hit,
    │     local content threshold, mandatory document missing,
    │     source unavailable, low-confidence facts, conflicting evidence
    │
    ├─► rule_engine.evaluate_rules()            → RuleResult[]
    │     Load YAML rulebook by tender.rulebook_id
    │     Evaluate each rule deterministically
    │
    ├─► scoring.calculate_scores()              → scores + breakdown
    │     Weighted compliance: mandatory_eligibility(0.60),
    │     statutory_compliance(0.25), documentation(0.15)
    │     Additive risk points from findings/rules/mismatches
    │
    └─► recommendation.generate()               → recommendation + summary
          Decision tree: mandatory failure → High-Risk,
          clarification needed → Needs Clarification,
          all pass + low risk → Compliant
```

## Allowed Recommendations (Exact Strings)

1. `"Compliant — Ready for Officer Confirmation"`
2. `"Needs Clarification — Missing or Unverified Evidence"`
3. `"High-Risk — Officer Review Required"`

No other recommendation strings are produced.

## Rule Evaluation

Rules are defined in versioned YAML files (`rules/TENDER-2026-IT-001_v1.yaml`). Each rule specifies:

- **`id`**: Unique rule identifier
- **`priority`**: `mandatory`, `recommended`, or `informational`
- **`category`**: `mandatory_eligibility`, `statutory_compliance`, or `documentation`
- **`when_applicable`**: Optional conditional (e.g. `tender.msme_mandatory`)
- **`conditions`**: `requires_fact`, `requires_source`, and `checks[]`
- **Configured outcomes**: `on_pass`, `on_fail`, `on_missing_fact`, `on_missing_source`, `on_unverifiable`

### Rule Result Statuses

| Status                | Meaning |
|-----------------------|---------|
| `PASS`                | Rule requirements satisfied |
| `FAIL`                | Rule requirements not met |
| `NEEDS_CLARIFICATION` | Evidence missing/invalid; cannot safely evaluate |
| `SOURCE_UNAVAILABLE`  | Required verification source was absent or errored |
| `NOT_APPLICABLE`      | Rule skipped due to `when_applicable` condition |

## Evidence Provenance

Every `MatchResult` includes:
- `extracted_observations[]`: All document-extracted values for the field (including low-confidence ones)
- `verification_observations[]`: All connector responses, including status, `verified_facts`, timestamps, and evidence references

Every `Finding` includes:
- `finding_id`: Deterministic (SHA-256 of type + key evidence)
- `evidence`: Structured dict with extracted values, source values, document IDs, etc.

## Missing/Unavailable Source Behaviour

- **No connector response**: Rule result = `SOURCE_UNAVAILABLE`; finding = `SOURCE_UNAVAILABLE` with severity `MEDIUM`
- **ERROR response**: Treated as `SOURCE_UNAVAILABLE`, never as positive confirmation
- **NOT_FOUND response**: Treated as unverified; does not confirm compliance
- **Missing extracted fact**: Rule result = `NEEDS_CLARIFICATION` with configured message

## Mandatory Failure Gating

If **any** mandatory-priority rule has `result = FAIL`:
- `has_mandatory_failure = True`
- Recommendation is forced to `"High-Risk — Officer Review Required"` regardless of compliance score
- A high compliance score cannot override a mandatory failure

## Error Handling

- Malformed YAML rulebooks raise `ValueError` at load time, preventing silent misclassification
- Unsupported operators/conditions raise `ValueError` during rulebook validation
- Unparseable dates return `None` from `parse_date()`, causing affected checks to return `NEEDS_CLARIFICATION` rather than false PASS/FAIL
- Duplicate rule IDs in a rulebook are rejected at load time

## Testing

Run the full compliance test suite:

```bash
# From the repository root
PYTHONPATH=backend python -m pytest backend/app/services/compliance/tests -v

# PowerShell
$env:PYTHONPATH="backend"; python -m pytest backend/app/services/compliance/tests -v
```

**277 tests** across 7 test modules covering entity matching, conflict detection, rule evaluation, scoring, recommendations, integration scenarios, and schema validation.

## Known Limitations

1. **YAML rulebooks only**: The rule engine loads YAML files from the filesystem. There is no database-backed rule management or runtime rule creation.
2. **`difflib.SequenceMatcher` for name similarity**: Name comparison uses stdlib, not a production fuzzy matching library. Threshold is 0.85.
3. **Connector field mapping is static**: The `_SOURCE_FIELD_MAP` in `entity_matcher.py` must be manually updated when new connectors are added or field names change.
4. **No async support**: `evaluate_bid_compliance()` is synchronous. If the orchestrator needs async, it should wrap the call in `asyncio.to_thread()`.
5. **Prototype demo data**: All connector sources operate in `DEMO` mode with controlled datasets. Results must not be presented as live government verification.
6. **No PDF/document processing**: The compliance engine consumes only structured `ExtractedFact` objects. Document processing is the responsibility of Member 4 (Document Intelligence).
