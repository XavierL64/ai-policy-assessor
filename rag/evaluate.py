"""
RAG pipeline evaluation: compare predictions against human-labeled ground truth.

Evaluates three tiers:
- Retrieval quality (page-overlap recall/precision)
- Commitment accuracy (exact match)
- Exception accuracy (applies/mitigated per exception ID)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

_SRC_DIR = Path(__file__).resolve().parents[1]
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))


# ---------------------------------------------------------------------------
# Gold case loader
# ---------------------------------------------------------------------------

def build_gold_case(
    bank_id: str,
    commitment_id: str,
    assessment: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize a ground-truth assessment dict into a standard evaluation shape.

    Exceptions are keyed by exception_id for O(1) comparison lookups.
    """
    exceptions_by_id: dict[str, dict[str, Any]] = {}
    for exc in assessment.get("exceptions", []):
        exc_id = exc.get("exception_id")
        if exc_id is None:
            continue
        exceptions_by_id[exc_id] = {
            "applies": bool(exc.get("applies", False)),
            "mitigated": bool(exc.get("mitigated", False)),
        }

    return {
        "bank_id": bank_id,
        "commitment_id": commitment_id,
        "ground_truth": {
            "commitment": bool(assessment.get("commitment", False)),
            "exceptions": exceptions_by_id,
        },
        "ground_truth_references": assessment.get("references", []),
    }


def load_all_gold_cases() -> list[dict[str, Any]]:
    """Load gold cases for every bank defined in assessment_examples.py."""
    from examples.assessment_examples import (
        ASSESSMENT_ABN,
        ASSESSMENT_BBVA,
        ASSESSMENT_BARCLAYS,
        ASSESSMENT_HSBC,
    )

    bank_cases = [
        ("ABN", "CP.1", ASSESSMENT_ABN),
        ("HSBC", "CP.1", ASSESSMENT_HSBC),
        ("BBVA", "CP.1", ASSESSMENT_BBVA),
        ("Barclays", "CP.1", ASSESSMENT_BARCLAYS),
    ]

    return [
        build_gold_case(bank_id=bank_id, commitment_id=cid, assessment=assessment)
        for bank_id, cid, assessment in bank_cases
    ]


# ---------------------------------------------------------------------------
# Prediction loader
# ---------------------------------------------------------------------------

def load_prediction(json_path: str | Path) -> dict[str, Any]:
    """
    Load a pipeline output JSON and normalize it for evaluation.

    Extracts the resolved assessment (not raw model output) and
    retrieved chunk IDs for retrieval evaluation.
    """
    with open(json_path, "r") as f:
        raw = json.load(f)

    assessment = raw.get("assessment", {})

    exceptions_by_id: dict[str, dict[str, Any]] = {}
    for exc in assessment.get("exceptions", []):
        exc_id = exc.get("exception_id")
        if exc_id is None:
            continue
        exceptions_by_id[exc_id] = {
            "applies": bool(exc.get("applies", False)),
            "mitigated": bool(exc.get("mitigated", False)),
        }

    retrieval_results = raw.get("retrieval", {}).get("results", [])
    retrieved_chunk_ids = [
        r["chunk_id"]
        for r in retrieval_results
        if "chunk_id" in r
    ]

    return {
        "commitment_id": raw.get("commitment_id", ""),
        "prediction": {
            "commitment": bool(assessment.get("commitment", False)),
            "exceptions": exceptions_by_id,
        },
        "retrieved_chunk_ids": retrieved_chunk_ids,
    }


# ---------------------------------------------------------------------------
# Retrieval metrics
# ---------------------------------------------------------------------------

# Extracts page number from chunk IDs like "DocName-p004-c002".
_CHUNK_ID_PAGE_RE = re.compile(r"-p(\d+)-c\d+$")


def _extract_page_from_chunk_id(chunk_id: str) -> int | None:
    """Parse the page number from a chunk ID (e.g. "...-p004-c002" -> 4)."""
    match = _CHUNK_ID_PAGE_RE.search(chunk_id)
    if match:
        return int(match.group(1))
    return None


def _expand_required_pages(references: list[dict[str, Any]]) -> set[int]:
    """Expand ground-truth references into a set of required page numbers."""
    pages: set[int] = set()
    for ref in references:
        start = ref.get("page_start")
        end = ref.get("page_end")
        if start is not None and end is not None:
            pages.update(range(int(start), int(end) + 1))
    return pages


def score_retrieval(
    retrieved_chunk_ids: list[str],
    ground_truth_references: list[dict[str, Any]],
) -> dict[str, float | None]:
    """
    Compute retrieval recall and precision via page-overlap matching.

    Recall: fraction of required pages that were retrieved.
    Precision: fraction of retrieved pages that were required.
    Returns None when the denominator is zero.
    """
    required_pages = _expand_required_pages(ground_truth_references)

    retrieved_pages: set[int] = set()
    for chunk_id in retrieved_chunk_ids:
        page = _extract_page_from_chunk_id(chunk_id)
        if page is not None:
            retrieved_pages.add(page)

    overlap = retrieved_pages & required_pages

    recall = len(overlap) / len(required_pages) if required_pages else None
    precision = len(overlap) / len(retrieved_pages) if retrieved_pages else None

    return {
        "retrieval_recall": recall,
        "retrieval_precision": precision,
    }


# ---------------------------------------------------------------------------
# Synthesis metrics
# ---------------------------------------------------------------------------

def score_commitment(
    prediction: dict[str, Any],
    ground_truth: dict[str, Any],
) -> dict[str, float]:
    """Score commitment accuracy as exact match (1.0 or 0.0)."""
    pred_val = prediction.get("commitment", False)
    gold_val = ground_truth.get("commitment", False)

    return {
        "commitment_correct": 1.0 if pred_val == gold_val else 0.0,
    }


def score_exceptions(
    prediction: dict[str, Any],
    ground_truth: dict[str, Any],
) -> dict[str, float | None]:
    """
    Score exception-level accuracy across shared exception IDs.

    Returns applies_accuracy, mitigated_accuracy, and exact_accuracy
    (both fields must match). Only exceptions present in both prediction
    and ground truth are evaluated.
    """
    pred_exceptions = prediction.get("exceptions", {})
    gold_exceptions = ground_truth.get("exceptions", {})

    shared_ids = set(pred_exceptions.keys()) & set(gold_exceptions.keys())
    count = len(shared_ids)

    if count == 0:
        return {
            "exception_applies_accuracy": None,
            "exception_mitigated_accuracy": None,
            "exception_exact_accuracy": None,
            "exception_count": 0,
        }

    applies_correct = 0
    mitigated_correct = 0
    exact_correct = 0

    for exc_id in shared_ids:
        pred = pred_exceptions[exc_id]
        gold = gold_exceptions[exc_id]

        applies_match = pred["applies"] == gold["applies"]
        mitigated_match = pred["mitigated"] == gold["mitigated"]

        if applies_match:
            applies_correct += 1
        if mitigated_match:
            mitigated_correct += 1
        if applies_match and mitigated_match:
            exact_correct += 1

    return {
        "exception_applies_accuracy": applies_correct / count,
        "exception_mitigated_accuracy": mitigated_correct / count,
        "exception_exact_accuracy": exact_correct / count,
        "exception_count": count,
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def evaluate_case(
    gold_case: dict[str, Any],
    prediction: dict[str, Any],
) -> dict[str, Any]:
    """Score a single (gold case, prediction) pair across all three tiers."""
    gt = gold_case["ground_truth"]
    pred = prediction["prediction"]

    retrieval_scores = score_retrieval(
        retrieved_chunk_ids=prediction.get("retrieved_chunk_ids", []),
        ground_truth_references=gold_case.get("ground_truth_references", []),
    )
    commitment_scores = score_commitment(prediction=pred, ground_truth=gt)
    exception_scores = score_exceptions(prediction=pred, ground_truth=gt)

    return {
        "bank_id": gold_case["bank_id"],
        "commitment_id": gold_case["commitment_id"],
        **retrieval_scores,
        **commitment_scores,
        **exception_scores,
    }


def evaluate_all(
    gold_cases: list[dict[str, Any]],
    predictions_by_bank: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Evaluate all gold cases and compute per-case + aggregate metrics."""
    per_case_results: list[dict[str, Any]] = []

    for gold_case in gold_cases:
        bank_id = gold_case["bank_id"]
        if bank_id not in predictions_by_bank:
            continue

        prediction = predictions_by_bank[bank_id]
        result = evaluate_case(gold_case=gold_case, prediction=prediction)
        per_case_results.append(result)

    aggregate = _compute_aggregate(per_case_results)

    return {
        "per_case": per_case_results,
        "aggregate": aggregate,
    }


def _compute_aggregate(
    per_case_results: list[dict[str, Any]],
) -> dict[str, float | None]:
    """Compute mean of each metric across all cases, skipping None values."""
    metric_keys = [
        "retrieval_recall",
        "retrieval_precision",
        "commitment_correct",
        "exception_applies_accuracy",
        "exception_mitigated_accuracy",
        "exception_exact_accuracy",
    ]

    aggregate: dict[str, float | None] = {}

    for key in metric_keys:
        values = [r[key] for r in per_case_results if r.get(key) is not None]
        aggregate[key] = sum(values) / len(values) if values else None

    aggregate["cases_evaluated"] = len(per_case_results)

    return aggregate


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------

PREDICTION_FILES: dict[str, str] = {
    "ABN": "data/rag/final_assessment_abn_cp1.json",
    "HSBC": "data/rag/final_assessment_hsbc_cp1.json",
    "BBVA": "data/rag/final_assessment_bbva_cp1.json",
    "Barclays": "data/rag/final_assessment_barclays_cp1.json",
}


def _fmt(value: float | None, decimals: int = 2) -> str:
    """Format a metric value for display: None -> 'N/A', float -> percentage."""
    if value is None:
        return "  N/A"
    return f"{value * 100:5.{decimals}f}%"


def print_report(results: dict[str, Any]) -> None:
    """Print a human-readable evaluation report to the terminal."""
    per_case = results["per_case"]
    aggregate = results["aggregate"]

    print("\n" + "=" * 72)
    print("  RAG EVALUATION REPORT")
    print("=" * 72)

    print(f"\n{'Bank':<10} {'Ret.Rec':>8} {'Ret.Pre':>8} {'Commit':>8} "
          f"{'Exc.App':>8} {'Exc.Mit':>8} {'Exc.Ext':>8} {'#Exc':>5}")
    print("-" * 72)

    for case in per_case:
        print(
            f"{case['bank_id']:<10} "
            f"{_fmt(case['retrieval_recall']):>8} "
            f"{_fmt(case['retrieval_precision']):>8} "
            f"{_fmt(case['commitment_correct']):>8} "
            f"{_fmt(case['exception_applies_accuracy']):>8} "
            f"{_fmt(case['exception_mitigated_accuracy']):>8} "
            f"{_fmt(case['exception_exact_accuracy']):>8} "
            f"{case['exception_count']:>5}"
        )

    print("-" * 72)
    n = aggregate.get("cases_evaluated", 0)
    print(
        f"{'MEAN':<10} "
        f"{_fmt(aggregate.get('retrieval_recall')):>8} "
        f"{_fmt(aggregate.get('retrieval_precision')):>8} "
        f"{_fmt(aggregate.get('commitment_correct')):>8} "
        f"{_fmt(aggregate.get('exception_applies_accuracy')):>8} "
        f"{_fmt(aggregate.get('exception_mitigated_accuracy')):>8} "
        f"{_fmt(aggregate.get('exception_exact_accuracy')):>8} "
        f"{'':>5}"
    )
    print(f"\nCases evaluated: {n}")
    print("=" * 72 + "\n")


def main() -> None:
    """Entry point: load data, evaluate, print report."""
    gold_cases = load_all_gold_cases()
    print(f"Loaded {len(gold_cases)} gold cases.")

    predictions_by_bank: dict[str, dict[str, Any]] = {}
    for bank_id, path in PREDICTION_FILES.items():
        p = Path(path)
        if p.exists():
            predictions_by_bank[bank_id] = load_prediction(p)
            print(f"  Loaded prediction for {bank_id}: {path}")
        else:
            print(f"  Skipping {bank_id}: {path} not found")

    if not predictions_by_bank:
        print("\nNo prediction files found. Nothing to evaluate.")
        return

    results = evaluate_all(
        gold_cases=gold_cases,
        predictions_by_bank=predictions_by_bank,
    )

    print_report(results)


if __name__ == "__main__":
    main()
