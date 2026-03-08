"""
Step 4: Retrieve relevant chunks from Chroma for a specific bank + commitment.

Builds a commitment-centric query from the commitment definition and exception
taxonomy, embeds it, and queries Chroma with a mandatory bank filter.
"""

from __future__ import annotations

from typing import Any

from chromadb.api.models.Collection import Collection
from openai import OpenAI

from utils import load_commitment, load_exceptions


def build_commitment_retrieval_query(
    commitment_id: str,
    criteria_csv_path: str = "criteria/criteria.csv",
    exceptions_csv_path: str = "exceptions/exceptions.csv",
    exceptions_criteria_csv_path: str = "exceptions/exceptions_criteria.csv",
    include_exceptions: bool = True,
) -> str:
    """
    Build a retrieval query from the commitment definition, optionally
    augmented with exception definitions to surface glossary/definition pages.

    When ``include_exceptions=True``, exception definitions are appended so
    the query embedding is attracted to both commitment statements AND
    exception-related terms (e.g. "captive plants", "contractually committed").
    """
    commitment = load_commitment(commitment_id=commitment_id, csv_path=criteria_csv_path)

    parts: list[str] = []
    parts.append("ASSESSMENT TARGET")
    parts.append(f"Commitment ID: {commitment_id}")
    parts.append("")
    parts.append("COMMITMENT")
    parts.append(f"Description: {commitment.get('commitment_description', '')}")
    parts.append(f"Guidelines: {commitment.get('commitment_guidelines', '')}")
    parts.append(f"Examples: {commitment.get('commitment_examples', '')}")

    if include_exceptions:
        exception_taxonomy = load_exceptions(
            exceptions_csv_path=exceptions_csv_path,
            exceptions_criteria_csv_path=exceptions_criteria_csv_path,
            commitment_id=commitment_id,
        )
        if exception_taxonomy:
            parts.append("")
            parts.append("RELATED EXCEPTION CONCEPTS")
            for exc in exception_taxonomy:
                defn = exc.get("exception_definition", "")
                if defn:
                    parts.append(f"- {exc.get('exception_id', '')}: {defn}")

    parts.append("")
    parts.append("TASK")
    parts.append(
        "Retrieve policy text relevant to whether this commitment exists "
        "and any exceptions, exemptions, or carve-outs."
    )

    return "\n".join(parts)


def embed_query_text(
    query_text: str,
    client: OpenAI,
    model_name: str = "text-embedding-3-small",
) -> list[float]:
    """Embed the retrieval query with the same model used for chunks."""
    response = client.embeddings.create(
        model=model_name,
        input=query_text,
    )
    return response.data[0].embedding


def query_chroma_for_bank(
    collection: Collection,
    query_embedding: list[float],
    bank_id: str,
    top_k: int = 3,
) -> dict[str, Any]:
    """Query Chroma with a mandatory bank filter and return normalized results."""
    if top_k <= 0:
        raise ValueError("top_k must be a positive integer.")
    if not bank_id.strip():
        raise ValueError("bank_id is required for bank-scoped retrieval.")

    raw = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"bank_id": bank_id},
        include=["documents", "metadatas", "distances"],
    )

    ids = raw.get("ids", [[]])[0]
    documents = raw.get("documents", [[]])[0]
    metadatas = raw.get("metadatas", [[]])[0]
    distances = raw.get("distances", [[]])[0]

    results: list[dict[str, Any]] = []
    for result_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        metadata = metadata or {}
        results.append(
            {
                "id": result_id,
                "chunk_id": metadata.get("chunk_id"),
                "bank_id": metadata.get("bank_id"),
                "source_file": metadata.get("source_file"),
                "document_name": metadata.get("document_name"),
                "page": metadata.get("page"),
                "page_chunk_index": metadata.get("page_chunk_index"),
                "global_chunk_index": metadata.get("global_chunk_index"),
                "token_count": metadata.get("token_count"),
                "distance": distance,
                "text": document,
            }
        )

    return {
        "bank_id_filter": bank_id,
        "top_k": top_k,
        "retrieved_count": len(results),
        "results": results,
    }
