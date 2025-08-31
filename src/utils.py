import pandas as pd
import unicodedata
import re
import os
import fitz

def load_exceptions(exceptions_csv_path, exceptions_criteria_csv_path=None, criteria_id=None):
      """
      Loads exceptions with criteria-specific examples.
      If criteria_id provided, returns only exceptions for that criteria where applies="yes".
      Cleans non-breaking spaces and converts NaN to None.
      """
      # Load base exceptions
      exceptions_df = pd.read_csv(exceptions_csv_path, encoding='utf-8')
      exceptions_df = exceptions_df.where(pd.notnull(exceptions_df), None)
      exceptions_df = exceptions_df.map(lambda x: x.replace("\xa0", " ").strip() if isinstance(x, str) else x)

      # Load exceptions_criteria mappings if provided
      if exceptions_criteria_csv_path and criteria_id:
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

      return exceptions_df[["exception_id", "exception_definition", "mitigant_definition"]].to_dict(orient="records")

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
    and returns a dict with commitment and only the exceptions where 'applies' is True.
    """
    commitment = data.get("commitment", False)
    exceptions = data.get("exceptions", [])
    
    filtered_exceptions = []
    for e in exceptions:
        if e.get("applies") == True:
            filtered_exceptions.append(e)
    
    return {"commitment": commitment, "exceptions": filtered_exceptions}

def normalize_text(text):
    """Basic normalization for verification and matching."""
    text = unicodedata.normalize("NFKC", text)        # normalize unicode
    text = re.sub(r"[ \t]+", " ", text)               # collapse spaces/tabs
    text = re.sub(r"\s*\n\s*", " ", text)             # collapse newlines
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