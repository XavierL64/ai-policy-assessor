"""
Package exports for `rag`.

What `__init__.py` does here:
- Marks this folder as a Python package.
- Re-exports selected functions/constants from internal modules.

Why re-export:
- Consumers can import from one stable package path:
    `from rag import chunk_pages_with_page_provenance, embed_chunk_records`
  instead of importing from multiple files directly.
- Keeps public API explicit through `__all__`.
"""

# Step 1 exports: chunking constants + helpers.
from .chunking import (
    DEFAULT_CHUNK_OVERLAP_TOKENS,
    DEFAULT_CHUNK_SIZE_TOKENS,
    DEFAULT_ENCODING_NAME,
    chunk_pages_with_page_provenance,
    make_recursive_splitter,
    make_token_length_function,
)

# Step 2 exports: embedding I/O and embedding transform.
from .embedding import embed_chunk_records, read_jsonl, write_jsonl
from .vector_store import (
    build_chroma_id,
    get_or_create_persistent_collection,
    upsert_embedding_records,
)
from .retrieval import (
    build_commitment_retrieval_query,
    embed_query_text,
    query_chroma_for_bank,
)
from .synthesis import (
    build_chunk_catalog,
    build_chunk_lookup,
    build_synthesis_user_input,
    resolve_model_output_with_programmatic_citations,
    synthesize_assessment_from_retrieval,
)

# Public API surface of this package.
# Only names listed here are intended for external imports.
__all__ = [
    "DEFAULT_CHUNK_OVERLAP_TOKENS",
    "DEFAULT_CHUNK_SIZE_TOKENS",
    "DEFAULT_ENCODING_NAME",
    "chunk_pages_with_page_provenance",
    "make_recursive_splitter",
    "make_token_length_function",
    "embed_chunk_records",
    "read_jsonl",
    "write_jsonl",
    "build_chroma_id",
    "get_or_create_persistent_collection",
    "upsert_embedding_records",
    "build_commitment_retrieval_query",
    "embed_query_text",
    "query_chroma_for_bank",
    "build_chunk_catalog",
    "build_chunk_lookup",
    "build_synthesis_user_input",
    "resolve_model_output_with_programmatic_citations",
    "synthesize_assessment_from_retrieval",
]
