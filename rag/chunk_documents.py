from __future__ import annotations

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
PDFS = [
    "policies/ABN/Exclusion list (Mar 2021).pdf",
    "policies/HSBC/Thermal Coal Phase-out Policy (Feb 2025).pdf",
    "policies/BBVA/Environmental and Social Framework (Dec 2024).pdf",
    "policies/Barclays/Climate change statement (Feb 2024).pdf",
]
OUTPUT = "data/rag/chunks.jsonl"
SECTION_TAGGING = True
# ---------------------------------------------------------------------------

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rag.chunking import (  # noqa: E402
    DEFAULT_CHUNK_OVERLAP_TOKENS,
    DEFAULT_CHUNK_SIZE_TOKENS,
    DEFAULT_ENCODING_NAME,
    chunk_pages_with_page_provenance,
)
from utils import load_pdf_pages  # noqa: E402


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=True) + "\n")


def main() -> None:
    if len(PDFS) < 1:
        raise ValueError("Add at least 1 PDF to the PDFS list.")

    all_chunks: list[dict] = []

    for pdf_path_str in PDFS:
        pdf_path = Path(pdf_path_str)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        pages = load_pdf_pages(str(pdf_path))
        pdf_chunks = chunk_pages_with_page_provenance(
            pages=pages,
            source_file=str(pdf_path),
            chunk_size_tokens=DEFAULT_CHUNK_SIZE_TOKENS,
            chunk_overlap_tokens=DEFAULT_CHUNK_OVERLAP_TOKENS,
            encoding_name=DEFAULT_ENCODING_NAME,
            section_tagging=SECTION_TAGGING,
        )
        all_chunks.extend(pdf_chunks)

    output_path = Path(OUTPUT)
    write_jsonl(output_path, all_chunks)

    total_tokens = sum(chunk["token_count"] for chunk in all_chunks)
    if SECTION_TAGGING:
        from collections import Counter
        section_counts = Counter(c["section_type"] for c in all_chunks)
        section_summary = ", ".join(f"{k}: {v}" for k, v in sorted(section_counts.items()))
    else:
        section_summary = "disabled"

    print(f"Chunking complete.")
    print(f"- PDFs processed: {len(PDFS)}")
    print(f"- Chunks written: {len(all_chunks)}")
    print(f"- Total tokens: {total_tokens}")
    print(f"- Section tagging: {section_summary}")
    print(f"- Output: {output_path}")


if __name__ == "__main__":
    main()
