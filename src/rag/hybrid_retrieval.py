"""
Hybrid retrieval: BM25 keyword search + vector search, merged via
Reciprocal Rank Fusion (RRF).

WHAT this module does:
- Runs BM25 keyword search over chunk text for a given bank.
- Merges BM25 results with Chroma vector results using RRF.
- Returns a unified ranked list of chunks.

WHY this module exists:
- Pure vector search misses glossary/definition chunks that contain
  exact terms (e.g. "exempted activities", "captive plants") but
  embed far from commitment-focused queries.
- BM25 finds exact keyword matches regardless of embedding similarity.
- RRF combines both signals without requiring score normalization —
  it only uses rank positions, making it robust across different
  scoring scales.

HOW RRF works:
    For each chunk, compute: score = sum(1 / (k + rank_i))
    where rank_i is the chunk's rank in result list i, and k is a
    smoothing constant (typically 60). Chunks appearing in multiple
    lists get boosted. Chunks in only one list still contribute.
"""

from __future__ import annotations

import json
from typing import Any

from rank_bm25 import BM25Okapi


# ---------------------------------------------------------------------------
# BM25 search over chunk text
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """
    Simple whitespace + lowercase tokenizer for BM25.

    BM25 works on token overlap, so we lowercase everything for
    case-insensitive matching. No stemming or stopword removal —
    keeping it simple for this prototype.
    """
    return text.lower().split()


def load_bank_chunks(chunks_jsonl_path: str, bank_id: str) -> list[dict]:
    """
    Load all chunks for a specific bank from the chunks JSONL file.

    We read from the JSONL (not Chroma) because BM25 needs the raw
    text corpus in memory to build its index.
    """
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
    """
    Run BM25 keyword search over a bank's chunks.

    Parameters
    ----------
    query : str
        The retrieval query text (same query used for vector search).
    bank_chunks : list[dict]
        All chunks for one bank (from load_bank_chunks).
    top_n : int
        Number of top BM25 results to return.

    Returns
    -------
    list of chunk dicts, ordered by BM25 score (highest first).
    Each dict gets an added "bm25_score" field.
    """
    if not bank_chunks:
        return []

    # Build BM25 index from chunk texts
    corpus = [_tokenize(c["text"]) for c in bank_chunks]
    bm25 = BM25Okapi(corpus)

    # Score all chunks against the query
    query_tokens = _tokenize(query)
    scores = bm25.get_scores(query_tokens)

    # Pair chunks with scores, sort by score descending
    scored = list(zip(bank_chunks, scores))
    scored.sort(key=lambda x: x[1], reverse=True)

    # Return top_n with scores attached
    results = []
    for chunk, score in scored[:top_n]:
        result = dict(chunk)
        result["bm25_score"] = float(score)
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion (RRF)
# ---------------------------------------------------------------------------

def reciprocal_rank_fusion(
    ranked_lists: list[list[dict]],
    id_key: str = "chunk_id",
    k: int = 60,
) -> list[dict]:
    """
    Merge multiple ranked lists using Reciprocal Rank Fusion.

    Parameters
    ----------
    ranked_lists : list[list[dict]]
        Each inner list is a ranked sequence of chunk dicts (best first).
    id_key : str
        The field used to identify unique chunks across lists.
    k : int
        Smoothing constant. Higher k reduces the influence of rank
        position differences. 60 is the standard value from the
        original RRF paper (Cormack et al., 2009).

    Returns
    -------
    list of chunk dicts, sorted by fused RRF score (highest first).

    HOW IT WORKS:
        For chunk C appearing at rank r1 in list 1 and rank r2 in list 2:
            rrf_score(C) = 1/(k + r1) + 1/(k + r2)

        A chunk ranked #1 in both lists:  1/61 + 1/61 = 0.0328
        A chunk ranked #1 in one list:    1/61       = 0.0164
        A chunk ranked #10 in both lists: 1/70 + 1/70 = 0.0286

        So being in both lists matters more than rank position —
        this is why RRF is good at surfacing chunks that are relevant
        by BOTH keyword and semantic criteria.
    """
    # Accumulate RRF scores per chunk_id
    rrf_scores: dict[str, float] = {}
    # Keep the chunk data from whichever list we see it in first
    chunk_data: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, chunk in enumerate(ranked_list, start=1):
            cid = chunk.get(id_key, "")
            if not cid:
                continue

            # RRF formula: 1 / (k + rank)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (k + rank)

            # Store chunk data on first encounter
            if cid not in chunk_data:
                chunk_data[cid] = chunk

    # Sort by RRF score descending
    sorted_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

    # Build final list with RRF score attached
    results = []
    for cid in sorted_ids:
        result = dict(chunk_data[cid])
        result["rrf_score"] = rrf_scores[cid]
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Hybrid retrieval: vector + BM25 + RRF
# ---------------------------------------------------------------------------

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

    Parameters
    ----------
    query : str
        The retrieval query text.
    query_embedding : list[float]
        Embedded query vector for Chroma search.
    collection : Chroma Collection
        The Chroma collection to search.
    bank_id : str
        Bank filter for Chroma query.
    bank_chunks : list[dict]
        All chunks for this bank (for BM25 search).
    top_k : int
        Final number of chunks to return after RRF merging.
    vector_candidates : int
        Number of candidates to pull from vector search before fusion.
    bm25_candidates : int
        Number of candidates to pull from BM25 before fusion.

    Returns
    -------
    list of top_k chunk dicts, ranked by RRF score.
    """
    # --- Vector search via Chroma ------------------------------------------
    raw = collection.query(
        query_embeddings=[query_embedding],
        n_results=vector_candidates,
        where={"bank_id": bank_id},
        include=["documents", "metadatas", "distances"],
    )

    # Unpack Chroma's nested list format into flat chunk dicts
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

    # --- BM25 keyword search -----------------------------------------------
    bm25_results = bm25_search(
        query=query,
        bank_chunks=bank_chunks,
        top_n=bm25_candidates,
    )

    # --- Reciprocal Rank Fusion --------------------------------------------
    fused = reciprocal_rank_fusion(
        ranked_lists=[vector_results, bm25_results],
        id_key="chunk_id",
    )

    # Return top_k after fusion
    return fused[:top_k]
