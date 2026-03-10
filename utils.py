import pandas as pd
import unicodedata
import re
import os
import fitz
import pymupdf4llm
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type
import json

def get_openai_client():
    """
    Initialize and return an OpenAI client with API key from environment.

    Returns:
        OpenAI: Configured OpenAI client instance
    """
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    return OpenAI(api_key=api_key)

# Pre-configured retry decorator for OpenAI API calls
openai_retry = retry(
    wait=wait_random_exponential(min=1, max=60),
    stop=stop_after_attempt(6),
    retry=retry_if_exception_type(RateLimitError)
)

def print_debug_section(title, content=None, sections=None, enabled=True):
    """
    Print formatted debug output with consistent styling.

    Args:
        title: Main title for the debug section
        content: Single content block to print (optional)
        sections: Dictionary of {section_name: section_content} for multiple sections (optional)
        enabled: Whether to actually print (controlled by debug flags)

    Usage:
        # Single content block
        print_debug_section("POLICY PAGES", policy_pages, enabled=policy_debug)

        # Multiple sections
        print_debug_section("INPUTS", sections={
            "ASSESSMENT DATE": assessment_date,
            "COMMITMENT DESCRIPTION": commitment_description
        }, enabled=input_debug)
    """
    if not enabled:
        return

    print("\n" + "="*80)
    print(f"DEBUG - {title}")
    print("="*80)

    if content is not None:
        print(content)
    elif sections:
        for section_name, section_content in sections.items():
            print(f"\n--- {section_name} ---")
            # Handle dict/list content by pretty-printing JSON
            if isinstance(section_content, (dict, list)):
                print(json.dumps(section_content, indent=2))
            else:
                print(section_content)

    print("="*80 + "\n")

def load_exceptions(exceptions_csv_path, exceptions_criteria_csv_path, commitment_id):
      """
      Loads exceptions with commitment-specific examples.
      Returns only exceptions for the specified commitment where applies="yes".
      Cleans non-breaking spaces and converts NaN to None.

      Args:
          exceptions_csv_path: Path to the base exceptions CSV file
          exceptions_criteria_csv_path: Path to the exceptions-criteria mapping CSV file
          commitment_id: ID of the commitment to filter exceptions for

      Returns:
          List of dictionaries containing exception data for the specified commitment
      """
      if not exceptions_criteria_csv_path or not commitment_id:
          raise ValueError("Both exceptions_criteria_csv_path and commitment_id are required")
      
      # Load base exceptions
      exceptions_df = pd.read_csv(exceptions_csv_path, encoding='utf-8')
      exceptions_df = exceptions_df.where(pd.notnull(exceptions_df), None)
      exceptions_df = exceptions_df.map(lambda x: x.replace("\xa0", " ").strip() if isinstance(x, str) else x)

      # Load exceptions_criteria mappings
      exceptions_criteria_df = pd.read_csv(exceptions_criteria_csv_path, encoding='utf-8')
      exceptions_criteria_df = exceptions_criteria_df.where(pd.notnull(exceptions_criteria_df), None)
      exceptions_criteria_df = exceptions_criteria_df.map(lambda x: x.replace("\xa0", " ").strip() if isinstance(x, str) else x)

      # Filter for the specific commitment AND where applies="yes"
      exceptions_criteria_df = exceptions_criteria_df[
          (exceptions_criteria_df['commitment_id'] == commitment_id) &
          (exceptions_criteria_df['applies'] == 'yes')
      ]

      # Join exceptions with exceptions_criteria
      result = pd.merge(exceptions_df, exceptions_criteria_df, on='exception_id', how='inner')
      return result[["exception_id", "exception_definition", "mitigant", "mitigant_definition",
                    "exception_examples", "mitigant_examples"]].to_dict(orient="records")

def get_exception_examples(exception_id, exceptions_criteria_csv_path, commitment_id):
    """
    Extracts examples for a specific exception and commitment combination.

    Args:
        exception_id: ID of the exception to get examples for
        exceptions_criteria_csv_path: Path to the exceptions-criteria mapping CSV file
        commitment_id: ID of the commitment

    Returns:
        Dictionary with exception_examples and mitigant_examples for the specific exception
    """
    exceptions_criteria_df = pd.read_csv(exceptions_criteria_csv_path, encoding='utf-8')
    exceptions_criteria_df = exceptions_criteria_df.where(pd.notnull(exceptions_criteria_df), None)
    exceptions_criteria_df = exceptions_criteria_df.map(lambda x: x.replace("\xa0", " ").strip() if isinstance(x, str) else x)

    # Filter for the specific exception and commitment
    filtered_df = exceptions_criteria_df[
        (exceptions_criteria_df['exception_id'] == exception_id) &
        (exceptions_criteria_df['commitment_id'] == commitment_id)
    ]

    if filtered_df.empty:
        return {
            'exception_examples': 'No examples provided',
            'mitigant_examples': 'No examples provided'
        }

    row = filtered_df.iloc[0]
    return {
        'exception_examples': row.get('exception_examples', 'No examples provided'),
        'mitigant_examples': row.get('mitigant_examples', 'No examples provided')
    }

def load_commitment(commitment_id, csv_path):
    """
    Loads a single commitment from a CSV file based on its ID.
    Returns a dictionary with 'commitment_description' and 'commitment_guidelines'.
    """
    df = pd.read_csv(csv_path, encoding='utf-8')
    commitment = df[df['commitment_id'] == commitment_id]

    return {
        'commitment_description': commitment['commitment_description'].iloc[0],
        'commitment_guidelines': commitment['commitment_guidelines'].iloc[0],
        'commitment_examples': commitment['commitment_examples'].iloc[0]
    }

def filter_exceptions(data):
    """
    Takes a dict with 'commitment' and 'exceptions' keys,
    and returns a dict with commitment, exceptions where 'applies' is True, and all references.
    """
    commitment = data.get("commitment", False)
    exceptions = data.get("exceptions", [])
    references = data.get("references", [])
    
    filtered_exceptions = []
    for e in exceptions:
        if e.get("applies") == True:
            filtered_exceptions.append(e)
    return {"commitment": commitment, "exceptions": filtered_exceptions, "references": references}

# def normalize_text(text):
#     """Basic normalization for verification and matching."""
#     text = unicodedata.normalize("NFKC", text)        # normalize unicode
#     text = re.sub(r"[ \t]+", " ", text)               # collapse spaces/tabs
#     text = re.sub(r"\s*\n\s*", " ", text)             # collapse newlines
#     return text.strip()

## alternative nomalizer function that preserves line breaks
def normalize_text(text):
    """Basic normalization for verification and matching."""
    # Normalise line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # normalize unicode
    text = unicodedata.normalize("NFKC", text)
    # Rejoin hyphenated words split across lines
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)  
    # Collapse runs of spaces/tabs
    text = re.sub(r"[ \t]+", " ", text)
    # Clean spaces around line breaks
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    # Limit 3+ consecutive newlines to 2 (paragraph break)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

## alternative nomalizer function for structured markdown extraction
def _light_normalize(text):
    """Normalize line endings and unicode without destroying markdown structure."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = unicodedata.normalize("NFKC", text)
    return text.strip()


# Superscript digits and their plain equivalents
_SUPERSCRIPT_MAP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
# Pattern for footnote markers in body text (superscript or bracketed digits)
_BODY_MARKER_RE = re.compile(r"([⁰¹²³⁴⁵⁶⁷⁸⁹]+)")

def _extract_footnotes(text):
    """
    Split page text into body and footnote definitions.
    Returns (body, footnotes_dict) where footnotes_dict maps marker number (str) to footnote text.
    """
    # Split on horizontal rule (common pymupdf4llm separator before footnotes)
    parts = re.split(r"\n-{3,}\n|\n_{3,}\n|\n\*{3,}\n", text)

    if len(parts) >= 2:
        body = parts[0]
        footer = "\n".join(parts[1:])
    else:
        # Fallback: check the last paragraph block for superscript footnote markers
        last_break = text.rfind("\n\n")
        if last_break == -1:
            return text, {}
        last_block = text[last_break + 2:]
        first_line = last_block.strip().split("\n")[0].strip() if last_block.strip() else ""
        if not re.match(r"^[⁰¹²³⁴⁵⁶⁷⁸⁹]+[\s.)\-:]", first_line):
            return text, {}
        body = text[:last_break]
        footer = last_block

    footnotes = {}
    lines = footer.strip().split("\n")
    current_marker = None
    current_text = []

    for line in lines:
        line = line.strip()
        if not line:
            if current_marker:
                current_text.append("")
            continue

        # Try superscript marker first
        sup_match = re.match(r"^([⁰¹²³⁴⁵⁶⁷⁸⁹]+)[\s.)\-:]*(.*)", line)
        # Then plain digit marker
        digit_match = re.match(r"^(\d{1,2})[\s.)\-:]+(.*)", line) if not sup_match else None

        match = sup_match or digit_match
        if match:
            # Save previous footnote
            if current_marker:
                footnotes[current_marker] = " ".join(current_text).strip()
            marker = match.group(1).translate(_SUPERSCRIPT_MAP)
            current_marker = marker
            current_text = [match.group(2) if sup_match else match.group(2)]
        elif current_marker:
            # Continuation line of current footnote
            current_text.append(line)

    if current_marker:
        footnotes[current_marker] = " ".join(current_text).strip()

    return body, footnotes


def _inline_footnotes(body, footnotes):
    """Replace footnote markers in body with inlined footnote text."""
    def replace_marker(match):
        marker = match.group(1).translate(_SUPERSCRIPT_MAP)
        if marker in footnotes:
            return f" [Footnote: {footnotes[marker]}]"
        return match.group(0)  # leave unmatched markers as-is

    return _BODY_MARKER_RE.sub(replace_marker, body)


def _process_footnotes(pages):
    """
    Inline footnotes into body text across all pages.
    Uses cross-page lookahead for unmatched markers.
    """
    # First pass: extract body and footnotes per page
    parsed = []
    for page in pages:
        body, footnotes = _extract_footnotes(page["text"])
        parsed.append({"body": body, "footnotes": footnotes, "page": page})

    # Second pass: inline with cross-page lookahead
    for i, entry in enumerate(parsed):
        # Find unmatched markers in this page's body
        markers_in_body = {
            m.translate(_SUPERSCRIPT_MAP) for m in _BODY_MARKER_RE.findall(entry["body"])
        }
        unmatched = markers_in_body - set(entry["footnotes"].keys())

        # Look ahead to next page for unmatched markers
        if unmatched and i + 1 < len(parsed):
            next_footnotes = parsed[i + 1]["footnotes"]
            for marker in unmatched:
                if marker in next_footnotes:
                    entry["footnotes"][marker] = next_footnotes[marker]

        # Inline footnotes into body
        text = _inline_footnotes(entry["body"], entry["footnotes"])

        # Annotate any still-unmatched markers
        remaining_markers = {
            m.translate(_SUPERSCRIPT_MAP) for m in _BODY_MARKER_RE.findall(text)
            if m.translate(_SUPERSCRIPT_MAP) not in entry["footnotes"]
        }
        if remaining_markers:
            for m in remaining_markers:
                # Find the superscript version in text and annotate
                for sup in _BODY_MARKER_RE.findall(text):
                    if sup.translate(_SUPERSCRIPT_MAP) == m:
                        text = text.replace(sup, f"{sup} [Footnote not found on this page]", 1)
                        break

        entry["page"]["text"] = text

    return [entry["page"] for entry in parsed]


def load_pdf_pages(path, inline_footnotes=True):
    """
    Load a PDF and return a list of pages as structured markdown.
    Each page is a dict with:
      - document_name: the PDF file name (without extension)
      - page_number: 1-based page number
      - text: markdown-formatted text (tables, headings, bold/italic preserved)

    Args:
        path: path to PDF file
        inline_footnotes: if True, inline footnote text at point of reference
    """
    docname = os.path.splitext(os.path.basename(path))[0]

    md_pages = pymupdf4llm.to_markdown(path, page_chunks=True)

    pages = []
    for i, md_page in enumerate(md_pages, start=1):
        md_text = md_page.get("text", "") or ""
        pages.append({
            "document_name": docname,
            "page_number": i,
            "text": _light_normalize(md_text)
        })

    if inline_footnotes:
        pages = _process_footnotes(pages)

    return pages

def build_page_pack(pages, max_chars=None):
    """
    Concatenate pages into one context string with headers:

    === DOC: <document_name> | PAGE: <n> ===
    <page_text>

    Args:
        pages: list of dicts from load_pdf_pages (each has document_name, page_number, text)
        max_chars: optional int; if set, stop once this many characters have been added

    Returns:
        str: the concatenated context
    """
    parts = []
    total = 0

    for p in pages:
        page_text = p.get("text", "") or ""
        block = f"=== DOC: {p['document_name']} | PAGE: {p['page_number']} ===\n{page_text}\n"

        if max_chars is not None:
            # Check how many characters we can still add
            remaining = max_chars - total
            if remaining <= 0:
                break
            if len(block) > remaining:
                # Truncate this block to fit exactly
                parts.append(block[:remaining])
                total += remaining
                break

        parts.append(block)
        total += len(block)

    return "".join(parts)

def find_page_by_reference(original_pages, document_name, page_start):
    """
    Find a specific page from a collection of pages by document name and page number.
    
    Args:
        original_pages: List of page dictionaries from load_pdf_pages
        document_name: Name of the document to search for
        page_start: Page number to find (1-based)
    
    Returns:
        Page dictionary if found, None otherwise
    """
    if not original_pages or not document_name or page_start is None:
        return None
    
    for page in original_pages:
        if (page.get('document_name') == document_name and 
            page.get('page_number') == page_start):
            return page
    
    return None

def validate_references(assessment, original_pages):
    """
    Validate that extracted references exist and are accurately quoted.
    
    Args:
        assessment: Assessment dict with references
        original_pages: List of all original page dicts
    
    Returns:
        Assessment dict with validation status added to references
    """
    validated_assessment = assessment.copy()
    
    for ref in validated_assessment.get('references', []):
        # Find the source page
        source_page = find_page_by_reference(
            original_pages, 
            ref.get('document_name'), 
            ref.get('page_start')
        )
        
        if source_page is None:
            ref['validation_status'] = 'page_not_found'
            continue
        
        # Check if excerpt exists in source text
        excerpt = ref.get('excerpt', '')
        source_text = source_page.get('text', '')
        
        # Normalize both texts for comparison
        normalized_excerpt = normalize_text(excerpt)
        normalized_source = normalize_text(source_text)
        
        if normalized_excerpt in normalized_source:
            ref['validation_status'] = 'verified'
        else:
            # Check for partial matches or similar text
            words_in_excerpt = normalized_excerpt.split()
            words_in_source = normalized_source.split()
            
            # Calculate word overlap
            overlap = len(set(words_in_excerpt) & set(words_in_source))
            overlap_ratio = overlap / len(words_in_excerpt) if words_in_excerpt else 0
            
            if overlap_ratio > 0.8:
                ref['validation_status'] = 'partial_match'
                ref['overlap_ratio'] = overlap_ratio
            else:
                ref['validation_status'] = 'needs_review'
                ref['overlap_ratio'] = overlap_ratio
    
    return validated_assessment

def interactive_reference_selector(references):
    """
    Interactive function to let user select and edit commitment references.
    Returns formatted reference text to be used in exception assessment.

    Args:
        references: List of reference dictionaries from commitment assessment

    Returns:
        tuple: (formatted_reference_str, selected_references_list)
            - formatted_reference_str: Formatted reference text to be used in exception step
            - selected_references_list: List of selected reference dictionaries
    """
    if not references:
        print("\nNo references found.")
        return "", []

    print("\n" + "="*80)
    print("COMMITMENT REFERENCES FOUND")
    print("="*80)

    # Display all references with numbers
    for i, ref in enumerate(references, 1):
        excerpt = ref.get('excerpt', 'N/A')

        print(f"\n[{i}] Page: {ref.get('page_number', 'N/A')}")
        print(f"    Excerpt: {excerpt}")

    print("\n" + "="*80)

    # Get user selection
    while True:
        selection = input("\nEnter reference numbers to include (e.g., '1,3' or '1' or 'all'): ").strip()

        if selection.lower() == 'all':
            selected_refs = references
            break
        else:
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                if all(0 <= i < len(references) for i in indices):
                    selected_refs = [references[i] for i in indices]
                    break
                else:
                    print(f"Invalid selection. Please enter numbers between 1 and {len(references)}.")
            except (ValueError, IndexError):
                print("Invalid input. Please enter comma-separated numbers or 'all'.")

    # Combine selected excerpts
    combined_excerpts = " ".join([ref.get('excerpt', '') for ref in selected_refs])

    print("\n" + "="*80)
    print("COMBINED REFERENCE TEXT")
    print("="*80)
    print(combined_excerpts)
    print("="*80)

    # Allow editing
    edit = input("\nWould you like to edit this text? (y/n): ").strip().lower()

    if edit == 'y':
        print("\nPaste or type your edited text below, then press Enter twice to finish:")
        print("-" * 80)

        lines = []
        empty_count = 0
        while True:
            try:
                line = input()
                if line == "":
                    empty_count += 1
                    if empty_count >= 2:
                        break
                    lines.append(line)
                else:
                    empty_count = 0
                    lines.append(line)
            except EOFError:
                break

        if lines:
            # Remove trailing empty lines
            while lines and lines[-1] == "":
                lines.pop()
            combined_excerpts = '\n'.join(lines)

    formatted_reference = f"commitment: {combined_excerpts}"

    print("\n" + "="*80)
    print("FINAL REFERENCE TEXT TO BE USED")
    print("="*80)
    print(formatted_reference)
    print("="*80)

    return formatted_reference, selected_refs


def flatten_assessment(result, commitment_id):
    """
    Flatten an assessment result into a single dict suitable for tabular export.
    Columns follow the function schema fields for commitment and exceptions.
    Supports both two-step structure (commitment.value) and single-step structure.
    """
    row = {"commitment_id": commitment_id}

    commit_block = result.get("commitment", {})
    if isinstance(commit_block, dict) and "value" in commit_block:
        commit_value = commit_block.get("value")
        commit_refs = commit_block.get("references", []) or []
    else:
        # single-step style: commitment as bool, references at top-level
        commit_value = commit_block if isinstance(commit_block, bool) else result.get("commitment")
        commit_refs = result.get("references", []) or []

    row["commitment_value"] = commit_value
    row["commitment_ref_count"] = len(commit_refs)
    row["commitment_ref_text"] = " | ".join(
        f'{r.get("document_name","")}:p{r.get("page_start","?")}-{r.get("page_end","?")} {r.get("excerpt","")}'.strip()
        for r in commit_refs
    )

    for exc in result.get("exceptions", []) or []:
        exc_id = exc.get("exception_id", "EX").replace(".", "_")
        prefix = exc_id
        row[f"{prefix}_applies"] = exc.get("applies")
        row[f"{prefix}_description"] = exc.get("description")
        row[f"{prefix}_mitigated"] = exc.get("mitigated")
        row[f"{prefix}_mitigant"] = exc.get("mitigant")
        exc_refs = exc.get("references", []) or []
        row[f"{prefix}_ref_count"] = len(exc_refs)
        row[f"{prefix}_ref_text"] = " | ".join(
            f'{r.get("document_name","")}:p{r.get("page_start","?")}-{r.get("page_end","?")} {r.get("excerpt","")}'.strip()
            for r in exc_refs
        )

    return row
