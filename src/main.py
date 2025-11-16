import os
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError
from utils import filter_exceptions, validate_references, load_pdf_pages, load_commitment, load_exceptions, build_page_pack, interactive_reference_selector
from function_schema import tools
from assessment_examples import ASSESSMENT_ABN, ASSESSMENT_HSBC, ASSESSMENT_BBVA, ASSESSMENT_BARCLAYS
from prompt import ROLE, TASK, INPUTS, STEPS, RULES
from config import assessment_date
import json
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type

# Load environment variables
load_dotenv()

# Get the API key from the environment
api_key = os.getenv("OPENAI_API_KEY")

# Create OpenAI client
client = OpenAI(api_key=api_key)

# Configuration variables
COMMITMENT_ID = "CP.2"
PDF_SOURCE = "sources/Barclays/Climate change statement (Feb 2024).pdf"
MODEL_NAME = "gpt-4o"
POLICY_DEBUG = False  # Set to True to print policy pages
INPUT_DEBUG = False   # Set to True to print other inputs
INTERACTIVE_MODE = True  # Set to True to manually select and edit commitment references

# Global token counter
total_tokens_used = 0

# Load commitment and exceptions based on configuration
commitment = load_commitment(COMMITMENT_ID, "criteria/criteria.csv")
commitment_description = commitment['commitment_description']
commitment_guidelines = commitment['commitment_guidelines']
commitment_examples = commitment['commitment_examples']
exception_taxonomy = load_exceptions("exceptions/exceptions.csv", "exceptions/exceptions_criteria.csv", COMMITMENT_ID)

# Load and prepare policy pages
pages = load_pdf_pages(PDF_SOURCE)
policy_pages = build_page_pack(pages)

# Build inputs
user_input = f"""
Policy pages to assess:
<<<POLICY_PAGES>>>
{policy_pages}
<<<END_POLICY_PAGES>>>

Assessment date:
<<<ASSESSMENT_DATE>>>
{assessment_date}
<<<END_ASSESSMENT_DATE>>>

Commitment description:
<<<COMMITMENT_DESCRIPTION>>>
{commitment_description}
<<<END_COMMITMENT_DESCRIPTION>>>

Commitment guidelines:
<<<COMMITMENT_GUIDELINES>>>
{commitment_guidelines}
<<<END_COMMITMENT_GUIDELINES>>>

Commitment examples:
<<<COMMITMENT_EXAMPLES>>>
{commitment_examples}
<<<END_COMMITMENT_EXAMPLES>>>

Exception taxonomy:
<<<EXCEPTION_TAXONOMY>>>
{json.dumps(exception_taxonomy)}
<<<END_EXCEPTION_TAXONOMY>>>
"""

# Debug prints
if POLICY_DEBUG:
    print("\n" + "="*80)
    print("DEBUG - POLICY PAGES")
    print("="*80)
    print(policy_pages)
    print("="*80 + "\n")

if INPUT_DEBUG:
    print("\n" + "="*80)
    print("DEBUG - INPUTS")
    print("="*80)
    print("\n--- ASSESSMENT DATE ---")
    print(assessment_date)
    print("\n--- COMMITMENT DESCRIPTION ---")
    print(commitment_description)
    print("\n--- COMMITMENT GUIDELINES ---")
    print(commitment_guidelines)
    print("\n--- COMMITMENT EXAMPLES ---")
    print(commitment_examples)
    print("\n--- EXCEPTION TAXONOMY ---")
    print(json.dumps(exception_taxonomy, indent=2))
    print("="*80 + "\n")

@retry(
    wait=wait_random_exponential(min=1, max=60),
    stop=stop_after_attempt(6),
    retry=retry_if_exception_type(RateLimitError)
)
def assess_policy(messages):
    """
    Assess policy with retry logic for rate limit errors.
    """
    # Create chat completion
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=tools,
        tool_choice={
            "type": "function",
            "function": {"name": "assess_commitment_exceptions"}
        },
        temperature=0
    )

    # Track token usage
    global total_tokens_used
    total_tokens_used += response.usage.total_tokens

    # Parse the raw tool response
    raw_output = response.choices[0].message.tool_calls[0].function.arguments
    return json.loads(raw_output)

# Create messages for the model
messages = [
    {
        "role": "system",
        "content": ROLE + TASK + INPUTS + STEPS + RULES
    },
    # Uncomment to add few-shot examples
    # {
    #     "role": "user",
    #     "content": input_abn
    # },
    # {
    #     "role": "assistant",
    #     "content": json.dumps(ASSESSMENT_ABN)
    # },
    {
        "role": "user",
        "content": user_input
    }
]

# Run assessment with retry logic
assessment = assess_policy(messages)

# Handle interactive mode for commitment references
if INTERACTIVE_MODE and assessment.get('references'):
    print(f"\n=== INTERACTIVE MODE: COMMITMENT REFERENCES ===")
    print(f"Found {len(assessment['references'])} references")
    formatted_references, selected_references = interactive_reference_selector(assessment['references'])
    # Replace the references with the user-selected and potentially edited ones
    assessment['references'] = selected_references
    print("\n=== FORMATTED COMMITMENT REFERENCES ===")
    print(formatted_references)
    print("=== END FORMATTED REFERENCES ===\n")

# Filter exceptions to only those that apply
filtered_assessment = filter_exceptions(assessment)

print(filtered_assessment)

print(f"\n=== TOTAL TOKENS USED: {total_tokens_used} ===")

# # Load original pages for reference validation
# document_path = "sources/BBVA/Environmental and Social Framework (Dec 2024).pdf"
# original_pages = load_pdf_pages(document_path)

# # Validate references against original document
# validated_assessment = validate_references(filtered_assessment, original_pages)

# # Print the final processed output
# print("=== FILTERED AND VALIDATED ASSESSMENT ===")
# print(json.dumps(validated_assessment, indent=2))


