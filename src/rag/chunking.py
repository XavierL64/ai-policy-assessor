"""
Step 1 (RAG): token-aware document chunking with page-level provenance.

WHAT this module does:
- Receives already-extracted PDF pages (one record per page).
- Splits each page into smaller chunks using LangChain's recursive splitter.
- Measures size in TOKENS (via tiktoken), not characters.
- Returns chunk records with metadata that preserves source traceability.

WHY this module exists:
- Embedding and retrieval quality strongly depend on chunk design.
- Token-aware chunking aligns with OpenAI model limits/costs.
- Page-level provenance gives precise evidence links (file + page), which is useful
  for auditability and interview explanations.

What this module intentionally does NOT do:
- No embeddings yet.
- No vector DB writes yet.
- No retrieval/reranking yet.
"""

from __future__ import annotations

import os
import re
from typing import Callable, Iterable
from pathlib import Path

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ---------------------------------------------------------------------------
# Baseline design choices for this first, minimal implementation.
# ---------------------------------------------------------------------------
# Why 500 / 125?
# - 500-token chunks: often improve retrieval precision for targeted questions.
# - 125-token overlap (25%): keeps continuity when important text crosses chunk
#   boundaries (common in legal/policy phrasing).
# These are baseline defaults, not universal optima.
DEFAULT_CHUNK_SIZE_TOKENS = 500
DEFAULT_CHUNK_OVERLAP_TOKENS = 125

# `cl100k_base` is a tiktoken encoding used by many modern OpenAI text models.
# In practice, this encoding defines how raw text is broken into tokens
# (sub-word units) for counting/billing/context-window purposes.
#
# Why this matters for chunking:
# - We set chunk size/overlap in TOKENS, so tokenization rules directly control
#   whether a chunk is considered "small enough".
# - A different encoding can produce different token counts for the same text,
#   which changes chunk boundaries and retrieval behavior.
# - Using a broadly compatible OpenAI encoding keeps chunk sizing closer to model
#   reality than character count does.
DEFAULT_ENCODING_NAME = "cl100k_base"

# Recursive split order: try strong semantic boundaries first (paragraphs), then
# weaker ones (spaces), then fallback to raw slicing if needed.
DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def make_token_length_function(encoding_name: str = DEFAULT_ENCODING_NAME) -> Callable[[str], int]:
    """
    Build a token-aware length function for LangChain splitters.

    Why this is critical:
    - LLM and embedding limits are token-based, not character-based.
    - Passing this function means chunk_size/chunk_overlap are interpreted in tokens.
    """
    # Build tokenizer once, then reuse inside the nested function for speed.
    # For `cl100k_base`, tiktoken applies OpenAI-specific BPE rules to map text
    # to integer token IDs.
    encoding = tiktoken.get_encoding(encoding_name)

    def token_length(text: str) -> int:
        # Core token-aware measurement used by the splitter.
        # `encoding.encode(text)` returns token IDs; length = token count.
        #
        # Example intuition:
        # - Short common words may be 1 token.
        # - Rare strings, symbols, or formatting can expand token count.
        # This is why token-aware sizing is more reliable than character length.
        return len(encoding.encode(text))

    return token_length


def make_recursive_splitter(
    chunk_size_tokens: int = DEFAULT_CHUNK_SIZE_TOKENS,
    chunk_overlap_tokens: int = DEFAULT_CHUNK_OVERLAP_TOKENS,
    encoding_name: str = DEFAULT_ENCODING_NAME,
) -> RecursiveCharacterTextSplitter:
    """
    Build the splitter object used by the chunking workflow.

    Workflow position:
    - This function runs at setup time inside `chunk_pages_with_page_provenance`.
    - It does NOT process pages directly.
    - It returns the configured splitting engine that will later split each page's text.

    Purpose:
    - Centralize splitting rules (size, overlap, separators, token length logic).
    - Keep chunking behavior consistent across all documents.
    """
    token_length = make_token_length_function(encoding_name=encoding_name)
    return RecursiveCharacterTextSplitter(
        # The two key knobs:
        # - chunk_size: maximum target length for each chunk.
        # - chunk_overlap: repeated context between neighboring chunks.
        chunk_size=chunk_size_tokens,
        chunk_overlap=chunk_overlap_tokens,
        # Critical: token-aware length function so size/overlap are in tokens.
        length_function=token_length,
        # Recursive split boundaries, from strongest to weakest.
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
    Main orchestration function for Step 1 chunking.

    Workflow position:
    - Input: page records from `utils.load_pdf_pages(...)`.
    - Internal setup: calls `make_recursive_splitter(...)` once.
    - Per-page processing: calls `splitter.split_text(page_text)` for each page.
    - Output: chunk records with text + provenance metadata for downstream embedding.

    Interaction with `make_recursive_splitter`:
    - `make_recursive_splitter` defines HOW splitting works.
    - `chunk_pages_with_page_provenance` defines WHERE and WHEN splitting is applied.
    - Together they separate configuration concerns from document-processing concerns.

    Why page-level first:
    - Every chunk can be traced back to an exact PDF page.
    - This improves auditability and interview-grade explainability.
    - It simplifies later debugging ("why did retrieval pick this chunk?").

    Input contract:
    - `pages` comes from `utils.load_pdf_pages`, each item has at least:
      - document_name
      - page_number
      - text
    """
    # Create shared helpers once per call.
    # `splitter` is the configured engine returned by `make_recursive_splitter`.
    token_length = make_token_length_function(encoding_name=encoding_name)
    splitter = make_recursive_splitter(
        chunk_size_tokens=chunk_size_tokens,
        chunk_overlap_tokens=chunk_overlap_tokens,
        encoding_name=encoding_name,
    )

    # Keep original filename for provenance metadata and human readability.
    source_filename = os.path.basename(source_file)
    # Filename stem is used in deterministic chunk IDs.
    source_stem, _ = os.path.splitext(source_filename)
    # Derive bank_id from the PDF parent folder name, e.g.:
    # policies/ABN/file.pdf -> bank_id = "ABN"
    bank_id = infer_bank_id_from_policy_path(source_file)

    # Output collection for all generated chunk records.
    chunks: list[dict] = []
    # A simple global index across all pages in this document.
    global_chunk_index = 0

    for page in pages:
        # Input pages come from utils.load_pdf_pages with 1-based page numbers.
        page_number = int(page["page_number"])
        page_text = page.get("text", "") or ""

        # Empty pages can happen in PDF extraction (tables/images only).
        if not page_text.strip():
            continue

        # Key architectural choice:
        # chunk each page independently to preserve unambiguous provenance.
        page_chunks = splitter.split_text(page_text)

        for page_chunk_index, chunk_text in enumerate(page_chunks, start=1):
            global_chunk_index += 1
            # Deterministic ID format:
            # <file-stem>-p<page>-c<chunk-on-page>
            chunk_id = f"{source_stem}-p{page_number:03d}-c{page_chunk_index:03d}"

            chunks.append(
                {
                    # Stable ID is useful for DB upserts/re-indexing later.
                    "chunk_id": chunk_id,
                    # Provenance fields used in retrieval explanations/citations.
                    "bank_id": bank_id,
                    "source_file": source_filename,
                    "document_name": page.get("document_name", source_stem),
                    "page": page_number,
                    # Token count supports QA checks and future tuning analyses.
                    "token_count": token_length(chunk_text),
                    # Position metadata for ordering and debugging.
                    "page_chunk_index": page_chunk_index,
                    "global_chunk_index": global_chunk_index,
                    # Section type for hybrid retrieval filtering.
                    # "general" when section_tagging is disabled.
                    "section_type": classify_section_type(chunk_text) if section_tagging else "general",
                    # Raw text content that will be embedded in Step 2.
                    "text": chunk_text,
                }
            )

    return chunks


# ---------------------------------------------------------------------------
# Section-aware tagging
#
# WHAT: Classifies each chunk by document section type (glossary, commitment,
#       scope, general) based on keyword patterns in the chunk text.
#
# WHY:  Glossary/definition chunks embed far from commitment queries but
#       contain critical evidence for exceptions. Tagging them enables
#       hybrid retrieval strategies that ensure these chunks are surfaced.
#
# HOW:  Simple regex keyword matching — no LLM needed. Each chunk gets a
#       single section_type label stored as Chroma metadata.
# ---------------------------------------------------------------------------

# Patterns checked in order — first match wins.
# Each tuple: (section_type, compiled regex pattern)
# Patterns are case-insensitive and match anywhere in the chunk text.
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

    Checks patterns in priority order (glossary > commitment > scope).
    Returns "general" if no pattern matches.

    WHY this priority order:
    - Glossary pages sometimes contain commitment-like language in their
      definitions (e.g. "HSBC will not..."). Checking glossary first
      prevents these from being misclassified as commitment chunks.
    """
    for section_type, pattern in SECTION_PATTERNS:
        if pattern.search(text):
            return section_type
    return "general"


def infer_bank_id_from_policy_path(source_file: str) -> str:
    """
    Infer bank_id from the immediate parent folder of the PDF path.

    Example:
    - policies/ABN/Exclusion list.pdf -> "ABN"
    """
    path = Path(source_file)
    parent_name = path.parent.name
    return parent_name if parent_name else "unknown_bank"
