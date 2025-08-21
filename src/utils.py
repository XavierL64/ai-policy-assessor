import pandas as pd
import unicodedata
import re
import os
import fitz

def load_exceptions(csv_path):
    """
    Loads exceptions from a CSV file and returns a list of dictionaries.
    Cleans non-breaking spaces and converts NaN to None.
    Each dictionary contains 'exception_id', 'exception_definition', and 'mitigant_definition' for one exception.
    """
    df = pd.read_csv(csv_path, encoding='utf-8')
    df = df.where(pd.notnull(df), None)
    df = df.map(lambda x: x.replace("\xa0", " ").strip() if isinstance(x, str) else x)

    return df[["exception_id", "exception_definition", "mitigant_definition"]].to_dict(orient="records")

def load_criteria(criteria_id, csv_path):
    """
    Loads a single criterion from a CSV file based on its ID.
    Returns a dictionary with 'criteria_description' and 'criteria_guidelines'.
    """
    df = pd.read_csv(csv_path, encoding='utf-8')
    criteria = df[df['criteria_id'] == criteria_id]

    return {
        'criteria_description': criteria['criteria_description'].iloc[0],
        'criteria_guidelines': criteria['criteria_guidelines'].iloc[0]
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