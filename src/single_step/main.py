import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import RateLimitError
from utils import (filter_exceptions, validate_references, load_pdf_pages, load_commitment,
                   load_exceptions, build_page_pack, interactive_reference_selector,
                   get_openai_client, openai_retry, print_debug_section)
from .function_schema import tools
from examples import POLICY_PAGES_ABN, ASSESSMENT_ABN, POLICY_PAGES_HSBC, ASSESSMENT_HSBC, POLICY_PAGES_BBVA, ASSESSMENT_BBVA, POLICY_PAGES_BARCLAYS, ASSESSMENT_BARCLAYS
from .prompt import ROLE, TASK, INPUTS, STEPS, RULES
from config import assessment_date
import json

# Create OpenAI client
client = get_openai_client()

def run_single_step_analysis(commitment_id="CP.2",
                             pdf_source="policies/Barclays/Climate change statement (Feb 2024).pdf",
                             model_name="gpt-4o",
                             policy_debug=False,
                             input_debug=False,
                             interactive_mode=True):
    """
    Assess commitment and all exceptions in one API call.

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
    # Token counter
    total_tokens_used = 0

    # Load commitment and exceptions based on configuration
    commitment = load_commitment(commitment_id, "criteria/criteria.csv")
    commitment_description = commitment['commitment_description']
    commitment_guidelines = commitment['commitment_guidelines']
    commitment_examples = commitment['commitment_examples']
    exception_taxonomy = load_exceptions("exceptions/exceptions.csv", "exceptions/exceptions_criteria.csv", commitment_id)

    # Load and prepare policy pages
    pages = load_pdf_pages(pdf_source)
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
    print_debug_section("POLICY PAGES", content=policy_pages, enabled=policy_debug)

    print_debug_section("INPUTS", sections={
        "ASSESSMENT DATE": assessment_date,
        "COMMITMENT DESCRIPTION": commitment_description,
        "COMMITMENT GUIDELINES": commitment_guidelines,
        "COMMITMENT EXAMPLES": commitment_examples,
        "EXCEPTION TAXONOMY": exception_taxonomy
    }, enabled=input_debug)

    @openai_retry
    def assess_policy(messages):
        """
        Assess policy with retry logic for rate limit errors.
        """
        nonlocal total_tokens_used

        # Create chat completion
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=tools,
            tool_choice={
                "type": "function",
                "function": {"name": "assess_commitment_exceptions"}
            },
            temperature=0
        )

        # Track token usage
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
        #     "content": POLICY_PAGES_ABN
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
    if interactive_mode and assessment.get('references'):
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

    # # Load original pages for reference validation
    # original_pages = load_pdf_pages(pdf_source)

    # # Validate references against original document
    # validated_assessment = validate_references(filtered_assessment, original_pages)

    # # Print the final processed output
    # print("=== FILTERED AND VALIDATED ASSESSMENT ===")
    # print(json.dumps(validated_assessment, indent=2))

    print(f"\n=== TOTAL TOKENS USED: {total_tokens_used} ===")

    return filtered_assessment

if __name__ == "__main__":
    # Default configuration for standalone execution
    run_single_step_analysis(
        commitment_id="CP.2",
        pdf_source="policies/Barclays/Climate change statement (Feb 2024).pdf",
        model_name="gpt-4o",
        policy_debug=False,
        input_debug=False,
        interactive_mode=True
    )


