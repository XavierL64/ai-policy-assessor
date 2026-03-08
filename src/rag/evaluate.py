"""
RAG pipeline evaluation module.

PURPOSE:
    Compare RAG pipeline predictions against human-labeled ground truth
    across three tiers: retrieval quality, commitment accuracy, and
    exception accuracy.

DESIGN DECISIONS:
    - Ground truth comes from assessment_examples.py (hand-labeled dicts).
    - Predictions come from the JSON files the pipeline already produces.
    - Exceptions are keyed by exception_id (dict, not list) so we can
      compare by ID without relying on list ordering.
    - Retrieval evaluation uses page-overlap matching: we parse chunk IDs
      to extract page numbers and check against ground-truth page ranges.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# Add `src/` to import path so this script can be run directly from project root:
#     python src/rag/evaluate.py
_SRC_DIR = Path(__file__).resolve().parents[1]
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))


# ---------------------------------------------------------------------------
# Component 1: Gold case loader
#
# WHAT: Transforms the raw ASSESSMENT_* dicts from assessment_examples.py
#       into a standardised shape that the evaluator can compare against
#       predictions.
#
# WHY:  Ground truth and predictions live in different formats. The loader
#       normalises ground truth so every downstream comparison function
#       receives a consistent interface.
# ---------------------------------------------------------------------------

def build_gold_case(
    bank_id: str,
    commitment_id: str,
    assessment: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert a single ASSESSMENT_* dict into a gold case for evaluation.

    Parameters
    ----------
    bank_id : str
        Short identifier for the bank (e.g. "HSBC", "ABN").
    commitment_id : str
        The commitment being assessed (e.g. "CP.1").
    assessment : dict
        A raw ground-truth dict from assessment_examples.py, shaped like:
        {
            "commitment": True,
            "exceptions": [ { "exception_id": "CP.EX.1", "applies": ..., ... }, ... ],
            "references": [ { "document_name": ..., "page_start": ..., "page_end": ... }, ... ]
        }

    Returns
    -------
    dict with keys:
        - bank_id, commitment_id  (pass-through identifiers)
        - ground_truth.commitment (bool)
        - ground_truth.exceptions (dict keyed by exception_id)
        - ground_truth_references (list of reference dicts for retrieval eval)
    """

    # --- Flatten exceptions list into a dict keyed by exception_id ----------
    # This lets us look up any exception in O(1) during comparison,
    # rather than scanning two lists to match by position.
    exceptions_by_id: dict[str, dict[str, Any]] = {}
    for exc in assessment.get("exceptions", []):
        exc_id = exc.get("exception_id")
        if exc_id is None:
            continue  # skip malformed entries

        # We only keep the boolean fields we evaluate.
        # description/mitigant text is excluded (would need LLM-as-judge).
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
        # References kept separately — used only for retrieval evaluation,
        # not for synthesis accuracy scoring.
        "ground_truth_references": assessment.get("references", []),
    }


def load_all_gold_cases() -> list[dict[str, Any]]:
    """
    Load gold cases for every bank defined in assessment_examples.py.

    Returns a list of gold case dicts, one per bank.

    NOTE: We import inside the function to avoid a module-level dependency
    on assessment_examples — keeps this module testable in isolation.
    """
    # Lazy import so evaluate.py can be imported without pulling in examples
    from examples.assessment_examples import (
        ASSESSMENT_ABN,
        ASSESSMENT_BBVA,
        ASSESSMENT_BARCLAYS,
        ASSESSMENT_HSBC,
    )

    # Each tuple: (bank_id, commitment_id, ground_truth_dict)
    # All four banks are assessed against commitment CP.1.
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
# Component 2: Prediction loader
#
# WHAT: Reads a pipeline output JSON file and extracts the prediction into
#       the same normalised shape as gold cases.
#
# WHY:  Symmetry between gold and prediction shapes means every metric
#       function works identically on both sides — no special-casing.
#       We also extract retrieved chunk IDs here so retrieval evaluation
#       has everything it needs from a single load call.
# ---------------------------------------------------------------------------

def load_prediction(json_path: str | Path) -> dict[str, Any]:
    """
    Load a pipeline output JSON and normalise it for evaluation.

    Parameters
    ----------
    json_path : str or Path
        Path to a final_assessment_*.json file produced by the pipeline.
        Expected top-level keys: commitment_id, retrieval, assessment.

    Returns
    -------
    dict with keys:
        - commitment_id  (str, e.g. "CP.1")
        - prediction.commitment  (bool)
        - prediction.exceptions  (dict keyed by exception_id, mirrors gold shape)
        - retrieved_chunk_ids    (list[str], for retrieval evaluation)
    """
    # --- Read the raw JSON from disk ---------------------------------------
    with open(json_path, "r") as f:
        raw = json.load(f)

    # --- Extract the assessment block --------------------------------------
    # The pipeline nests the final result under "assessment".
    # "assessment_model_output" is the raw LLM response before citation
    # resolution — we evaluate the resolved version only.
    assessment = raw.get("assessment", {})

    # --- Flatten exceptions into a dict keyed by exception_id --------------
    # Identical logic to build_gold_case so both sides have the same shape.
    exceptions_by_id: dict[str, dict[str, Any]] = {}
    for exc in assessment.get("exceptions", []):
        exc_id = exc.get("exception_id")
        if exc_id is None:
            continue
        exceptions_by_id[exc_id] = {
            "applies": bool(exc.get("applies", False)),
            "mitigated": bool(exc.get("mitigated", False)),
        }

    # --- Extract retrieved chunk IDs for retrieval evaluation --------------
    # These come from retrieval.results[].chunk_id — the IDs of chunks
    # the vector store returned before synthesis.
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
# Component 3: Retrieval metrics
#
# WHAT: Measures whether the vector store returned the chunks that contain
#       the evidence a human used to make the assessment.
#
# WHY:  In a RAG pipeline, retrieval is the bottleneck — if the right
#       chunks never reach the LLM, synthesis cannot succeed no matter
#       how good the model is. Measuring retrieval separately lets us
#       diagnose WHERE failures originate.
#
# HOW:  We use page-overlap matching. Ground-truth references specify
#       document_name + page_start/page_end. Retrieved chunk IDs encode
#       the page number (e.g. "DocName-p004-c002" → page 4). We check
#       whether retrieved pages cover the required pages.
# ---------------------------------------------------------------------------

# Regex to extract page number from chunk IDs like "DocName-p004-c002".
# The pattern captures the digits after "-p" and before "-c".
_CHUNK_ID_PAGE_RE = re.compile(r"-p(\d+)-c\d+$")


def _extract_page_from_chunk_id(chunk_id: str) -> int | None:
    """
    Parse the page number from a chunk ID.

    Chunk IDs follow the convention: "{document_name}-p{page:03d}-c{chunk:03d}"
    e.g. "Thermal Coal Phase-out Policy (Feb 2025)-p004-c002" → 4

    Returns None if the chunk ID doesn't match the expected pattern.
    """
    match = _CHUNK_ID_PAGE_RE.search(chunk_id)
    if match:
        return int(match.group(1))
    return None


def _expand_required_pages(references: list[dict[str, Any]]) -> set[int]:
    """
    Expand ground-truth references into a set of required page numbers.

    Each reference has page_start and page_end. We expand the range
    inclusive on both ends:
        {"page_start": 8, "page_end": 10}  →  {8, 9, 10}

    Multiple references may overlap — the set deduplicates automatically.
    """
    pages: set[int] = set()
    for ref in references:
        start = ref.get("page_start")
        end = ref.get("page_end")
        if start is not None and end is not None:
            # range() is exclusive on the upper bound, so +1 to include end
            pages.update(range(int(start), int(end) + 1))
    return pages


def score_retrieval(
    retrieved_chunk_ids: list[str],
    ground_truth_references: list[dict[str, Any]],
) -> dict[str, float | None]:
    """
    Compute retrieval recall and precision via page-overlap matching.

    Parameters
    ----------
    retrieved_chunk_ids : list[str]
        Chunk IDs returned by the vector store (from prediction loader).
    ground_truth_references : list[dict]
        Reference dicts from the gold case, each with document_name,
        page_start, page_end.

    Returns
    -------
    dict with keys:
        - retrieval_recall    : float or None
            |retrieved ∩ required| / |required|
            "Of the pages we needed, what fraction did we retrieve?"
            None if there are no required pages (can't divide by zero).

        - retrieval_precision : float or None
            |retrieved ∩ required| / |retrieved|
            "Of the pages we retrieved, what fraction were needed?"
            None if nothing was retrieved.
    """
    # --- Build the set of required pages from ground truth -----------------
    required_pages = _expand_required_pages(ground_truth_references)

    # --- Build the set of retrieved pages from chunk IDs -------------------
    retrieved_pages: set[int] = set()
    for chunk_id in retrieved_chunk_ids:
        page = _extract_page_from_chunk_id(chunk_id)
        if page is not None:
            retrieved_pages.add(page)

    # --- Compute overlap ---------------------------------------------------
    overlap = retrieved_pages & required_pages

    # --- Recall: what fraction of required pages did we retrieve? ----------
    # None when there are no required pages — avoids division by zero
    # and signals "retrieval eval not applicable for this case".
    recall = len(overlap) / len(required_pages) if required_pages else None

    # --- Precision: what fraction of retrieved pages were required? --------
    # None when nothing was retrieved.
    precision = len(overlap) / len(retrieved_pages) if retrieved_pages else None

    return {
        "retrieval_recall": recall,
        "retrieval_precision": precision,
    }


# ---------------------------------------------------------------------------
# Component 4: Synthesis metrics
#
# WHAT: Measures whether the LLM produced the correct assessment GIVEN
#       the chunks it received.
#
# WHY:  This is the second half of the RAG diagnostic split. If retrieval
#       recall is high but commitment/exception accuracy is low, the
#       problem is in the prompt or model — not the vector store.
#
# Two sub-components:
#   a) Commitment accuracy — did the LLM get the top-level bool right?
#   b) Exception accuracy  — per-exception comparison of applies/mitigated.
# ---------------------------------------------------------------------------

def score_commitment(
    prediction: dict[str, Any],
    ground_truth: dict[str, Any],
) -> dict[str, float]:
    """
    Score commitment accuracy: simple exact match.

    Parameters
    ----------
    prediction : dict
        The "prediction" sub-dict from load_prediction(), containing
        {"commitment": bool, "exceptions": {...}}.
    ground_truth : dict
        The "ground_truth" sub-dict from build_gold_case(), same shape.

    Returns
    -------
    dict with:
        - commitment_correct : float (1.0 if match, 0.0 if not)

    WHY a float instead of bool:
        So we can average across cases directly — mean([1.0, 0.0, 1.0]) = 0.67
        is the aggregate accuracy. With bools you'd need to cast first.
    """
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
    Score exception-level accuracy across all exception IDs.

    Compares only exception IDs that appear in BOTH prediction and ground
    truth. If the model invents an ID or misses one, that exception is
    excluded from scoring (not penalised as wrong) — we measure accuracy
    on the shared set only.

    Parameters
    ----------
    prediction : dict
        {"commitment": ..., "exceptions": {"CP.EX.1": {"applies": ..., "mitigated": ...}, ...}}
    ground_truth : dict
        Same shape.

    Returns
    -------
    dict with:
        - exception_applies_accuracy   : float or None
            Fraction of shared exceptions where `applies` matched.
        - exception_mitigated_accuracy : float or None
            Fraction of shared exceptions where `mitigated` matched.
        - exception_exact_accuracy     : float or None
            Fraction where BOTH applies AND mitigated matched.
            This is the strictest metric — the one that matters most
            for a ratings agency because a wrong applies or wrong
            mitigated both change the final rating.
        - exception_count              : int
            Number of shared exceptions evaluated (denominator).

    All accuracy values are None when exception_count is 0 (nothing to
    compare — e.g. both sides have commitment=false so exceptions are empty).
    """
    pred_exceptions = prediction.get("exceptions", {})
    gold_exceptions = ground_truth.get("exceptions", {})

    # --- Find shared exception IDs -----------------------------------------
    # We only score exceptions present on both sides. This avoids penalising
    # the model for ID format mismatches we haven't caught, while still
    # measuring accuracy on every exception we CAN compare.
    shared_ids = set(pred_exceptions.keys()) & set(gold_exceptions.keys())
    count = len(shared_ids)

    if count == 0:
        return {
            "exception_applies_accuracy": None,
            "exception_mitigated_accuracy": None,
            "exception_exact_accuracy": None,
            "exception_count": 0,
        }

    # --- Compare each shared exception field-by-field ----------------------
    applies_correct = 0
    mitigated_correct = 0
    exact_correct = 0

    for exc_id in shared_ids:
        pred = pred_exceptions[exc_id]
        gold = gold_exceptions[exc_id]

        # Check each boolean field independently
        applies_match = pred["applies"] == gold["applies"]
        mitigated_match = pred["mitigated"] == gold["mitigated"]

        if applies_match:
            applies_correct += 1
        if mitigated_match:
            mitigated_correct += 1
        # Exact = both fields must match for this exception
        if applies_match and mitigated_match:
            exact_correct += 1

    return {
        "exception_applies_accuracy": applies_correct / count,
        "exception_mitigated_accuracy": mitigated_correct / count,
        "exception_exact_accuracy": exact_correct / count,
        "exception_count": count,
    }


# ---------------------------------------------------------------------------
# Component 5: Orchestration — evaluate one case and evaluate all cases
#
# WHAT: Ties together the loaders and scorers into two entry points:
#       - evaluate_case()  → scores one (gold, prediction) pair
#       - evaluate_all()   → scores every bank, returns per-case + aggregate
#
# WHY:  Keeps scoring functions pure (they don't know about files or
#       lists of banks). Orchestration handles the plumbing: loading,
#       matching gold to prediction, collecting results, averaging.
# ---------------------------------------------------------------------------

def evaluate_case(
    gold_case: dict[str, Any],
    prediction: dict[str, Any],
) -> dict[str, Any]:
    """
    Score a single (gold case, prediction) pair across all three tiers.

    Parameters
    ----------
    gold_case : dict
        Output of build_gold_case(). Contains ground_truth and
        ground_truth_references.
    prediction : dict
        Output of load_prediction(). Contains prediction and
        retrieved_chunk_ids.

    Returns
    -------
    Flat dict combining identifiers and all metric scores:
        {
            "bank_id": "HSBC",
            "commitment_id": "CP.1",
            # Tier 1: retrieval
            "retrieval_recall": 0.25,
            "retrieval_precision": 0.33,
            # Tier 2: commitment
            "commitment_correct": 1.0,
            # Tier 3: exceptions
            "exception_applies_accuracy": 0.86,
            "exception_mitigated_accuracy": 0.93,
            "exception_exact_accuracy": 0.86,
            "exception_count": 14,
        }

    WHY a flat dict:
        Easy to convert to a CSV row or pandas DataFrame. Nested dicts
        would require extra unpacking logic for every consumer.
    """
    gt = gold_case["ground_truth"]
    pred = prediction["prediction"]

    # --- Tier 1: Retrieval -------------------------------------------------
    retrieval_scores = score_retrieval(
        retrieved_chunk_ids=prediction.get("retrieved_chunk_ids", []),
        ground_truth_references=gold_case.get("ground_truth_references", []),
    )

    # --- Tier 2: Commitment ------------------------------------------------
    commitment_scores = score_commitment(prediction=pred, ground_truth=gt)

    # --- Tier 3: Exceptions ------------------------------------------------
    exception_scores = score_exceptions(prediction=pred, ground_truth=gt)

    # --- Merge everything into one flat dict -------------------------------
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
    """
    Evaluate all gold cases and compute per-case + aggregate metrics.

    Parameters
    ----------
    gold_cases : list[dict]
        Output of load_all_gold_cases().
    predictions_by_bank : dict[str, dict]
        Mapping of bank_id → prediction dict (output of load_prediction).
        Only banks present in this dict will be evaluated.

    Returns
    -------
    dict with:
        - "per_case": list of per-case score dicts (from evaluate_case)
        - "aggregate": dict of mean scores across all evaluated cases

    WHY predictions_by_bank is a dict (not a list):
        We need to match each gold case to its prediction by bank_id.
        A dict makes this O(1) per case. If we used two lists, we'd
        need nested loops or sorting to align them.
    """
    per_case_results: list[dict[str, Any]] = []

    for gold_case in gold_cases:
        bank_id = gold_case["bank_id"]

        # --- Skip banks we don't have predictions for ----------------------
        # This lets us evaluate a subset (e.g. only HSBC) without errors.
        if bank_id not in predictions_by_bank:
            continue

        prediction = predictions_by_bank[bank_id]
        result = evaluate_case(gold_case=gold_case, prediction=prediction)
        per_case_results.append(result)

    # --- Compute aggregate metrics -----------------------------------------
    # For each numeric metric, compute the mean across all evaluated cases.
    # None values are excluded (they mean "not applicable for this case").
    aggregate = _compute_aggregate(per_case_results)

    return {
        "per_case": per_case_results,
        "aggregate": aggregate,
    }


def _compute_aggregate(
    per_case_results: list[dict[str, Any]],
) -> dict[str, float | None]:
    """
    Compute mean of each metric across all cases, skipping None values.

    Returns None for a metric if no cases had a value for it.

    WHY skip None instead of treating as 0:
        None means "not applicable" (e.g. no ground-truth references for
        retrieval). Treating it as 0 would drag down the average unfairly.
        Skipping it gives the true average over cases where the metric
        is actually measurable.
    """
    # The metrics we want to aggregate (all numeric fields from evaluate_case)
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
        # Collect non-None values for this metric across all cases
        values = [r[key] for r in per_case_results if r.get(key) is not None]

        # Mean if we have values, None if no case produced this metric
        aggregate[key] = sum(values) / len(values) if values else None

    # Also include how many cases were evaluated (useful context)
    aggregate["cases_evaluated"] = len(per_case_results)

    return aggregate


# ---------------------------------------------------------------------------
# Component 6: Runner
#
# WHAT: A __main__ entry point that loads gold cases + prediction files,
#       runs evaluate_all(), and prints a readable terminal report.
#
# WHY:  Makes evaluation a single command:
#           cd src && python -m rag.evaluate
#       No notebooks, no manual wiring. You run it, you see results.
#
# DESIGN: Prediction files are mapped to bank IDs via a simple dict.
#         This is explicit and easy to extend when you add more banks.
#         A fancier approach (scanning a directory, parsing filenames)
#         would be fragile and harder to debug.
# ---------------------------------------------------------------------------

# Mapping of bank_id → path to the prediction JSON file.
# Paths are relative to the project root (where you run from).
# Add new banks here as you generate predictions for them.
PREDICTION_FILES: dict[str, str] = {
    "ABN": "data/rag/final_assessment_abn_cp1.json",
    "HSBC": "data/rag/final_assessment_hsbc_cp1.json",
    "BBVA": "data/rag/final_assessment_bbva_cp1.json",
    "Barclays": "data/rag/final_assessment_barclays_cp1.json",
}


def _fmt(value: float | None, decimals: int = 2) -> str:
    """Format a metric value for display: None → 'N/A', float → percentage."""
    if value is None:
        return "  N/A"
    return f"{value * 100:5.{decimals}f}%"


def print_report(results: dict[str, Any]) -> None:
    """
    Print a human-readable evaluation report to the terminal.

    Shows per-case results in a table, then aggregate summary.
    """
    per_case = results["per_case"]
    aggregate = results["aggregate"]

    # --- Header ------------------------------------------------------------
    print("\n" + "=" * 72)
    print("  RAG EVALUATION REPORT")
    print("=" * 72)

    # --- Per-case table ----------------------------------------------------
    # Each row is one bank. Columns are the metrics.
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

    # --- Aggregate summary -------------------------------------------------
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
    """
    Entry point: load data, evaluate, print report.
    """
    # --- Load gold cases ---------------------------------------------------
    gold_cases = load_all_gold_cases()
    print(f"Loaded {len(gold_cases)} gold cases.")

    # --- Load predictions --------------------------------------------------
    # Only load files that exist — gracefully handle missing predictions.
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

    # --- Run evaluation ----------------------------------------------------
    results = evaluate_all(
        gold_cases=gold_cases,
        predictions_by_bank=predictions_by_bank,
    )

    # --- Print report ------------------------------------------------------
    print_report(results)


if __name__ == "__main__":
    main()
