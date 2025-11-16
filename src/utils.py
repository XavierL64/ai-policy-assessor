import pandas as pd
import unicodedata
import re
import os
import fitz

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

def load_pdf_pages(path):
    """
    Load a PDF and return a list of pages.
    Each page is a dict with:
      - document_name: the PDF file name (without extension)
      - page_number: 1-based page number
      - text: normalized text only (cleaned for verification)
    """
    docname = os.path.splitext(os.path.basename(path))[0]
    pages = []

    with fitz.open(path) as pdf:
        for i, page in enumerate(pdf, start=1):
            raw_text = page.get_text("text") or ""
            pages.append({
                "document_name": docname,
                "page_number": i,
                "text": normalize_text(raw_text)
            })

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