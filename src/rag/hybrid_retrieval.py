"""
Hybrid retrieval: BM25 keyword search + vector search, merged via
Reciprocal Rank Fusion (RRF).

Pure vector search misses glossary/definition chunks that contain exact
terms but embed far from commitment-focused queries. BM25 finds exact
keyword matches, and RRF combines both signals using only rank positions,
making it robust across different scoring scales.
"""

from __future__ import annotations

import json
from typing import Any

from rank_bm25 import BM25Okapi


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + lowercase tokenizer for BM25."""
    return text.lower().split()


def load_bank_chunks(chunks_jsonl_path: str, bank_id: str) -> list[dict]:
    """Load all chunks for a specific bank from the chunks JSONL file."""
    chunks = []
    with open(chunks_jsonl_path, "r") as f:
        for line in f:
            record = json.loads(line)
            if record.get("bank_id") == bank_id:
                chunks.append(record)
    return chunks


def bm25_search(
    query: str,
    bank_chunks: list[dict],
    top_n: int = 20,
) -> list[dict]:
    """Run BM25 keyword search over a bank's chunks, returning top_n results."""
    if not bank_chunks:
        return []

    corpus = [_tokenize(c["text"]) for c in bank_chunks]
    bm25 = BM25Okapi(corpus)

    query_tokens = _tokenize(query)
    scores = bm25.get_scores(query_tokens)

    scored = list(zip(bank_chunks, scores))
    scored.sort(key=lambda x: x[1], reverse=True)

    results = []
    for chunk, score in scored[:top_n]:
        result = dict(chunk)
        result["bm25_score"] = float(score)
        results.append(result)

    return results


def reciprocal_rank_fusion(
    ranked_lists: list[list[dict]],
    id_key: str = "chunk_id",
    k: int = 60,
) -> list[dict]:
    """
    Merge multiple ranked lists using Reciprocal Rank Fusion.

    For each chunk: rrf_score = sum(1 / (k + rank_i)) across all lists.
    k=60 is the standard smoothing constant (Cormack et al., 2009).
    Chunks appearing in multiple lists are boosted, making RRF effective
    at surfacing results relevant by both keyword and semantic criteria.
    """
    rrf_scores: dict[str, float] = {}
    chunk_data: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, chunk in enumerate(ranked_list, start=1):
            cid = chunk.get(id_key, "")
            if not cid:
                continue

            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (k + rank)

            if cid not in chunk_data:
                chunk_data[cid] = chunk

    sorted_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

    results = []
    for cid in sorted_ids:
        result = dict(chunk_data[cid])
        result["rrf_score"] = rrf_scores[cid]
        results.append(result)

    return results


def hybrid_retrieve(
    query: str,
    query_embedding: list[float],
    collection,
    bank_id: str,
    bank_chunks: list[dict],
    top_k: int = 5,
    vector_candidates: int = 20,
    bm25_candidates: int = 20,
) -> list[dict]:
    """
    Run hybrid retrieval combining vector search and BM25 via RRF.

    Pulls ``vector_candidates`` from Chroma and ``bm25_candidates`` from
    BM25, fuses them with RRF, and returns the top_k merged results.
    """
    # Vector search via Chroma
    raw = collection.query(
        query_embeddings=[query_embedding],
        n_results=vector_candidates,
        where={"bank_id": bank_id},
        include=["documents", "metadatas", "distances"],
    )

    ids = raw.get("ids", [[]])[0]
    documents = raw.get("documents", [[]])[0]
    metadatas = raw.get("metadatas", [[]])[0]
    distances = raw.get("distances", [[]])[0]

    vector_results = []
    for rid, doc, meta, dist in zip(ids, documents, metadatas, distances):
        meta = meta or {}
        vector_results.append({
            "id": rid,
            "chunk_id": meta.get("chunk_id"),
            "bank_id": meta.get("bank_id"),
            "source_file": meta.get("source_file"),
            "document_name": meta.get("document_name"),
            "page": meta.get("page"),
            "page_chunk_index": meta.get("page_chunk_index"),
            "global_chunk_index": meta.get("global_chunk_index"),
            "token_count": meta.get("token_count"),
            "section_type": meta.get("section_type", "general"),
            "distance": dist,
            "text": doc,
        })

    # BM25 keyword search
    bm25_results = bm25_search(
        query=query,
        bank_chunks=bank_chunks,
        top_n=bm25_candidates,
    )

    # Reciprocal Rank Fusion
    fused = reciprocal_rank_fusion(
        ranked_lists=[vector_results, bm25_results],
        id_key="chunk_id",
    )

    return fused[:top_k]
