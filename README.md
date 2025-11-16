# AI Policy Assessor

An AI-powered tool for assessing bank financing policies against environmental commitment criteria, specifically focusing on thermal coal-related commitments and exceptions.

## Overview

This tool uses OpenAI's language models to automatically analyze bank policy documents (PDFs) and determine whether they meet specific environmental commitments related to coal power financing. The assessment process checks for both the presence of commitments and identifies any exceptions or loopholes that may weaken them.

## Features

- **Multiple Assessment Approaches**: Choose from three different assessment methodologies:
  - `single_step`: All assessments in one API call
  - `two_step`: Separate commitment and exception assessments
  - `two_step_simple`: Simplified two-step approach

- **Interactive Reference Selection**: Manually review and edit extracted policy references
- **Exception Analysis**: Automatically identifies policy exceptions and whether they're mitigated
- **Structured Output**: JSON-formatted results with commitment status and exception details
- **Token Usage Tracking**: Monitor API costs with built-in token counting

## Project Structure

```
ai-policy-assessor/
├── src/
│   ├── single_step/          # Single API call assessment
│   ├── two_step/              # Two-step assessment (commitment + exceptions)
│   ├── two_step_simple/       # Simplified two-step approach
│   ├── examples/              # Sample outputs and assessment examples
│   ├── utils.py               # Shared utilities
│   ├── config.py              # Configuration and assessment date
│   └── run_assessment.py      # Main entry point
├── policies/                  # Bank policy PDFs (organized by bank)
├── criteria/                  # Commitment definitions and criteria
├── exceptions/                # Exception taxonomy and criteria
├── data/                      # Output data and results
└── requirements.txt           # Python dependencies
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-policy-assessor
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
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

## Usage

### Quick Start

1. **Configure the assessment** in `src/config.py`:
   ```python
   COMMITMENT_ID = "CP.1"  # or "CP.2"
   PDF_SOURCE = "policies/ABN/Exclusion list (Mar 2021).pdf"
   APPROACH = "two_step"  # Choose: single_step, two_step_simple, two_step
   MODEL_NAME = "gpt-4o"
   INTERACTIVE_MODE = True
   ```

2. **Run the assessment**:
   ```bash
   python src/run_assessment.py
   ```

### Assessment Approaches

**Single Step** (`single_step`):
- Assesses commitment and all exceptions in one API call
- Faster and more cost-effective
- Uses comprehensive few-shot examples

**Two Step** (`two_step`):
- Step 1: Assess if commitment exists
- Step 2: Individually assess each exception
- More granular control and debugging
- Higher token usage

**Two Step Simple** (`two_step_simple`):
- Simplified version of two-step approach
- Balanced between speed and accuracy

### Interactive Mode

When `INTERACTIVE_MODE = True`, you can:
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

## Commitments

The tool currently supports two main commitments (defined in `criteria/criteria.csv`):

**CP.1**: Coal Power Project Finance
- Does the bank prohibit dedicated financing for thermal coal power plants?
- Covers project-specific financing, direct loans, dedicated financing

**CP.2**: Coal Power Corporate Finance
- Does the bank restrict general corporate purpose finance based on revenue/generation thresholds?
- Covers corporate loans and general purpose financing

## Exceptions

The tool identifies common policy exceptions that may weaken commitments:

- **Geographic limitations**: Exclusions only applying to specific regions
- **Transition plans**: Exemptions for clients with transition/phase-out plans
- **Ringfenced financing**: Exemptions for sustainable activity financing
- **Capacity replacements**: Exclusions not covering like-for-like replacements
- And more...

Each exception can be mitigated or unmitigated based on specific criteria defined in `exceptions/exceptions_criteria.csv`.

## Policy Sources

Place bank policy PDFs in the `policies/` directory, organized by bank name:

```
policies/
├── ABN/
├── Barclays/
├── BBVA/
├── Credit Agricole/
├── Danske Bank/
└── HSBC/
```

## Output

The assessment produces JSON output with:
- Commitment status (true/false)
- Supporting references from the policy
- List of applicable exceptions
- Mitigation status for each exception
- Total tokens used

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

## Configuration Options

In `src/config.py`:
- `COMMITMENT_ID`: Which commitment to assess
- `PDF_SOURCE`: Path to policy PDF
- `APPROACH`: Assessment methodology
- `MODEL_NAME`: OpenAI model (e.g., "gpt-4o", "gpt-4-turbo")
- `POLICY_DEBUG`: Print policy pages for debugging
- `INPUT_DEBUG`: Print input prompts for debugging
- `INTERACTIVE_MODE`: Enable manual reference selection

## Development

### Adding New Commitments

1. Add commitment definition to `criteria/criteria.csv`
2. Define relevant exceptions in `exceptions/exceptions.csv`
3. Add exception examples in `exceptions/exceptions_criteria.csv`

### Debugging

Enable debug modes in `config.py`:
```python
POLICY_DEBUG = True   # View policy pages sent to API
INPUT_DEBUG = True    # View all input parameters
```

## Dependencies

Key dependencies:
- `openai`: OpenAI API client
- `pymupdf`: PDF parsing
- `pandas`: Data handling
- `python-dotenv`: Environment variable management
- `jupyterlab`: Optional, for notebook development

See `requirements.txt` for full list.

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

## Contact

[Add contact information here]
