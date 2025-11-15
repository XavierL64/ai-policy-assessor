import os
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError
from utils import load_commitment, load_exceptions, load_pdf_pages, build_page_pack, get_exception_examples
from function_schema_two_step import assess_commitment_schema, assess_exception_schema
from prompt_two_step import build_commitment_prompt, build_exception_prompt
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
MODEL_NAME = "gpt-4.1"
POLICY_DEBUG = False  # Set to True to print policy pages in commitment evaluation
INPUT_DEBUG = False   # Set to True to print other inputs in both evaluation steps

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
def assess_exception_step(policy_pages, exception_data, commitment_id, commitment_references, commitment_guidelines, assessment_date):
    """
    Step 2: Assess whether a specific exception applies and if it is mitigated.
    """

    # Extract specific examples for this exception and commitment
    examples = get_exception_examples(
        exception_data['exception_id'],
        "exceptions/exceptions_criteria.csv",
        commitment_id
    )

    # Build the exception assessment prompt
    exception_input = f"""
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

Exception ID:
<<<EXCEPTION_ID>>>
{exception_data['exception_id']}
<<<END_EXCEPTION_ID>>>

Exception definition:
<<<EXCEPTION_DEFINITION>>>
{exception_data['exception_definition']}
<<<END_EXCEPTION_DEFINITION>>>

Mitigant available:
<<<MITIGANT>>>
{exception_data['mitigant']}
<<<END_MITIGANT>>>

Mitigant definition:
<<<MITIGANT_DEFINITION>>>
{exception_data.get('mitigant_definition', 'n/a')}
<<<END_MITIGANT_DEFINITION>>>

Exception examples:
<<<EXCEPTION_EXAMPLES>>>
{examples['exception_examples']}
<<<END_EXCEPTION_EXAMPLES>>>

Mitigant examples:
<<<MITIGANT_EXAMPLES>>>
{examples['mitigant_examples']}
<<<END_MITIGANT_EXAMPLES>>>
"""

    messages = [
        {
            "role": "system",
            "content": build_exception_prompt()
        },
        {
            "role": "user",
            "content": exception_input
        }
    ]

    # Debug prints
    if INPUT_DEBUG:
        print("\n" + "="*80)
        print(f"DEBUG - INPUTS (EXCEPTION STEP: {exception_data['exception_id']})")
        print("="*80)
        print("\n--- COMMITMENT REFERENCES ---")
        print(commitment_references)
        print("\n--- COMMITMENT GUIDELINES ---")
        print(commitment_guidelines)
        print("\n--- EXCEPTION ID ---")
        print(exception_data['exception_id'])
        print("\n--- EXCEPTION DEFINITION ---")
        print(exception_data['exception_definition'])
        print("\n--- MITIGANT ---")
        print(exception_data['mitigant'])
        print("\n--- MITIGANT DEFINITION ---")
        print(exception_data.get('mitigant_definition', 'n/a'))
        print("\n--- EXCEPTION EXAMPLES ---")
        print(examples['exception_examples'])
        print("\n--- MITIGANT EXAMPLES ---")
        print(examples['mitigant_examples'])
        print("="*80 + "\n")

    # Create chat completion for exception assessment
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=assess_exception_schema,
        tool_choice={
            "type": "function",
            "function": {"name": "assess_exception"}
        },
        temperature=0
    )

    # Track token usage
    global total_tokens_used
    total_tokens_used += response.usage.total_tokens

    # Parse the response
    raw_output = response.choices[0].message.tool_calls[0].function.arguments
    return json.loads(raw_output)

def run_two_step_analysis():
    """
    Main function to run the two-step analysis approach.
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

    # Format commitment references into readable text (only first reference)
    formatted_references = ""
    if commitment_result['references']:
        first_ref = commitment_result['references'][0]
        formatted_references = f"commitment: {first_ref.get('excerpt', '')}"

    print("\n=== FORMATTED COMMITMENT REFERENCES ===")
    print(formatted_references)
    print("=== END FORMATTED REFERENCES ===\n")

    # Step 2: Assess exceptions (only if commitment is True)
    exceptions_results = []

    if commitment_result['commitment']:
        print(f"\n=== STEP 2: ASSESSING {len(exception_taxonomy)} EXCEPTIONS ===")

        for i, exception_data in enumerate(exception_taxonomy, 1):
            print(f"Assessing exception {i}/{len(exception_taxonomy)}: {exception_data['exception_id']}")

            exception_result = assess_exception_step(
                policy_pages,
                exception_data,
                COMMITMENT_ID,
                formatted_references,
                commitment_guidelines,
                assessment_date
            )

            # Only include references if the exception applies
            if not exception_result['applies']:
                exception_result['references'] = []

            exceptions_results.append(exception_result)

            print(f"  - Applies: {exception_result['applies']}")
            if exception_result['applies']:
                print(f"  - Mitigated: {exception_result['mitigated']}")
    else:
        print("\n=== STEP 2: SKIPPED (No commitment found) ===")

    # Combine results - include references with commitment only if commitment is true
    final_assessment = {
        "commitment": {
            "value": commitment_result['commitment'],
            "references": commitment_result['references'] if commitment_result['commitment'] else []
        },
        "exceptions": exceptions_results
    }

    print("\n=== FINAL ASSESSMENT ===")
    print(json.dumps(final_assessment, indent=2))

    print(f"\n=== TOTAL TOKENS USED: {total_tokens_used} ===")

    return final_assessment

if __name__ == "__main__":
    run_two_step_analysis()