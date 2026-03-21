"""
Step 3: Store embedded chunks in local ChromaDB.

Uses a single shared collection (``policy_chunks``) for all banks, with
bank-specific retrieval via metadata filters. Upserts for idempotent reruns.
"""

from __future__ import annotations

from typing import Iterable

import chromadb
from chromadb.api.models.Collection import Collection


def get_or_create_persistent_collection(
    persist_directory: str = "data/rag/chroma_db",
    collection_name: str = "policy_chunks",
) -> Collection:
    """Create or open a persistent Chroma collection."""
    client = chromadb.PersistentClient(path=persist_directory)
    collection = client.get_or_create_collection(name=collection_name)
    return collection


def batch_records(records: list[dict], batch_size: int) -> Iterable[list[dict]]:
    """Yield fixed-size batches from a list of records."""
    for i in range(0, len(records), batch_size):
        yield records[i : i + batch_size]


def build_chroma_id(record: dict) -> str:
    """
    Build a stable Chroma record ID.

    Prefixes chunk_id with bank_id to avoid collisions across banks
    when using a single shared collection.
    """
    bank_id = str(record.get("bank_id", "unknown_bank"))
    chunk_id = str(record.get("chunk_id", "unknown_chunk"))
    return f"{bank_id}::{chunk_id}"


def upsert_embedding_records(
    collection: Collection,
    embedding_records: list[dict],
    batch_size: int = 100,
) -> int:
    """Upsert embedding records into Chroma and return number of records processed."""
    if batch_size <= 0:
        raise ValueError("batch_size must be a positive integer.")

    processed = 0

    for batch in batch_records(embedding_records, batch_size=batch_size):
        ids: list[str] = []
        embeddings: list[list[float]] = []
        documents: list[str] = []
        metadatas: list[dict] = []

        for record in batch:
            ids.append(build_chroma_id(record))

            vector = record.get("embedding")
            if not isinstance(vector, list) or not vector:
                raise ValueError("Each record must contain a non-empty `embedding` list.")
            embeddings.append(vector)

            documents.append(str(record.get("text", "")))

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

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        processed += len(batch)

    return processed
