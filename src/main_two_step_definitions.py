import os
from dotenv import load_dotenv
from openai import OpenAI
from utils import (load_criteria, load_exceptions, load_pdf_pages, build_page_pack,
                   get_exception_examples, detect_definitions_section, split_policy_and_definitions)
from function_schema_two_step import assess_commitment_schema, assess_exception_schema
from prompt_two_step_definitions import build_commitment_prompt, build_exception_prompt
import json

# Load environment variables
load_dotenv()

# Get the API key from the environment
api_key = os.getenv("OPENAI_API_KEY")

# Create OpenAI client
client = OpenAI(api_key=api_key)

def assess_commitment_step_with_definitions(policy_pages, definitions_pages, criteria_description, criteria_guidelines, criteria_examples):
    """
    Step 1: Assess whether the policy contains a commitment for the criteria, with definitions awareness.
    """

    # Build the commitment assessment prompt with definitions
    commitment_input = f"""
Policy pages to assess:
<<<POLICY_PAGES>>>
{policy_pages}
<<<END_POLICY_PAGES>>>

Definitions section:
<<<DEFINITIONS_PAGES>>>
{definitions_pages if definitions_pages else "No definitions section available."}
<<<END_DEFINITIONS_PAGES>>>

Criteria description:
<<<CRITERIA_DESCRIPTION>>>
{criteria_description}
<<<END_CRITERIA_DESCRIPTION>>>

Criteria assessment guidelines:
<<<CRITERIA_GUIDELINES>>>
{criteria_guidelines}
<<<END_CRITERIA_GUIDELINES>>>

Criteria examples:
<<<CRITERIA_EXAMPLES>>>
{criteria_examples}
<<<END_CRITERIA_EXAMPLES>>>
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

    # Create chat completion for commitment assessment
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=messages,
        tools=assess_commitment_schema,
        tool_choice={
            "type": "function",
            "function": {"name": "assess_commitment"}
        },
        temperature=0
    )

    # Parse the response
    raw_output = response.choices[0].message.tool_calls[0].function.arguments
    return json.loads(raw_output)

def assess_exception_step_with_definitions(policy_pages, definitions_pages, exception_data, criteria_id, criteria_description, criteria_guidelines):
    """
    Step 2: Assess whether a specific exception applies and if it is mitigated, with definitions awareness.
    """

    # Extract specific examples for this exception and criteria
    examples = get_exception_examples(
        exception_data['exception_id'],
        "exceptions/exceptions_criteria.csv",
        criteria_id
    )

    # Build the exception assessment prompt with definitions
    exception_input = f"""
Policy pages to assess:
<<<POLICY_PAGES>>>
{policy_pages}
<<<END_POLICY_PAGES>>>

Definitions section:
<<<DEFINITIONS_PAGES>>>
{definitions_pages if definitions_pages else "No definitions section available."}
<<<END_DEFINITIONS_PAGES>>>

Criteria description:
<<<CRITERIA_DESCRIPTION>>>
{criteria_description}
<<<END_CRITERIA_DESCRIPTION>>>

Criteria assessment guidelines:
<<<CRITERIA_GUIDELINES>>>
{criteria_guidelines}
<<<END_CRITERIA_GUIDELINES>>>

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

    # Create chat completion for exception assessment
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=messages,
        tools=assess_exception_schema,
        tool_choice={
            "type": "function",
            "function": {"name": "assess_exception"}
        },
        temperature=0
    )

    # Parse the response
    raw_output = response.choices[0].message.tool_calls[0].function.arguments
    return json.loads(raw_output)

def run_two_step_analysis_with_definitions():
    """
    Main function to run the two-step analysis approach with definitions awareness.
    """

    # Load criteria and exceptions
    criteria = load_criteria("CP.1", "criteria/criteria.csv")
    criteria_description = criteria['criteria_description']
    criteria_guidelines = criteria['criteria_guidelines']
    criteria_examples = criteria['criteria_examples']
    exception_taxonomy = load_exceptions("exceptions/exceptions.csv", "exceptions/exceptions_criteria.csv", "CP.1")

    # Load and prepare policy pages
    pages = load_pdf_pages("sources/ABN/Exclusion list (Mar 2021).pdf")

    # Check for definitions section
    print("=== CHECKING FOR DEFINITIONS SECTION ===")
    definitions_info = detect_definitions_section(pages)

    if definitions_info['has_definitions']:
        print(f"[+] Definitions section detected on page {definitions_info['start_page']}")
        print(f"  Section title: {definitions_info['section_title']}")
        print(f"  Preview: {definitions_info['detected_text'][:100]}...")

        # Split policy into policy content and definitions
        split_result = split_policy_and_definitions(pages, definitions_info)
        policy_pages = build_page_pack(split_result['policy_pages'])
        definitions_pages = build_page_pack(split_result['definitions_pages'])

        print(f"  Policy pages: {len(split_result['policy_pages'])}")
        print(f"  Definitions pages: {len(split_result['definitions_pages'])}")
    else:
        print("[-] No definitions section detected")
        policy_pages = build_page_pack(pages)
        definitions_pages = ""

    print("\n=== STEP 1: ASSESSING COMMITMENT ===")

    # Step 1: Assess commitment with definitions awareness
    commitment_result = assess_commitment_step_with_definitions(
        policy_pages,
        definitions_pages,
        criteria_description,
        criteria_guidelines,
        criteria_examples
    )

    print(f"Commitment: {commitment_result['commitment']}")
    print(f"Commitment references: {len(commitment_result['references'])}")

    # Step 2: Assess exceptions (only if commitment is True)
    exceptions_results = []

    if commitment_result['commitment']:
        print(f"\n=== STEP 2: ASSESSING {len(exception_taxonomy)} EXCEPTIONS ===")

        for i, exception_data in enumerate(exception_taxonomy, 1):
            print(f"Assessing exception {i}/{len(exception_taxonomy)}: {exception_data['exception_id']}")

            exception_result = assess_exception_step_with_definitions(
                policy_pages,
                definitions_pages,
                exception_data,
                "CP.1",
                criteria_description,
                criteria_guidelines
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
        "exceptions": exceptions_results,
        "definitions_detected": definitions_info['has_definitions'],
        "definitions_info": definitions_info if definitions_info['has_definitions'] else None
    }

    print("\n=== FINAL ASSESSMENT ===")
    print(json.dumps(final_assessment, indent=2))

    return final_assessment

if __name__ == "__main__":
    run_two_step_analysis_with_definitions()