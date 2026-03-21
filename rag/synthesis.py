"""
Step 5: One-call synthesis with programmatic citations.

Feeds retrieved chunks to the LLM as a structured catalog, asks the model
to return evidence as chunk IDs only, then resolves those IDs into citation
objects deterministically in Python.
"""

from __future__ import annotations

import json
import re
from typing import Any

from config import assessment_date
from utils import get_openai_client, load_commitment, load_exceptions, openai_retry

from .function_schema import tools
from .synthesis_prompt import ROLE, TASK, INPUTS, STEPS, RULES

MAX_EXCERPT_CHARS = 280


def build_chunk_catalog(retrieval_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a compact, model-facing chunk catalog from retrieval results."""
    catalog: list[dict[str, Any]] = []
    for result in retrieval_results:
        catalog.append(
            {
                "chunk_id": str(result.get("chunk_id", "")),
                "document_name": str(result.get("document_name", "")),
                "page": int(result.get("page", 0)),
                "text": str(result.get("text", "")),
            }
        )
    return catalog


def build_chunk_lookup(chunk_catalog: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Build chunk_id -> chunk record mapping for fast citation resolution."""
    return {
        item["chunk_id"]: item
        for item in chunk_catalog
        if isinstance(item.get("chunk_id"), str) and item.get("chunk_id")
    }


def _sanitize_evidence_ids(candidate_ids: Any, valid_ids: set[str]) -> list[str]:
    """Keep only valid chunk IDs, preserving order and removing duplicates."""
    if not isinstance(candidate_ids, list):
        return []

    cleaned: list[str] = []
    seen: set[str] = set()
    for value in candidate_ids:
        chunk_id = str(value)
        if chunk_id in valid_ids and chunk_id not in seen:
            cleaned.append(chunk_id)
            seen.add(chunk_id)
    return cleaned


def _build_excerpt(text: str, max_chars: int = MAX_EXCERPT_CHARS) -> str:
    """Build a deterministic short excerpt from chunk text."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars].rstrip() + "..."


def _build_references_from_ids(
    evidence_ids: list[str],
    chunk_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Resolve evidence chunk IDs into citation objects."""
    references: list[dict[str, Any]] = []
    for chunk_id in evidence_ids:
        chunk = chunk_lookup.get(chunk_id)
        if not chunk:
            continue
        page = int(chunk.get("page", 0))
        references.append(
            {
                "chunk_id": chunk_id,
                "excerpt": _build_excerpt(str(chunk.get("text", ""))),
                "document_name": str(chunk.get("document_name", "")),
                "page_start": page,
                "page_end": page,
            }
        )
    return references


def resolve_model_output_with_programmatic_citations(
    model_output: dict[str, Any],
    chunk_lookup: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """
    Convert model output (IDs only) into final assessment with resolved citations.

    Validates evidence IDs against the chunk catalog and builds reference
    objects with excerpts and page numbers.
    """
    valid_ids = set(chunk_lookup.keys())

    commitment = bool(model_output.get("commitment", False))
    commitment_ids = _sanitize_evidence_ids(
        model_output.get("commitment_evidence_chunk_ids", []), valid_ids
    )

    raw_exceptions = model_output.get("exceptions", [])
    resolved_exceptions: list[dict[str, Any]] = []
    positive_exception_evidence_ids: list[str] = []

    if isinstance(raw_exceptions, list):
        for item in raw_exceptions:
            item = item if isinstance(item, dict) else {}
            applies = bool(item.get("applies", False))
            mitigated = bool(item.get("mitigated", False))
            evidence_ids = _sanitize_evidence_ids(item.get("evidence_chunk_ids", []), valid_ids)

            if applies or mitigated:
                for chunk_id in evidence_ids:
                    if chunk_id not in positive_exception_evidence_ids:
                        positive_exception_evidence_ids.append(chunk_id)

            resolved_exceptions.append(
                {
                    "exception_id": item.get("exception_id"),
                    "applies": applies,
                    "description": item.get("description"),
                    "mitigated": mitigated,
                    "mitigant": item.get("mitigant"),
                    "evidence_chunk_ids": evidence_ids,
                }
            )

    # Reference IDs: commitment evidence first, then exception evidence.
    reference_ids: list[str] = []
    if commitment:
        reference_ids.extend(commitment_ids)
    for chunk_id in positive_exception_evidence_ids:
        if chunk_id not in reference_ids:
            reference_ids.append(chunk_id)

    references = _build_references_from_ids(reference_ids, chunk_lookup)

    return {
        "commitment": commitment,
        "commitment_evidence_chunk_ids": commitment_ids if commitment else [],
        "exceptions": resolved_exceptions if commitment else [],
        "references": references,
    }


def build_synthesis_user_input(
    commitment_id: str,
    commitment: dict[str, str],
    exception_taxonomy: list[dict[str, Any]],
    chunk_catalog: list[dict[str, Any]],
) -> str:
    """Build structured user payload for the synthesis LLM call."""
    commitment_description = commitment.get("commitment_description", "")
    commitment_guidelines = commitment.get("commitment_guidelines", "")
    commitment_examples = commitment.get("commitment_examples", "")

    return f"""
Chunk catalog to assess:
<<<CHUNK_CATALOG_JSON>>>
{json.dumps(chunk_catalog)}
<<<END_CHUNK_CATALOG_JSON>>>

Assessment date:
<<<ASSESSMENT_DATE>>>
{assessment_date}
<<<END_ASSESSMENT_DATE>>>

Commitment ID:
<<<COMMITMENT_ID>>>
{commitment_id}
<<<END_COMMITMENT_ID>>>

Commitment description:
<<<COMMITMENT_DESCRIPTION>>>
{commitment_description}
<<<END_COMMITMENT_DESCRIPTION>>>

Commitment guidelines:
<<<COMMITMENT_GUIDELINES>>>
{commitment_guidelines}
<<<END_COMMITMENT_GUIDELINES>>>

Commitment examples:
<<<COMMITMENT_EXAMPLES>>>
{commitment_examples}
<<<END_COMMITMENT_EXAMPLES>>>

Exception taxonomy:
<<<EXCEPTION_TAXONOMY>>>
{json.dumps(exception_taxonomy)}
<<<END_EXCEPTION_TAXONOMY>>>
"""


def synthesize_assessment_from_retrieval(
    retrieval_payload: dict[str, Any],
    model_name: str = "gpt-4.1",
    criteria_csv_path: str = "criteria/criteria.csv",
    exceptions_csv_path: str = "exceptions/exceptions.csv",
    exceptions_criteria_csv_path: str = "exceptions/exceptions_criteria.csv",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """
    Run one-call synthesis from a Step 4 retrieval payload.

    Returns (raw_model_output, resolved_assessment, total_tokens_used).
    """
    commitment_id = retrieval_payload.get("commitment_id")
    if not commitment_id:
        raise ValueError("retrieval_payload must contain `commitment_id`.")

    retrieval = retrieval_payload.get("retrieval", {})
    retrieval_results = retrieval.get("results", [])
    if not isinstance(retrieval_results, list):
        raise ValueError("retrieval_payload.retrieval.results must be a list.")

    commitment = load_commitment(commitment_id=commitment_id, csv_path=criteria_csv_path)
    exception_taxonomy = load_exceptions(
        exceptions_csv_path=exceptions_csv_path,
        exceptions_criteria_csv_path=exceptions_criteria_csv_path,
        commitment_id=commitment_id,
    )

    chunk_catalog = build_chunk_catalog(retrieval_results)
    chunk_lookup = build_chunk_lookup(chunk_catalog)
    user_input = build_synthesis_user_input(
        commitment_id=commitment_id,
        commitment=commitment,
        exception_taxonomy=exception_taxonomy,
        chunk_catalog=chunk_catalog,
    )

    messages = [
        {"role": "system", "content": ROLE + TASK + INPUTS + STEPS + RULES},
        {"role": "user", "content": user_input},
    ]

    client = get_openai_client()
    total_tokens_used = 0

    @openai_retry
    def _run_completion() -> dict[str, Any]:
        nonlocal total_tokens_used
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=tools,
            tool_choice={
                "type": "function",
                "function": {"name": "assess_commitment_exceptions_with_evidence_ids"},
            },
            temperature=0,
        )
        total_tokens_used += response.usage.total_tokens
        raw_output = response.choices[0].message.tool_calls[0].function.arguments
        return json.loads(raw_output)

    raw_model_output = _run_completion()
    resolved_assessment = resolve_model_output_with_programmatic_citations(
        model_output=raw_model_output,
        chunk_lookup=chunk_lookup,
    )
    return raw_model_output, resolved_assessment, total_tokens_used
