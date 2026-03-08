"""
Step 4 CLI: retrieve relevant chunks for each bank + commitment from Chroma.

Run from project root:
    python src/rag/retrieve_chunks.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
COMMITMENT_ID = "CP.1"
BANK_IDS = ["ABN", "HSBC", "BBVA", "Barclays"]
TOP_K = 5
EMBEDDING_MODEL = "text-embedding-3-small"
CRITERIA_CSV = "criteria/criteria.csv"
EXCEPTIONS_CSV = "exceptions/exceptions.csv"
EXCEPTIONS_CRITERIA_CSV = "exceptions/exceptions_criteria.csv"
PERSIST_DIR = "data/rag/chroma_db"
COLLECTION = "policy_chunks"
CHUNKS_JSONL = "data/rag/chunks.jsonl"
OUTPUT_DIR = "data/rag"
HYBRID_RETRIEVAL = True
# ---------------------------------------------------------------------------

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rag.retrieval import (  # noqa: E402
    build_commitment_retrieval_query,
    embed_query_text,
    query_chroma_for_bank,
)
from rag.vector_store import get_or_create_persistent_collection  # noqa: E402
from utils import get_openai_client  # noqa: E402


def main() -> None:
    composite_query = build_commitment_retrieval_query(
        commitment_id=COMMITMENT_ID,
        criteria_csv_path=CRITERIA_CSV,
        exceptions_csv_path=EXCEPTIONS_CSV,
        exceptions_criteria_csv_path=EXCEPTIONS_CRITERIA_CSV,
    )

    client = get_openai_client()
    query_embedding = embed_query_text(
        query_text=composite_query,
        client=client,
        model_name=EMBEDDING_MODEL,
    )

    collection = get_or_create_persistent_collection(
        persist_directory=PERSIST_DIR,
        collection_name=COLLECTION,
    )

    if HYBRID_RETRIEVAL:
        from rag.hybrid_retrieval import hybrid_retrieve, load_bank_chunks

    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    mode = "hybrid (BM25 + vector + RRF)" if HYBRID_RETRIEVAL else "vector-only"
    print(f"Retrieval mode: {mode}")

    for bank_id in BANK_IDS:

        if HYBRID_RETRIEVAL:
            bank_chunks = load_bank_chunks(CHUNKS_JSONL, bank_id)
            results = hybrid_retrieve(
                query=composite_query,
                query_embedding=query_embedding,
                collection=collection,
                bank_id=bank_id,
                bank_chunks=bank_chunks,
                top_k=TOP_K,
            )

            retrieval = {
                "bank_id_filter": bank_id,
                "top_k": TOP_K,
                "retrieval_mode": "hybrid",
                "retrieved_count": len(results),
                "results": [
                    {
                        "id": r.get("id", f"{bank_id}::{r.get('chunk_id', '')}"),
                        "chunk_id": r.get("chunk_id"),
                        "bank_id": r.get("bank_id"),
                        "source_file": r.get("source_file"),
                        "document_name": r.get("document_name"),
                        "page": r.get("page"),
                        "page_chunk_index": r.get("page_chunk_index"),
                        "global_chunk_index": r.get("global_chunk_index"),
                        "token_count": r.get("token_count"),
                        "section_type": r.get("section_type", "general"),
                        "rrf_score": r.get("rrf_score"),
                        "text": r.get("text"),
                    }
                    for r in results
                ],
            }
        else:
            retrieval = query_chroma_for_bank(
                collection=collection,
                query_embedding=query_embedding,
                bank_id=bank_id,
                top_k=TOP_K,
            )

        payload = {
            "commitment_id": COMMITMENT_ID,
            "query_embedding_model": EMBEDDING_MODEL,
            "retrieval": retrieval,
        }

        output_path = output_dir / f"retrieval_{bank_id.lower()}_cp1.json"
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=True, indent=2)

        print(f"  {bank_id}: {retrieval['retrieved_count']} chunks -> {output_path}")

    print(f"\nRetrieval complete for {len(BANK_IDS)} banks.")


if __name__ == "__main__":
    main()
