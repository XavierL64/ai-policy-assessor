"""
Step 1: Token-aware document chunking with page-level provenance.

Splits PDF pages into smaller chunks measured in tokens (via tiktoken),
preserving source traceability (file + page) for downstream citation.
"""

from __future__ import annotations

import os
import re
from typing import Callable, Iterable
from pathlib import Path

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 500-token chunks with 25% overlap balance retrieval precision
# against continuity across chunk boundaries in legal/policy text.
DEFAULT_CHUNK_SIZE_TOKENS = 500
DEFAULT_CHUNK_OVERLAP_TOKENS = 125

# cl100k_base is the tiktoken encoding used by OpenAI embedding models.
DEFAULT_ENCODING_NAME = "cl100k_base"

DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def make_token_length_function(encoding_name: str = DEFAULT_ENCODING_NAME) -> Callable[[str], int]:
    """Return a token-counting function for use as a LangChain length_function."""
    encoding = tiktoken.get_encoding(encoding_name)

    def token_length(text: str) -> int:
        return len(encoding.encode(text))

    return token_length


def make_recursive_splitter(
    chunk_size_tokens: int = DEFAULT_CHUNK_SIZE_TOKENS,
    chunk_overlap_tokens: int = DEFAULT_CHUNK_OVERLAP_TOKENS,
    encoding_name: str = DEFAULT_ENCODING_NAME,
) -> RecursiveCharacterTextSplitter:
    """Build a token-aware recursive text splitter."""
    token_length = make_token_length_function(encoding_name=encoding_name)
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size_tokens,
        chunk_overlap=chunk_overlap_tokens,
        length_function=token_length,
        separators=DEFAULT_SEPARATORS,
        is_separator_regex=False,
    )


def chunk_pages_with_page_provenance(
    pages: Iterable[dict],
    source_file: str,
    chunk_size_tokens: int = DEFAULT_CHUNK_SIZE_TOKENS,
    chunk_overlap_tokens: int = DEFAULT_CHUNK_OVERLAP_TOKENS,
    encoding_name: str = DEFAULT_ENCODING_NAME,
    section_tagging: bool = False,
) -> list[dict]:
    """
    Split PDF pages into token-sized chunks with page-level provenance.

    Each page is chunked independently so every chunk maps to exactly one
    PDF page, enabling precise evidence citations. Returns chunk records
    with metadata ready for embedding.
    """
    token_length = make_token_length_function(encoding_name=encoding_name)
    splitter = make_recursive_splitter(
        chunk_size_tokens=chunk_size_tokens,
        chunk_overlap_tokens=chunk_overlap_tokens,
        encoding_name=encoding_name,
    )

    source_filename = os.path.basename(source_file)
    source_stem, _ = os.path.splitext(source_filename)
    bank_id = infer_bank_id_from_policy_path(source_file)

    chunks: list[dict] = []
    global_chunk_index = 0

    for page in pages:
        page_number = int(page["page_number"])
        page_text = page.get("text", "") or ""

        if not page_text.strip():
            continue

        page_chunks = splitter.split_text(page_text)

        for page_chunk_index, chunk_text in enumerate(page_chunks, start=1):
            global_chunk_index += 1
            # Deterministic ID: <file-stem>-p<page>-c<chunk-on-page>
            chunk_id = f"{source_stem}-p{page_number:03d}-c{page_chunk_index:03d}"

            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "bank_id": bank_id,
                    "source_file": source_filename,
                    "document_name": page.get("document_name", source_stem),
                    "page": page_number,
                    "token_count": token_length(chunk_text),
                    "page_chunk_index": page_chunk_index,
                    "global_chunk_index": global_chunk_index,
                    "section_type": classify_section_type(chunk_text) if section_tagging else "general",
                    "text": chunk_text,
                }
            )

    return chunks


# ---------------------------------------------------------------------------
# Section-aware tagging
#
# Classifies chunks by document section type using regex keyword matching.
# Glossary/definition chunks embed far from commitment queries but contain
# critical evidence for exceptions — tagging them enables hybrid retrieval
# strategies that ensure these chunks are surfaced.
# ---------------------------------------------------------------------------

# Patterns checked in priority order — first match wins.
SECTION_PATTERNS = [
    ("glossary", re.compile(
        r"glossary|definitions?\b|key terms|means the following|"
        r"the following definitions apply|exempted activities",
        re.IGNORECASE,
    )),
    ("commitment", re.compile(
        r"will not (provide|finance|knowingly)|exclusion|"
        r"no (project finance|new finance)|phase.?out commitment",
        re.IGNORECASE,
    )),
    ("scope", re.compile(
        r"\bscope\b|applies to|prospective clients?|existing clients?|"
        r"enhanced due diligence",
        re.IGNORECASE,
    )),
]


def classify_section_type(text: str) -> str:
    """
    Classify a chunk's section type by keyword matching.

    Priority: glossary > commitment > scope > general.
    Glossary is checked first because glossary pages sometimes contain
    commitment-like language in their definitions.
    """
    for section_type, pattern in SECTION_PATTERNS:
        if pattern.search(text):
            return section_type
    return "general"


def infer_bank_id_from_policy_path(source_file: str) -> str:
    """Infer bank_id from the PDF's parent folder (e.g. policies/ABN/file.pdf -> "ABN")."""
    path = Path(source_file)
    parent_name = path.parent.name
    return parent_name if parent_name else "unknown_bank"
