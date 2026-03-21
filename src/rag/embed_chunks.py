"""
Step 2: embed chunks with OpenAI and write JSONL output.
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
INPUT = "data/rag/chunks.jsonl"
OUTPUT = "data/rag/chunk_embeddings.jsonl"
MODEL = "text-embedding-3-small"
BATCH_SIZE = 100
# ---------------------------------------------------------------------------

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rag.embedding import (  # noqa: E402
    embed_chunk_records,
    read_jsonl,
    write_jsonl,
)
from utils import get_openai_client  # noqa: E402


def main() -> None:
    input_path = Path(INPUT)
    output_path = Path(OUTPUT)

    if not input_path.exists():
        raise FileNotFoundError(f"Input chunk file not found: {input_path}")

    chunk_records = read_jsonl(input_path)
    if not chunk_records:
        raise ValueError(f"No chunk records found in: {input_path}")

    client = get_openai_client()

    embedded_records = embed_chunk_records(
        chunk_records=chunk_records,
        client=client,
        model_name=MODEL,
        batch_size=BATCH_SIZE,
    )

    write_jsonl(output_path, embedded_records)

    print("Embedding complete.")
    print(f"- Input chunks: {len(chunk_records)}")
    print(f"- Embedded records: {len(embedded_records)}")
    print(f"- Model: {MODEL}")
    print(f"- Output: {output_path}")


if __name__ == "__main__":
    main()
