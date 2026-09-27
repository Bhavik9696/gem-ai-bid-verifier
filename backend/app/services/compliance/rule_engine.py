"""
Compliance Engine — Rule Engine

Loads tender-specific versioned YAML rulebooks and evaluates each rule
deterministically against bid data, extracted facts, and verification
results.

Design constraints:
    - Deterministic: same inputs always produce same outputs.
    - No database access, no HTTP calls, no LLM calls, no side effects.
    - Rules are data-driven via YAML files, not hardcoded.
    - Each rule produces exactly one RuleResult.
    - Supports conditional applicability (when_applicable).
    - Missing facts/sources produce explicit outcomes, never silent skips.
    - Malformed rulebooks and unsupported operators fail explicitly.
    - Unparseable dates are not treated as valid dates or as null values.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .schemas import (
    BidderProfile,
    ExtractedFact,
    RuleCategory,
    RulePriority,
    RuleResult,
    RuleResultStatus,
    Severity,
    TenderContext,
    VerificationResult,
)
from .utils import (
    normalise_name,
    name_similarity,
    parse_date,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_RULES_DIR = Path(__file__).parent / "rules"

# Name-match similarity threshold (same as entity_matcher).
_NAME_MATCH_THRESHOLD = 0.85

# Only these operators are supported by the rule engine.
_SUPPORTED_OPERATORS = {
    "eq",
    "neq",
    "gte",
    "lte",
    "after_or_eq",
    "before",
    "is_null_or_after",
    "name_match",
}

# Supported conditional applicability expressions.
_SUPPORTED_APPLICABILITY_CONDITIONS = {
    "tender.msme_mandatory",
    "tender.oem_required",
    "tender.make_in_india_required",
}

# Supported source statuses used by the verification contract.
_VERIFIED_STATUS = "VERIFIED"
_ERROR_STATUS = "ERROR"
_NOT_FOUND_STATUS = "NOT_FOUND"

# Fields that may be resolved directly from the bidder profile when
# a rule declares conditions.requires_fact.
_BIDDER_FACT_FIELDS = {
    "pan": "pan",
    "gstin": "gstin",
    "udyam_number": "udyam_number",
    "udyamNumber": "udyam_number",
    "cin": "cin",
}


# ---------------------------------------------------------------------------
# YAML loading and validation
# ---------------------------------------------------------------------------

def _validate_rulebook(rulebook: Any, path: Path) -> dict:
    """
    Validate the rulebook structure before evaluation.

    Validation is intentionally performed at load time so malformed
    configuration does not silently produce PASS or NOT_APPLICABLE results.
    """
    if not isinstance(rulebook, dict):
        raise ValueError(f"Invalid rulebook format in {path}: expected a mapping.")

    rules = rulebook.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ValueError(
            f"Invalid rulebook format in {path}: 'rules' must be a non-empty list."
        )

    seen_rule_ids: set[str] = set()

    for index, rule in enumerate(rules):
        location = f"{path}: rules[{index}]"

        if not isinstance(rule, dict):
            raise ValueError(f"Invalid rule at {location}: expected a mapping.")

        rule_id = rule.get("id")
        rule_name = rule.get("name")

        if not isinstance(rule_id, str) or not rule_id.strip():
            raise ValueError(f"Invalid rule at {location}: missing non-empty 'id'.")

        if not isinstance(rule_name, str) or not rule_name.strip():
            raise ValueError(
                f"Invalid rule '{rule_id}' at {location}: "
                "missing non-empty 'name'."
            )

        if rule_id in seen_rule_ids:
            raise ValueError(
                f"Duplicate rule ID '{rule_id}' in rulebook {path}."
            )
        seen_rule_ids.add(rule_id)

        # Validate enum values early, rather than failing halfway through
        # evaluation of a bidder.
        try:
            RulePriority(rule.get("priority", "informational"))
            RuleCategory(rule.get("category", "mandatory_eligibility"))
        except ValueError as exc:
            raise ValueError(
                f"Invalid priority/category for rule '{rule_id}': {exc}"
            ) from exc

        when_applicable = rule.get("when_applicable")
        if when_applicable is not None:
            if not isinstance(when_applicable, str):
                raise ValueError(
                    f"Invalid when_applicable for rule '{rule_id}': "
                    "expected a string."
                )
            if when_applicable.strip() not in _SUPPORTED_APPLICABILITY_CONDITIONS:
                raise ValueError(
                    f"Unsupported when_applicable condition "
                    f"'{when_applicable}' in rule '{rule_id}'."
                )

        conditions = rule.get("conditions", {})
        if not isinstance(conditions, dict):
            raise ValueError(
                f"Invalid conditions for rule '{rule_id}': expected a mapping."
            )

        checks = conditions.get("checks", [])
        if not isinstance(checks, list):
            raise ValueError(
                f"Invalid checks for rule '{rule_id}': expected a list."
            )

        requires_fact = conditions.get("requires_fact")
        requires_source = conditions.get("requires_source")

        # A rule must have something to evaluate. An empty check list is
        # allowed only when the rule explicitly requires a fact or source.
        if not checks and not requires_fact and not requires_source:
            raise ValueError(
                f"Rule '{rule_id}' has no checks, requires_fact, or "
                "requires_source; refusing to treat it as an automatic PASS."
            )

        for check_index, check in enumerate(checks):
            check_location = f"{location}.conditions.checks[{check_index}]"

            if not isinstance(check, dict):
                raise ValueError(
                    f"Invalid check at {check_location}: expected a mapping."
                )

            field = check.get("field")
            operator = check.get("operator")

            if not isinstance(field, str) or not field.strip():
                raise ValueError(
                    f"Invalid check at {check_location}: "
                    "missing non-empty 'field'."
                )

            if operator not in _SUPPORTED_OPERATORS:
                raise ValueError(
                    f"Unsupported operator '{operator}' at {check_location}."
                )

            if "reference" not in check and "value" not in check:
                raise ValueError(
                    f"Invalid check at {check_location}: "
                    "must define either 'value' or 'reference'."
                )

        # Validate configured outcomes before a rule is evaluated.
        for outcome_key in (
            "on_pass",
            "on_fail",
            "on_missing_fact",
            "on_missing_source",
            "on_unverifiable",
        ):
            outcome = rule.get(outcome_key)
            if outcome is None:
                continue

            if not isinstance(outcome, dict):
                raise ValueError(
                    f"Invalid '{outcome_key}' for rule '{rule_id}': "
                    "expected a mapping."
                )

            result_value = outcome.get("result")
            if result_value is not None:
                try:
                    RuleResultStatus(result_value)
                except ValueError as exc:
                    raise ValueError(
                        f"Invalid result '{result_value}' in "
                        f"'{outcome_key}' for rule '{rule_id}'."
                    ) from exc

            severity_value = outcome.get("severity")
            if severity_value is not None:
                try:
                    Severity(severity_value)
                except ValueError as exc:
                    raise ValueError(
                        f"Invalid severity '{severity_value}' in "
                        f"'{outcome_key}' for rule '{rule_id}'."
                    ) from exc

    return rulebook


def load_rulebook(rulebook_id: str) -> dict:
    """
    Load and parse a YAML rulebook by its ID.

    Args:
        rulebook_id: e.g. 'TENDER-2026-IT-001_v1'

    Returns:
        Validated parsed YAML dict containing rulebook metadata and rules.

    Raises:
        FileNotFoundError: if the rulebook YAML does not exist.
        ValueError: if the ID, YAML, or rulebook structure is invalid.
    """
    # Prevent path traversal and unexpected filenames.
    if not isinstance(rulebook_id, str) or not re.fullmatch(
        r"[A-Za-z0-9_-]+", rulebook_id
    ):
        raise ValueError(f"Invalid rulebook ID: {rulebook_id!r}")

    path = _RULES_DIR / f"{rulebook_id}.yaml"

    if not path.is_file():
        raise FileNotFoundError(f"Rulebook not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        raise ValueError(f"Malformed YAML in rulebook {path}: {exc}") from exc

    if not isinstance(data, dict) or "rulebook" not in data:
        raise ValueError(
            f"Invalid rulebook format in {path}: "
            "expected top-level 'rulebook' mapping."
        )

    return _validate_rulebook(data["rulebook"], path)


# ---------------------------------------------------------------------------
# Applicability check
# ---------------------------------------------------------------------------

def _check_applicability(
    when_applicable: str | None,
    tender: TenderContext,
) -> bool:
    """
    Evaluate whether a rule is applicable based on its when_applicable
    condition and the tender context.

    Supported conditions:
        tender.msme_mandatory
        tender.oem_required
        tender.make_in_india_required

    Unknown conditions raise ValueError rather than silently making a
    potentially mandatory rule NOT_APPLICABLE.
    """
    if when_applicable is None:
        return True

    field = when_applicable.strip()

    lookup = {
        "tender.msme_mandatory": tender.msme_mandatory,
        "tender.oem_required": tender.oem_required,
        "tender.make_in_india_required": tender.make_in_india_required,
    }

    if field not in lookup:
        raise ValueError(
            f"Unsupported when_applicable condition: {when_applicable!r}"
        )

    return bool(lookup[field])


# ---------------------------------------------------------------------------
# Value resolution
# ---------------------------------------------------------------------------

def _resolve_reference(
    reference: str,
    tender: TenderContext,
    bidder: BidderProfile,
) -> Any:
    """Resolve a reference such as 'tender.closing_date' or 'bidder.pan'."""
    parts = reference.split(".", 1)

    if len(parts) != 2:
        return None

    obj_name, attr = parts

    if obj_name == "tender":
        return getattr(tender, attr, None)

    if obj_name == "bidder":
        return getattr(bidder, attr, None)

    return None


def _get_verified_value(
    verification_results: list[VerificationResult],
    source: str,
    field: str,
) -> Any:
    """Get a field value only from a VERIFIED result for the requested source."""
    for verification_result in verification_results:
        if (
            verification_result.source == source
            and verification_result.status == _VERIFIED_STATUS
        ):
            return verification_result.verified_facts.get(field)

    return None


def _get_best_extracted_value(
    extracted_facts: list[ExtractedFact],
    field: str,
) -> str | None:
    """Get the highest-confidence extracted value for a field."""
    candidates = [
        fact
        for fact in extracted_facts
        if fact.field == field and fact.value is not None
    ]

    if not candidates:
        return None

    best = max(candidates, key=lambda fact: fact.confidence)
    return best.value


def _get_source_results(
    verification_results: list[VerificationResult],
    source: str,
) -> list[VerificationResult]:
    """Return all verification results for a named source."""
    return [
        result
        for result in verification_results
        if result.source == source
    ]


def _source_has_error(
    verification_results: list[VerificationResult],
    source: str,
) -> bool:
    """Check whether a source returned an ERROR result."""
    return any(
        result.status == _ERROR_STATUS
        for result in _get_source_results(verification_results, source)
    )


def _source_has_verified_result(
    verification_results: list[VerificationResult],
    source: str,
) -> bool:
    """Check whether the source returned at least one VERIFIED result."""
    return any(
        result.status == _VERIFIED_STATUS
        for result in _get_source_results(verification_results, source)
    )


# ---------------------------------------------------------------------------
# Outcome helpers
# ---------------------------------------------------------------------------

def _configured_outcome(
    rule: dict,
    outcome_key: str,
    default_result: str,
    default_message: str,
    *,
    evidence: dict[str, Any] | None = None,
) -> RuleResult:
    """
    Build a RuleResult from a configured rule outcome.

    Centralizing this logic keeps missing-fact/source and failure outcomes
    consistent and ensures enum conversion happens in one place.
    """
    outcome = rule.get(outcome_key, {}) or {}

    return RuleResult(
        rule_id=rule["id"],
        rule_name=rule["name"],
        result=RuleResultStatus(outcome.get("result", default_result)),
        priority=RulePriority(rule.get("priority", "informational")),
        category=RuleCategory(rule.get("category", "mandatory_eligibility")),
        tender_clause=rule.get("clause"),
        message=outcome.get("message", default_message),
        severity=(
            Severity(outcome["severity"])
            if outcome.get("severity")
            else None
        ),
        evidence=evidence,
    )


def _unverifiable_result(
    rule: dict,
    message: str,
    evidence: dict[str, Any] | None = None,
) -> RuleResult:
    """
    Return a clarification outcome when the engine cannot safely evaluate
    a check, such as when a required value is missing or malformed.

    This avoids interpreting missing or invalid evidence as a confirmed
    compliance failure or a successful check.
    """
    return _configured_outcome(
        rule,
        "on_unverifiable",
        "NEEDS_CLARIFICATION",
        message,
        evidence=evidence,
    )


# ---------------------------------------------------------------------------
# Operator evaluation
# ---------------------------------------------------------------------------

def _evaluate_check(
    check: dict,
    verification_results: list[VerificationResult],
    extracted_facts: list[ExtractedFact],
    tender: TenderContext,
    bidder: BidderProfile,
    source: str | None,
) -> bool | None:
    """
    Evaluate a single check within a rule.

    Returns:
        True  - check passes.
        False - check has sufficient values and fails.
        None  - check cannot be safely evaluated because a value is missing
                or malformed. The caller should return clarification.

    The tri-state return prevents absent or malformed evidence from being
    silently interpreted as a confirmed failure.
    """
    field = check.get("field", "")
    operator = check.get("operator", "")
    expected_value = check.get("value")
    reference = check.get("reference")

    actual_value = None

    # Prefer verified source data when a source is specified.
    if source:
        actual_value = _get_verified_value(
            verification_results,
            source,
            field,
        )

    # Fall back to extracted facts when no verified value is available.
    if actual_value is None:
        actual_value = _get_best_extracted_value(extracted_facts, field)

    # Resolve an optional tender/bidder reference.
    ref_value = None
    if reference:
        ref_value = _resolve_reference(reference, tender, bidder)

    target = ref_value if reference else expected_value

    # --- Equality ---
    if operator == "eq":
        if target is None or actual_value is None:
            return None

        if isinstance(target, bool):
            if isinstance(actual_value, bool):
                return actual_value == target
            return str(actual_value).strip().lower() == str(target).lower()

        return str(actual_value).strip().upper() == str(target).strip().upper()

    # --- Inequality ---
    elif operator == "neq":
        if target is None or actual_value is None:
            return None

        return (
            str(actual_value).strip().upper()
            != str(target).strip().upper()
        )

    # --- Numeric greater-than-or-equal ---
    elif operator == "gte":
        if actual_value is None or target is None:
            return None

        try:
            return float(actual_value) >= float(target)
        except (ValueError, TypeError):
            return None

    # --- Numeric less-than-or-equal ---
    elif operator == "lte":
        if actual_value is None or target is None:
            return None

        try:
            return float(actual_value) <= float(target)
        except (ValueError, TypeError):
            return None

    # --- Date greater-than-or-equal ---
    elif operator == "after_or_eq":
        if actual_value is None or target is None:
            return None

        actual_date = parse_date(str(actual_value))
        target_date = parse_date(str(target))

        if actual_date is None or target_date is None:
            return None

        return actual_date >= target_date

    # --- Date strictly before ---
    elif operator == "before":
        if actual_value is None or target is None:
            return None

        actual_date = parse_date(str(actual_value))
        target_date = parse_date(str(target))

        if actual_date is None or target_date is None:
            return None

        return actual_date < target_date

    # --- Null or strictly after ---
    elif operator == "is_null_or_after":
        # This operator explicitly permits a null actual value.
        if actual_value is None:
            return True

        if target is None:
            return None

        actual_date = parse_date(str(actual_value))
        target_date = parse_date(str(target))

        # A non-null but unparseable date is invalid evidence, not null.
        if actual_date is None or target_date is None:
            return None

        return actual_date > target_date

    # --- Name matching ---
    elif operator == "name_match":
        if actual_value is None or target is None:
            return None

        norm_actual = normalise_name(str(actual_value))
        norm_target = normalise_name(str(target))

        if not norm_actual or not norm_target:
            return None

        if norm_actual == norm_target:
            return True

        return (
            name_similarity(str(actual_value), str(target))
            >= _NAME_MATCH_THRESHOLD
        )

    # The rulebook validator should prevent unsupported operators from
    # reaching this function. Keep an explicit failure in case it is called
    # directly or configuration is modified after loading.
    raise ValueError(f"Unsupported rule operator: {operator!r}")


# ---------------------------------------------------------------------------
# Single rule evaluator
# ---------------------------------------------------------------------------

def _evaluate_single_rule(
    rule: dict,
    tender: TenderContext,
    bidder: BidderProfile,
    extracted_facts: list[ExtractedFact],
    verification_results: list[VerificationResult],
) -> RuleResult:
    """Evaluate a single rule from the rulebook and return a RuleResult."""

    rule_id = rule["id"]
    rule_name = rule["name"]
    priority = RulePriority(rule.get("priority", "informational"))
    category = RuleCategory(rule.get("category", "mandatory_eligibility"))
    clause = rule.get("clause")

    # 1. Check applicability.
    when_applicable = rule.get("when_applicable")

    if not _check_applicability(when_applicable, tender):
        return RuleResult(
            rule_id=rule_id,
            rule_name=rule_name,
            result=RuleResultStatus.NOT_APPLICABLE,
            priority=priority,
            category=category,
            tender_clause=clause,
            message="Rule not applicable for this tender configuration.",
        )

    conditions = rule.get("conditions", {})
    requires_fact = conditions.get("requires_fact")
    requires_source = conditions.get("requires_source")

    # 2. Check whether a required fact is present in extracted facts or
    #    the bidder profile.
    if requires_fact:
        fact_value = _get_best_extracted_value(
            extracted_facts,
            requires_fact,
        )

        bidder_attribute = _BIDDER_FACT_FIELDS.get(requires_fact)
        bidder_value = (
            getattr(bidder, bidder_attribute, None)
            if bidder_attribute
            else None
        )

        if fact_value is None and bidder_value is None:
            return _configured_outcome(
                rule,
                "on_missing_fact",
                "NEEDS_CLARIFICATION",
                f"Required fact '{requires_fact}' was not found.",
                evidence={"missing_fact": requires_fact},
            )

    # 3. Check required verification source.
    if requires_source:
        source_results = _get_source_results(
            verification_results,
            requires_source,
        )

        # An absent source, ERROR response, NOT_FOUND response, or response
        # without a VERIFIED result cannot establish a verified fact.
        # Route these cases through the configured missing-source outcome.
        if (
            not source_results
            or _source_has_error(verification_results, requires_source)
            or not _source_has_verified_result(
                verification_results,
                requires_source,
            )
        ):
            if not source_results:
                message = (
                    f"Required verification source '{requires_source}' "
                    "was not available."
                )
            elif _source_has_error(verification_results, requires_source):
                message = (
                    f"Required verification source '{requires_source}' "
                    "returned an error."
                )
            else:
                message = (
                    f"Required verification source '{requires_source}' "
                    "did not return a verified result."
                )

            return _configured_outcome(
                rule,
                "on_missing_source",
                "SOURCE_UNAVAILABLE",
                message,
                evidence={
                    "required_source": requires_source,
                    "source_statuses": [
                        str(result.status)
                        for result in source_results
                    ],
                },
            )

    # 4. Evaluate all checks. Every configured check must pass.
    checks = conditions.get("checks", [])

    # A rule that has no checks but explicitly requires a fact/source is
    # treated as a presence/availability rule. The checks are validated
    # during rulebook loading, so this branch is intentionally explicit.
    if not checks:
        return _configured_outcome(
            rule,
            "on_pass",
            "PASS",
            f"Rule '{rule_name}' requirements were satisfied.",
        )

    failed_evidence: dict[str, Any] = {}

    for check in checks:
        check_result = _evaluate_check(
            check,
            verification_results,
            extracted_facts,
            tender,
            bidder,
            requires_source,
        )

        if check_result is None:
            evidence = {
                "field": check.get("field", ""),
                "operator": check.get("operator", ""),
                "reason": "Required value was missing, malformed, or unparseable.",
            }
            return _unverifiable_result(
                rule,
                (
                    f"Rule '{rule_name}' could not be evaluated because "
                    "required evidence was missing or invalid."
                ),
                evidence=evidence,
            )

        if check_result is False:
            failed_evidence = {
                "failed_check": check.get("field", ""),
                "operator": check.get("operator", ""),
            }
            break

    if not failed_evidence:
        return _configured_outcome(
            rule,
            "on_pass",
            "PASS",
            f"Rule '{rule_name}' passed.",
        )

    return _configured_outcome(
        rule,
        "on_fail",
        "FAIL",
        f"Rule '{rule_name}' failed.",
        evidence=failed_evidence,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate_rules(
    tender: TenderContext,
    bidder: BidderProfile,
    extracted_facts: list[ExtractedFact],
    verification_results: list[VerificationResult],
) -> list[RuleResult]:
    """
    Load the tender rulebook and evaluate all rules.

    Args:
        tender: Tender context including rulebook_id.
        bidder: Bidder profile.
        extracted_facts: Facts extracted from bid documents.
        verification_results: Verification responses from connectors.

    Returns:
        List of RuleResult, one per rule in the rulebook.

    Raises:
        FileNotFoundError: if the tender's rulebook does not exist.
        ValueError: if the rulebook is malformed or contains unsupported
                    conditions/operators/outcomes.
    """
    rulebook = load_rulebook(tender.rulebook_id)
    rules = rulebook["rules"]

    results: list[RuleResult] = []

    for rule in rules:
        result = _evaluate_single_rule(
            rule,
            tender,
            bidder,
            extracted_facts,
            verification_results,
        )
        results.append(result)

    return results