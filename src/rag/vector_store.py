"""
Step 3 (RAG): store embedded chunks in local ChromaDB.

WHAT this module does:
- Reads embedding records (metadata + text + embedding vector).
- Upserts them into a local persistent Chroma collection.

WHY this module exists:
- Step 4 retrieval needs an indexed vector store.
- Chroma persistence keeps the index on disk across runs.

Design decisions implemented:
1) Single collection for all banks: `policy_chunks`
2) Local persistence directory under `data/rag/chroma_db`
3) Use upsert (not add) so reruns update existing records cleanly
"""

from __future__ import annotations

from typing import Iterable

import chromadb
from chromadb.api.models.Collection import Collection


def get_or_create_persistent_collection(
    persist_directory: str = "data/rag/chroma_db",
    collection_name: str = "policy_chunks",
) -> Collection:
    """
    Create or open a persistent Chroma collection.

    Workflow position:
    - Called once at startup of Step 3.
    - Returns the collection handle used by batch upsert logic.
    """
    # PersistentClient stores index/data files on local disk.
    client = chromadb.PersistentClient(path=persist_directory)

    # One shared collection for all banks.
    # Bank-specific retrieval is done later via metadata filters (bank_id).
    collection = client.get_or_create_collection(name=collection_name)
    return collection


def batch_records(records: list[dict], batch_size: int) -> Iterable[list[dict]]:
    """
    Yield fixed-size batches from a list of records.
    """
    for i in range(0, len(records), batch_size):
        yield records[i : i + batch_size]


def build_chroma_id(record: dict) -> str:
    """
    Build a stable Chroma record id.

    Why not only `chunk_id`:
    - `chunk_id` may collide across banks if filenames are reused.
    - Prefixing with bank_id keeps IDs unique in a single shared collection.
    """
    bank_id = str(record.get("bank_id", "unknown_bank"))
    chunk_id = str(record.get("chunk_id", "unknown_chunk"))
    return f"{bank_id}::{chunk_id}"


def upsert_embedding_records(
    collection: Collection,
    embedding_records: list[dict],
    batch_size: int = 100,
) -> int:
    """
    Upsert embedding records into Chroma and return number of records processed.

    Input requirement per record:
    - `embedding`: list[float]
    - `text`: string document
    - metadata fields such as bank_id/source_file/page/etc.
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be a positive integer.")

    processed = 0

    for batch in batch_records(embedding_records, batch_size=batch_size):
        ids: list[str] = []
        embeddings: list[list[float]] = []
        documents: list[str] = []
        metadatas: list[dict] = []

        for record in batch:
            # Stable id for upsert behavior.
            ids.append(build_chroma_id(record))

            vector = record.get("embedding")
            if not isinstance(vector, list) or not vector:
                raise ValueError("Each record must contain a non-empty `embedding` list.")
            embeddings.append(vector)

            documents.append(str(record.get("text", "")))

            # Metadata kept small and query-friendly for filtered retrieval.
            metadatas.append(
                {
                    "chunk_id": str(record.get("chunk_id", "")),
                    "bank_id": str(record.get("bank_id", "")),
                    "source_file": str(record.get("source_file", "")),
                    "document_name": str(record.get("document_name", "")),
                    "page": int(record.get("page", 0)),
                    "page_chunk_index": int(record.get("page_chunk_index", 0)),
                    "global_chunk_index": int(record.get("global_chunk_index", 0)),
                    "token_count": int(record.get("token_count", 0)),
                    "embedding_model": str(record.get("embedding_model", "")),
                    "embedding_dimensions": int(record.get("embedding_dimensions", 0)),
                    "section_type": str(record.get("section_type", "general")),
                }
            )

        # Decision 3: use upsert so repeated runs update existing ids.
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        processed += len(batch)

    return processed
