"""
Step 3: store embeddings in local ChromaDB.

"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
INPUT = "data/rag/chunk_embeddings.jsonl"
PERSIST_DIR = "data/rag/chroma_db"
COLLECTION = "policy_chunks"
BATCH_SIZE = 100
# ---------------------------------------------------------------------------

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rag.embedding import read_jsonl  # noqa: E402
from rag.vector_store import (  # noqa: E402
    get_or_create_persistent_collection,
    upsert_embedding_records,
)


def main() -> None:
    input_path = Path(INPUT)

    if not input_path.exists():
        raise FileNotFoundError(f"Input embeddings file not found: {input_path}")

    embedding_records = read_jsonl(input_path)
    if not embedding_records:
        raise ValueError(f"No embedding records found in: {input_path}")

    collection = get_or_create_persistent_collection(
        persist_directory=PERSIST_DIR,
        collection_name=COLLECTION,
    )

    processed = upsert_embedding_records(
        collection=collection,
        embedding_records=embedding_records,
        batch_size=BATCH_SIZE,
    )

    print("Chroma storage complete.")
    print(f"- Input records: {len(embedding_records)}")
    print(f"- Upserted records: {processed}")
    print(f"- Collection: {COLLECTION}")
    print(f"- Persist directory: {PERSIST_DIR}")
    print(f"- Collection count: {collection.count()}")


if __name__ == "__main__":
    main()
