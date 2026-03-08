"""
Step 2 (RAG): embed chunk text with OpenAI embeddings.

WHAT this module does:
- Reads chunk records produced by Step 1.
- Sends chunk `text` fields to OpenAI's embeddings endpoint in batches.
- Returns enriched records that keep original metadata + embedding vectors.

WHY this module exists:
- Retrieval in later steps needs vector similarity search.
- Embeddings convert unstructured text into numeric vectors we can index/query.

Design decisions implemented here (as requested):
1) Model: `text-embedding-3-small`
2) Dimensions: full default dimensions (we do NOT pass `dimensions=...`)
3) Output shape: one JSONL-ready record per chunk including its embedding vector
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from openai import OpenAI


def read_jsonl(path: Path) -> list[dict]:
    """
    Read a JSONL file into a list of dictionaries.

    JSONL means "one JSON object per line".
    This format is convenient for large pipelines and incremental re-processing.
    """
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: Iterable[dict]) -> None:
    """
    Write dictionaries to JSONL (one object per line).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=True) + "\n")


def batch_records(records: list[dict], batch_size: int) -> Iterable[list[dict]]:
    """
    Yield fixed-size batches from a list of records.

    Why batching:
    - Reduces API round trips compared to one request per chunk.
    - Keeps implementation simple while improving throughput.
    """
    for i in range(0, len(records), batch_size):
        yield records[i : i + batch_size]


def embed_chunk_records(
    chunk_records: list[dict],
    client: OpenAI,
    model_name: str = "text-embedding-3-small",
    batch_size: int = 100,
) -> list[dict]:
    """
    Embed chunk records and return enriched records.

    Input requirement:
    - Every record must contain a `text` field.

    Output:
    - Original metadata and text
    - `embedding`: list[float]
    - `embedding_model`: model used to embed
    - `embedding_dimensions`: vector length (derived from API response)
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be a positive integer.")

    embedded_records: list[dict] = []

    for batch in batch_records(chunk_records, batch_size=batch_size):
        texts = [record.get("text", "") for record in batch]

        # Decision 1: use `text-embedding-3-small`.
        # Decision 2: keep full default dimensions by NOT passing `dimensions=...`.
        response = client.embeddings.create(
            model=model_name,
            input=texts,
        )

        # The API returns one embedding per input text, indexed by `item.index`.
        # We sort by index to guarantee alignment with our `batch` order.
        items = sorted(response.data, key=lambda item: item.index)

        for record, item in zip(batch, items):
            vector = item.embedding

            # Keep metadata first for readability when scanning JSONL manually.
            output_record = {
                "chunk_id": record.get("chunk_id"),
                "bank_id": record.get("bank_id"),
                "source_file": record.get("source_file"),
                "document_name": record.get("document_name"),
                "page": record.get("page"),
                "page_chunk_index": record.get("page_chunk_index"),
                "global_chunk_index": record.get("global_chunk_index"),
                "token_count": record.get("token_count"),
                "text": record.get("text", ""),
                "embedding": vector,
                "embedding_model": model_name,
                "embedding_dimensions": len(vector),
            }
            embedded_records.append(output_record)

    return embedded_records
