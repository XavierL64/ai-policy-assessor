from utils import (load_commitment, load_exceptions, load_pdf_pages, build_page_pack,
                   detect_definitions_section, split_policy_and_definitions)
from assessment_examples import POLICY_EXTRACT_ABN, POLICY_PAGES_ABN, POLICY_EXTRACT_HSBC, POLICY_PAGES_HSBC, POLICY_EXTRACT_BBVA, POLICY_PAGES_BBVA, POLICY_EXTRACT_BARCLAYS, POLICY_PAGES_BARCLAYS
import json

# Load commitment and exceptions
commitment = load_commitment("CP.1", "criteria/criteria.csv")
commitment_description = commitment['commitment_description']
commitment_guidelines = commitment['commitment_guidelines']
commitment_examples = commitment['commitment_examples']
exception_taxonomy = load_exceptions("exceptions/exceptions.csv", "exceptions/exceptions_criteria.csv", "CP.1")

# Load and prepare policy pages with definitions detection
pages = load_pdf_pages("sources/ABN/Exclusion list (Mar 2021).pdf")

# Check for definitions section and split if found
definitions_info = detect_definitions_section(pages)
if definitions_info['has_definitions']:
    split_result = split_policy_and_definitions(pages, definitions_info)
    policy_pages = build_page_pack(split_result['policy_pages'])
    definitions_pages = build_page_pack(split_result['definitions_pages'])
else:
    policy_pages = build_page_pack(pages)
    definitions_pages = ""

# Prepare input for the model with definitions section

input_abn = f"""
Policy pages to assess:
<<<POLICY_PAGES>>>
{policy_pages}
<<<END_POLICY_PAGES>>>

Definitions section:
<<<DEFINITIONS_PAGES>>>
{definitions_pages if definitions_pages else "No definitions section available."}
<<<END_DEFINITIONS_PAGES>>>

Commitment description:
<<<COMMITMENT_DESCRIPTION>>>
{commitment_description}
<<<END_COMMITMENT_DESCRIPTION>>>

Commitment assessment guidelines:
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

input_hsbc = f"""
Policy pages to assess:
<<<POLICY_PAGES>>>
{policy_pages}
<<<END_POLICY_PAGES>>>

Definitions section:
<<<DEFINITIONS_PAGES>>>
{definitions_pages if definitions_pages else "No definitions section available."}
<<<END_DEFINITIONS_PAGES>>>

Commitment description:
<<<COMMITMENT_DESCRIPTION>>>
{commitment_description}
<<<END_COMMITMENT_DESCRIPTION>>>

Commitment assessment guidelines:
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

input_bbva = f"""
Policy pages to assess:
<<<POLICY_PAGES>>>
{policy_pages}
<<<END_POLICY_PAGES>>>

Definitions section:
<<<DEFINITIONS_PAGES>>>
{definitions_pages if definitions_pages else "No definitions section available."}
<<<END_DEFINITIONS_PAGES>>>

Commitment description:
<<<COMMITMENT_DESCRIPTION>>>
{commitment_description}
<<<END_COMMITMENT_DESCRIPTION>>>

Commitment assessment guidelines:
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

input_barclays = f"""
Policy pages to assess:
<<<POLICY_PAGES>>>
{policy_pages}
<<<END_POLICY_PAGES>>>

Definitions section:
<<<DEFINITIONS_PAGES>>>
{definitions_pages if definitions_pages else "No definitions section available."}
<<<END_DEFINITIONS_PAGES>>>

Commitment description:
<<<COMMITMENT_DESCRIPTION>>>
{commitment_description}
<<<END_COMMITMENT_DESCRIPTION>>>

Commitment assessment guidelines:
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

input_ca = f"""
Policy pages to assess:
<<<POLICY_PAGES>>>
{policy_pages}
<<<END_POLICY_PAGES>>>

Definitions section:
<<<DEFINITIONS_PAGES>>>
{definitions_pages if definitions_pages else "No definitions section available."}
<<<END_DEFINITIONS_PAGES>>>

Commitment description:
<<<COMMITMENT_DESCRIPTION>>>
{commitment_description}
<<<END_COMMITMENT_DESCRIPTION>>>

Commitment assessment guidelines:
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

input_danske = f"""
Policy pages to assess:
<<<POLICY_PAGES>>>
{policy_pages}
<<<END_POLICY_PAGES>>>

Definitions section:
<<<DEFINITIONS_PAGES>>>
{definitions_pages if definitions_pages else "No definitions section available."}
<<<END_DEFINITIONS_PAGES>>>

Commitment description:
<<<COMMITMENT_DESCRIPTION>>>
{commitment_description}
<<<END_COMMITMENT_DESCRIPTION>>>

Commitment assessment guidelines:
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
