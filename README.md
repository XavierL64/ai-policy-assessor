# AI Policy Assessor (prototype)

An AI-powered tool that evaluates bank fossil fuel policies against defined assessment criteria. The project explores how large language models (LLMs) can support automated policy analysis by extracting commitments, identifying exceptions, validating references, and producing structured, machine-readable outputs.

## Overview

This prototype uses the OpenAI API with structured function-calling to ensure consistent JSON outputs across different assessment steps. Policy documents (PDFs) are ingested and normalised before being passed to the model, which evaluates whether a specified commitment is present. The tool then scans for exceptions and possible mitigants using a custom exception taxonomy.

Three assessment approaches involving one or multiple API calls are currently being tested for performance and reliability.

The tool is still under active development. This prototype focuses on a subset of assessment criteria related to thermal coal power, with additional themes (e.g., coal mining, oil & gas) planned for future iterations following the initial testing phase.

A RAG-based retrieval approach is being explored in the [`rag-workflow-eval`](../../tree/rag-workflow-eval) branch, where policy documents are chunked, embedded, and stored in a vector database to enable semantic retrieval before assessment.

## Project Structure

```
ai-policy-assessor/
|- src/
|  |- single_step/           # Single API call assessment
|  |- two_step/              # Two-step assessment (commitment + exceptions (multiple API calls))
|  |- two_step_simple/       # Two-step assessment (commitment + exceptions)
|  |- examples/              # Sample outputs and assessment examples
|  |- utils.py               # Shared utilities
|  |- config.py              # Configuration and assessment date
|  |- run_assessment.py      # Main entry point
|- policies/                 # Bank policy PDFs (organized by bank)
|- criteria/                 # Commitment definitions and criteria
|- exceptions/               # Exception taxonomy and criteria
|- data/                     # Output data and results
|- requirements.txt          # Python dependencies
```

## Inputs

### Commitments

The prototype currently supports two main commitments (defined in `criteria/criteria.csv`)

### Exceptions

The prototype includes an exception taxonomy defining loopholes that may weaken commitments (defined in `exceptions\\exceptions.csv`)

Each exception can be mitigated or unmitigated based on specific criteria (defined in `exceptions/exceptions_criteria.csv`).

### Policy Sources

Place bank policy PDFs in the `policies/` directory, organized by bank name:

```
policies/
|- ABN/
|- Barclays/
|- BBVA/
|- Credit Agricole/
|- Danske Bank/
|- HSBC/
```

## Output

The assessment produces JSON output with:
- Commitment status (true/false)
- List of applicable exceptions
- Mitigation status for each exception
- Supporting references from the policy

Example output:
```json
{
  "commitment": {
    "value": true,
    "references": [
      {
        "page": 3,
        "excerpt": "The bank will not finance new coal power plants..."
      }
    ]
  },
  "exceptions": [
    {
      "exception_id": "CP.EX.2",
      "applies": true,
      "mitigated": false,
      "references": [...]
    }
  ]
}
```
The tool also returns total tokens used separately.

## Usage

### Run the assessment

```bash
python src/run_assessment.py --commitment-id CP.1 --pdf-source policies/ABN/policy.pdf
```

#### CLI Options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--commitment-id` | `-c` | *(required)* | Commitment ID to assess (e.g. `CP.1`) |
| `--pdf-source` | `-p` | *(required)* | Path to the policy PDF |
| `--approach` | `-a` | `two_step_simple` | Assessment approach: `single_step`, `two_step_simple`, `two_step` |
| `--model` | `-m` | `gpt-4o` | OpenAI model name |
| `--policy-debug` | | off | Print extracted policy pages |
| `--input-debug` | | off | Print other inputs |
| `--interactive` | | off | Manually select/edit commitment references (not applicable for `single_step`) |
| `--to-excel` | | off | Export `two_step` results to Excel |

### Assessment Approaches

**Single Step** (`single_step`):
- Assesses commitment and all exceptions in one API call
- Can use few-shot examples

**Two Step Simple** (`two_step_simple`):
- Step 1: Assess if commitment exists in one API call
- Step 2: Assesses all exceptions for that commitment if it exists in one API call

**Two Step** (`two_step`):
- Step 1: Assess if commitment exists in one API call
- Step 2: Assesses each exception individually for that commitment if it exists through multiple API calls

### Interactive Mode

When `--interactive` is set, you can:
- Review extracted policy references
- Select which references to include in the final assessment
- Edit reference text before processing
- Skip irrelevant references

### Running Individual Modules

You can also run assessment approaches directly:

```bash
# Run single-step assessment
python src/single_step/main.py

# Run two-step assessment
python src/two_step/main.py

# Run two-step simple assessment
python src/two_step_simple/main.py
```

## PDF Text Extraction Strategy

The prototype uses **PyMuPDF (fitz)** to extract text from PDF policy documents. The extraction process includes:

1. **Page-by-Page Extraction**: Each PDF page is processed individually with metadata:
   - Document name (PDF filename without extension)
   - Page number (1-indexed)
   - Extracted text content

2. **Text Normalization**: Extracted text undergoes normalization to improve accuracy:
   - Line ending standardization
   - Unicode normalization (NFKC)
   - Hyphenated word rejoining across line breaks
   - Whitespace cleanup (collapse spaces/tabs, limit consecutive newlines)
   - This ensures consistent text matching and comparison

3. **Context Building**: Pages are concatenated with clear delimiters:
   ```
   === DOC: <document_name> | PAGE: <n> ===
   <page_text>
   ```
   This format helps the AI model understand document structure and page boundaries.

4. **Reference Validation (Experimental)**: Verify that AI-extracted policy references actually exist in the original PDF and are accurately quoted.

An optional reference validation feature is available (currently implemented for the `single_step` approach only)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-policy-assessor
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Dependencies

See `requirements.txt` for full list.
