import pandas as pd
import unicodedata
import re
import os
import fitz

def load_exceptions(exceptions_csv_path, exceptions_criteria_csv_path, criteria_id):
      """
      Loads exceptions with criteria-specific examples.
      Returns only exceptions for the specified criteria where applies="yes".
      Cleans non-breaking spaces and converts NaN to None.
      
      Args:
          exceptions_csv_path: Path to the base exceptions CSV file
          exceptions_criteria_csv_path: Path to the exceptions-criteria mapping CSV file
          criteria_id: ID of the criteria to filter exceptions for
      
      Returns:
          List of dictionaries containing exception data for the specified criteria
      """
      if not exceptions_criteria_csv_path or not criteria_id:
          raise ValueError("Both exceptions_criteria_csv_path and criteria_id are required")
      
      # Load base exceptions
      exceptions_df = pd.read_csv(exceptions_csv_path, encoding='utf-8')
      exceptions_df = exceptions_df.where(pd.notnull(exceptions_df), None)
      exceptions_df = exceptions_df.map(lambda x: x.replace("\xa0", " ").strip() if isinstance(x, str) else x)

      # Load exceptions_criteria mappings
      exceptions_criteria_df = pd.read_csv(exceptions_criteria_csv_path, encoding='utf-8')
      exceptions_criteria_df = exceptions_criteria_df.where(pd.notnull(exceptions_criteria_df), None)
      exceptions_criteria_df = exceptions_criteria_df.map(lambda x: x.replace("\xa0", " ").strip() if isinstance(x, str) else x)

      # Filter for the specific criteria AND where applies="yes"
      exceptions_criteria_df = exceptions_criteria_df[
          (exceptions_criteria_df['criteria_id'] == criteria_id) &
          (exceptions_criteria_df['applies'] == 'yes')
      ]

      # Join exceptions with exceptions_criteria
      result = pd.merge(exceptions_df, exceptions_criteria_df, on='exception_id', how='inner')
      return result[["exception_id", "exception_definition", "mitigant", "mitigant_definition",
                    "exception_examples", "mitigant_examples"]].to_dict(orient="records")

def get_exception_examples(exception_id, exceptions_criteria_csv_path, criteria_id):
    """
    Extracts examples for a specific exception and criteria combination.

    Args:
        exception_id: ID of the exception to get examples for
        exceptions_criteria_csv_path: Path to the exceptions-criteria mapping CSV file
        criteria_id: ID of the criteria

    Returns:
        Dictionary with exception_examples and mitigant_examples for the specific exception
    """
    exceptions_criteria_df = pd.read_csv(exceptions_criteria_csv_path, encoding='utf-8')
    exceptions_criteria_df = exceptions_criteria_df.where(pd.notnull(exceptions_criteria_df), None)
    exceptions_criteria_df = exceptions_criteria_df.map(lambda x: x.replace("\xa0", " ").strip() if isinstance(x, str) else x)

    # Filter for the specific exception and criteria
    filtered_df = exceptions_criteria_df[
        (exceptions_criteria_df['exception_id'] == exception_id) &
        (exceptions_criteria_df['criteria_id'] == criteria_id)
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

def load_criteria(criteria_id, csv_path):
    """
    Loads a single criterion from a CSV file based on its ID.
    Returns a dictionary with 'criteria_description' and 'criteria_guidelines'.
    """
    df = pd.read_csv(csv_path, encoding='utf-8')
    criteria = df[df['criteria_id'] == criteria_id]

    return {
        'criteria_description': criteria['criteria_description'].iloc[0],
        'criteria_guidelines': criteria['criteria_guidelines'].iloc[0],
        'criteria_examples': criteria['criteria_examples'].iloc[0]
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

def detect_definitions_section(pages):
    """
    Detect if there is a definitions section in the policy pages.

    Args:
        pages: List of page dictionaries from load_pdf_pages

    Returns:
        dict: Contains 'has_definitions' (bool), 'start_page' (int), 'end_page' (int), 'section_title' (str)
    """
    definitions_patterns = [
        r'\b(key\s+definitions?|definitions?|glossary|key\s+terms?)\b',
        r'\b(defined\s+terms?)\b'
    ]

    for page in pages:
        text = page.get('text', '')
        text_lower = text.lower()

        # Look for definitions section headers
        for pattern in definitions_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                # Get the context around the match
                start_pos = match.start()
                before_text = text_lower[max(0, start_pos-50):start_pos]
                after_text = text_lower[start_pos:start_pos+200]
                original_after_text = text[start_pos:start_pos+200]

                # Skip if this looks like a table of contents entry (has dots leading to page numbers)
                if re.search(r'\.{3,}', after_text[:100]):  # Three or more dots in a row
                    continue

                # Skip if followed immediately by page numbers pattern
                if re.search(r'\s*\.+\s*\d+\s*$', after_text[:50]):
                    continue

                # Check if this appears to be a section header (start of line or after punctuation)
                is_section_header = (
                    re.search(r'(\n|^)\s*' + pattern, before_text + match.group(), re.IGNORECASE) or
                    re.search(r'^\s*' + pattern, after_text, re.IGNORECASE) or
                    any(char in before_text[-10:] for char in ['\n', '.', ';', ':'])
                )

                if is_section_header:
                    # Additional validation: look for actual definitions content
                    # Check if the page contains definition-like content
                    has_definition_content = (
                        # Look for term/definition table headers
                        re.search(r'\b(term|definition)\b.*\b(definition|term)\b', after_text[:300], re.IGNORECASE) or
                        # Look for definition patterns (word followed by explanation)
                        re.search(r'\n\w+[\s\w]*\n.*refers?\s+to|means|is\s+defined\s+as', after_text[:500], re.IGNORECASE) or
                        # Look for bullet points or lists with definitions
                        re.search(r'\n\s*[•\-\*]\s*\w+.*?[:;]\s*.{10,}', after_text[:500], re.IGNORECASE)
                    )

                    if has_definition_content:
                        return {
                            'has_definitions': True,
                            'start_page': page['page_number'],
                            'section_title': match.group(),
                            'detected_text': original_after_text[:100]
                        }

    return {
        'has_definitions': False,
        'start_page': None,
        'section_title': None,
        'detected_text': None
    }

def split_policy_and_definitions(pages, definitions_info):
    """
    Split policy pages into policy content and definitions section.

    Args:
        pages: List of page dictionaries from load_pdf_pages
        definitions_info: Dict from detect_definitions_section

    Returns:
        dict: Contains 'policy_pages' and 'definitions_pages' lists
    """
    if not definitions_info['has_definitions']:
        return {
            'policy_pages': pages,
            'definitions_pages': []
        }

    start_page = definitions_info['start_page']
    section_title = definitions_info['section_title']

    # Find where definitions section ends by looking for next major section
    end_page = len(pages)  # Default to end of document

    # Look for section endings (next major section or end patterns)
    for i, page in enumerate(pages[start_page-1:], start=start_page):
        text = page.get('text', '').lower()

        # Look for next major section headers that would indicate end of definitions
        next_section_patterns = [
            r'\b(introduction|background|scope|purpose|policy|procedures?|implementation|compliance|governance|responsibilities|appendix|annex)\b',
            r'\b(section\s+\d+|chapter\s+\d+|\d+\.\s+[a-z])',
            r'^\s*[ivx]+\.\s+',  # Roman numerals
            r'^\s*[a-z]\.\s+'    # Letter enumeration
        ]

        for pattern in next_section_patterns:
            if re.search(r'(\n|^)\s*' + pattern, text, re.IGNORECASE):
                # Don't end on the same page we started unless it's clearly a separate section
                if i > start_page:
                    end_page = i - 1
                    break

        if end_page < len(pages):
            break

    # Split the pages
    policy_pages = []
    definitions_pages = []

    for page in pages:
        page_num = page['page_number']
        if page_num < start_page:
            policy_pages.append(page)
        elif page_num <= end_page:
            definitions_pages.append(page)
        else:
            policy_pages.append(page)

    return {
        'policy_pages': policy_pages,
        'definitions_pages': definitions_pages
    }