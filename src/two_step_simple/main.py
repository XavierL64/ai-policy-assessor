import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import RateLimitError
from utils import (load_commitment, load_exceptions, load_pdf_pages, build_page_pack,
                   interactive_reference_selector, get_openai_client, openai_retry,
                   print_debug_section)
from .function_schema import assess_commitment_schema, assess_all_exceptions_schema
from .prompt import build_commitment_prompt, build_all_exceptions_prompt
from config import assessment_date
import json

# Create OpenAI client
client = get_openai_client()


def assess_commitment_step(policy_pages, commitment_description, commitment_guidelines, commitment_examples,
                           model_name, policy_debug, input_debug, total_tokens_counter):
    """
    Assess whether the policy contains a commitment.
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
    print_debug_section("POLICY PAGES (COMMITMENT STEP)", content=policy_pages, enabled=policy_debug)

    print_debug_section("INPUTS (COMMITMENT STEP)", sections={
        "COMMITMENT DESCRIPTION": commitment_description,
        "COMMITMENT GUIDELINES": commitment_guidelines,
        "COMMITMENT EXAMPLES": commitment_examples
    }, enabled=input_debug)

    @openai_retry
    def make_api_call():
        # Create chat completion for commitment assessment
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=assess_commitment_schema,
            tool_choice={
                "type": "function",
                "function": {"name": "assess_commitment"}
            },
            temperature=0
        )

        # Track token usage
        total_tokens_counter['count'] += response.usage.total_tokens

        # Parse the response
        raw_output = response.choices[0].message.tool_calls[0].function.arguments
        return json.loads(raw_output)

    return make_api_call()

def assess_all_exceptions_step(policy_pages, exception_taxonomy, commitment_references,
                               commitment_guidelines, assessment_date, model_name, input_debug, total_tokens_counter):
    """
    Assess all exceptions.
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
    print_debug_section("INPUTS (ALL EXCEPTIONS STEP)", sections={
        "ASSESSMENT DATE": assessment_date,
        "COMMITMENT REFERENCES": commitment_references,
        "COMMITMENT GUIDELINES": commitment_guidelines,
        "EXCEPTION TAXONOMY": exception_taxonomy
    }, enabled=input_debug)

    @openai_retry
    def make_api_call():
        # Create chat completion for all exceptions assessment
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=assess_all_exceptions_schema,
            tool_choice={
                "type": "function",
                "function": {"name": "assess_all_exceptions"}
            },
            temperature=0
        )

        # Track token usage
        total_tokens_counter['count'] += response.usage.total_tokens

        # Parse the response
        raw_output = response.choices[0].message.tool_calls[0].function.arguments
        return json.loads(raw_output)

    return make_api_call()

def run_two_step_simple_analysis(commitment_id="CP.2",
                                 pdf_source="sources/Barclays/Climate change statement (Feb 2024).pdf",
                                 model_name="gpt-4o",
                                 policy_debug=False,
                                 input_debug=False,
                                 interactive_mode=False):
    """
    Assess commitment first, then all exceptions in one call

    Args:
        commitment_id: ID of the commitment to assess
        pdf_source: Path to the PDF file to assess
        model_name: OpenAI model to use
        policy_debug: Whether to print policy pages
        input_debug: Whether to print other inputs
        interactive_mode: Whether to manually select and edit commitment references

    Returns:
        dict: Final assessment with commitment and exceptions
    """
    # Token counter (using dict to allow modification in nested functions)
    total_tokens_counter = {'count': 0}

    # Load commitment and exceptions
    commitment = load_commitment(commitment_id, "criteria/criteria.csv")
    commitment_description = commitment['commitment_description']
    commitment_guidelines = commitment['commitment_guidelines']
    commitment_examples = commitment['commitment_examples']
    exception_taxonomy = load_exceptions("exceptions/exceptions.csv", "exceptions/exceptions_criteria.csv", commitment_id)

    # Load and prepare policy pages
    pages = load_pdf_pages(pdf_source)
    policy_pages = build_page_pack(pages)

    print("=== STEP 1: ASSESSING COMMITMENT ===")

    # Step 1: Assess commitment
    commitment_result = assess_commitment_step(
        policy_pages,
        commitment_description,
        commitment_guidelines,
        commitment_examples,
        model_name,
        policy_debug,
        input_debug,
        total_tokens_counter
    )

    print(f"Commitment: {commitment_result['commitment']}")
    print(f"Commitment references: {len(commitment_result['references'])}")

    # Format commitment references based on mode
    formatted_references = ""
    selected_references = []
    if commitment_result['references']:
        if interactive_mode:
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
            formatted_references,
            commitment_guidelines,
            assessment_date,
            model_name,
            input_debug,
            total_tokens_counter
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

    print(f"\n=== TOTAL TOKENS USED: {total_tokens_counter['count']} ===")

    return final_assessment

if __name__ == "__main__":
    # Default configuration for standalone execution
    run_two_step_simple_analysis(
        commitment_id="CP.2",
        pdf_source="sources/Barclays/Climate change statement (Feb 2024).pdf",
        model_name="gpt-4o",
        policy_debug=False,
        input_debug=False,
        interactive_mode=False
    )
