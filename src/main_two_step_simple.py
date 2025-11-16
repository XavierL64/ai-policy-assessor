import os
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError
from utils import load_commitment, load_exceptions, load_pdf_pages, build_page_pack, interactive_reference_selector
from function_schema_two_step_simple import assess_commitment_schema, assess_all_exceptions_schema
from prompt_two_step_simple import build_commitment_prompt, build_all_exceptions_prompt
from config import assessment_date
import json
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type

# Load environment variables
load_dotenv()

# Get the API key from the environment
api_key = os.getenv("OPENAI_API_KEY")

# Create OpenAI client
client = OpenAI(api_key=api_key)

# configuration variables
COMMITMENT_ID = "CP.2"
PDF_SOURCE = "sources/Barclays/Climate change statement (Feb 2024).pdf"
MODEL_NAME = "gpt-4o"
POLICY_DEBUG = False  # Set to True to print policy pages in commitment evaluation
INPUT_DEBUG = False   # Set to True to print other inputs in both evaluation steps
INTERACTIVE_MODE = False  # Set to True to manually select and edit commitment references

# Global token counter
total_tokens_used = 0

@retry(
    wait=wait_random_exponential(min=1, max=60),
    stop=stop_after_attempt(6),
    retry=retry_if_exception_type(RateLimitError)
)
def assess_commitment_step(policy_pages, commitment_description, commitment_guidelines, commitment_examples, assessment_date):
    """
    Step 1: Assess whether the policy contains a commitment.
    """

    # Build the commitment assessment prompt
    commitment_input = f"""
Policy pages to assess:
<<<POLICY_PAGES>>>
{policy_pages}
<<<END_POLICY_PAGES>>>

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
"""

    messages = [
        {
            "role": "system",
            "content": build_commitment_prompt()
        },
        {
            "role": "user",
            "content": commitment_input
        }
    ]

    # Debug prints
    if POLICY_DEBUG:
        print("\n" + "="*80)
        print("DEBUG - POLICY PAGES (COMMITMENT STEP)")
        print("="*80)
        print(policy_pages)
        print("="*80 + "\n")

    if INPUT_DEBUG:
        print("\n" + "="*80)
        print("DEBUG - INPUTS (COMMITMENT STEP)")
        print("="*80)
        print("\n--- COMMITMENT DESCRIPTION ---")
        print(commitment_description)
        print("\n--- COMMITMENT GUIDELINES ---")
        print(commitment_guidelines)
        print("\n--- COMMITMENT EXAMPLES ---")
        print(commitment_examples)
        print("="*80 + "\n")

    # Create chat completion for commitment assessment
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=assess_commitment_schema,
        tool_choice={
            "type": "function",
            "function": {"name": "assess_commitment"}
        },
        temperature=0
    )

    # Track token usage
    global total_tokens_used
    total_tokens_used += response.usage.total_tokens

    # Parse the response
    raw_output = response.choices[0].message.tool_calls[0].function.arguments
    return json.loads(raw_output)

@retry(
    wait=wait_random_exponential(min=1, max=60),
    stop=stop_after_attempt(6),
    retry=retry_if_exception_type(RateLimitError)
)
def assess_all_exceptions_step(policy_pages, exception_taxonomy, commitment_id, commitment_references, commitment_guidelines, assessment_date):
    """
    Step 2: Assess all exceptions at once.
    """

    # Build the exception assessment prompt
    exceptions_input = f"""
Policy pages to assess:
<<<POLICY_PAGES>>>
{policy_pages}
<<<END_POLICY_PAGES>>>

Assessment date:
<<<ASSESSMENT_DATE>>>
{assessment_date}
<<<END_ASSESSMENT_DATE>>>

Commitment:
<<<COMMITMENT>>>
{commitment_references}
<<<END_COMMITMENT>>>

Commitment guidelines:
<<<COMMITMENT_GUIDELINES>>>
{commitment_guidelines}
<<<END_COMMITMENT_GUIDELINES>>>

Exception taxonomy:
<<<EXCEPTION_TAXONOMY>>>
{json.dumps(exception_taxonomy, indent=2)}
<<<END_EXCEPTION_TAXONOMY>>>
"""

    messages = [
        {
            "role": "system",
            "content": build_all_exceptions_prompt()
        },
        {
            "role": "user",
            "content": exceptions_input
        }
    ]

    # Debug prints
    if INPUT_DEBUG:
        print("\n" + "="*80)
        print("DEBUG - INPUTS (ALL EXCEPTIONS STEP)")
        print("="*80)
        print("\n--- ASSESSMENT DATE ---")
        print(assessment_date)
        print("\n--- COMMITMENT REFERENCES ---")
        print(commitment_references)
        print("\n--- COMMITMENT GUIDELINES ---")
        print(commitment_guidelines)
        print("\n--- EXCEPTION TAXONOMY ---")
        print(json.dumps(exception_taxonomy, indent=2))
        print("="*80 + "\n")

    # Create chat completion for all exceptions assessment
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=assess_all_exceptions_schema,
        tool_choice={
            "type": "function",
            "function": {"name": "assess_all_exceptions"}
        },
        temperature=0
    )

    # Track token usage
    global total_tokens_used
    total_tokens_used += response.usage.total_tokens

    # Parse the response
    raw_output = response.choices[0].message.tool_calls[0].function.arguments
    return json.loads(raw_output)

def run_two_step_simple_analysis():
    """
    Main function to run the two-step simple analysis approach.
    Step 1: Assess commitment
    Step 2: Assess all exceptions at once
    """

    # Load commitment and exceptions
    commitment = load_commitment(COMMITMENT_ID, "criteria/criteria.csv")
    commitment_description = commitment['commitment_description']
    commitment_guidelines = commitment['commitment_guidelines']
    commitment_examples = commitment['commitment_examples']
    exception_taxonomy = load_exceptions("exceptions/exceptions.csv", "exceptions/exceptions_criteria.csv", COMMITMENT_ID)

    # Load and prepare policy pages
    pages = load_pdf_pages(PDF_SOURCE)
    policy_pages = build_page_pack(pages)

    print("=== STEP 1: ASSESSING COMMITMENT ===")

    # Step 1: Assess commitment
    commitment_result = assess_commitment_step(
        policy_pages,
        commitment_description,
        commitment_guidelines,
        commitment_examples,
        assessment_date
    )

    print(f"Commitment: {commitment_result['commitment']}")
    print(f"Commitment references: {len(commitment_result['references'])}")

    # Format commitment references based on mode
    formatted_references = ""
    selected_references = []
    if commitment_result['references']:
        if INTERACTIVE_MODE:
            # Interactive mode: let user select and edit references
            formatted_references, selected_references = interactive_reference_selector(commitment_result['references'])
        else:
            # Automatic mode: use first reference only
            first_ref = commitment_result['references'][0]
            formatted_references = f"commitment: {first_ref.get('excerpt', '')}"
            selected_references = [first_ref]

    print("\n=== FORMATTED COMMITMENT REFERENCES ===")
    print(formatted_references)
    print("=== END FORMATTED REFERENCES ===\n")

    # Step 2: Assess all exceptions (only if commitment is True)
    exceptions_results = []

    if commitment_result['commitment']:
        print(f"\n=== STEP 2: ASSESSING EXCEPTIONS ===")

        all_exceptions_result = assess_all_exceptions_step(
            policy_pages,
            exception_taxonomy,
            COMMITMENT_ID,
            formatted_references,
            commitment_guidelines,
            assessment_date
        )

        exceptions_results = all_exceptions_result['exceptions']

        # Clean up references for exceptions that don't apply
        for exception_result in exceptions_results:
            if not exception_result['applies']:
                exception_result['references'] = []

        # Print summary
        print(f"\n=== EXCEPTIONS SUMMARY ===")
        for exception_result in exceptions_results:
            print(f"  - {exception_result['exception_id']}: Applies={exception_result['applies']}", end="")
            if exception_result['applies']:
                print(f", Mitigated={exception_result['mitigated']}")
            else:
                print()
    else:
        print("\n=== STEP 2: SKIPPED (No commitment found) ===")

    # Combine results - include references with commitment only if commitment is true
    # Use selected_references (which may be user-edited) instead of original commitment_result['references']
    final_assessment = {
        "commitment": {
            "value": commitment_result['commitment'],
            "references": selected_references if commitment_result['commitment'] else []
        },
        "exceptions": exceptions_results
    }

    print("\n=== FINAL ASSESSMENT ===")
    print(json.dumps(final_assessment, indent=2))

    print(f"\n=== TOTAL TOKENS USED: {total_tokens_used} ===")

    return final_assessment

if __name__ == "__main__":
    run_two_step_simple_analysis()
