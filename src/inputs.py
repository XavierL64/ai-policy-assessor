from utils import load_commitment, load_exceptions, load_pdf_pages, build_page_pack
from assessment_examples import POLICY_EXTRACT_ABN, POLICY_PAGES_ABN, POLICY_EXTRACT_HSBC, POLICY_PAGES_HSBC, POLICY_EXTRACT_BBVA, POLICY_PAGES_BBVA, POLICY_EXTRACT_BARCLAYS, POLICY_PAGES_BARCLAYS
import json

# Load commitment and exceptions
commitment = load_commitment("CP.1", "criteria/criteria.csv")
commitment_description = commitment['commitment_description']
commitment_guidelines = commitment['commitment_guidelines']
commitment_examples = commitment['commitment_examples']
exception_taxonomy = load_exceptions("exceptions/exceptions.csv", "exceptions/exceptions_criteria.csv", "CP.1")

# Load and prepare policy pages
pages = load_pdf_pages("sources/BBVA/Environmental and Social Framework (Dec 2024).pdf")
policy_pages = build_page_pack(pages)

# Prepare input for the model

input_abn= f"""
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

Exception taxonomy:
<<<EXCEPTION_TAXONOMY>>>
{json.dumps(exception_taxonomy)}
<<<END_EXCEPTION_TAXONOMY>>>
"""

input_hsbc= f"""
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

Exception taxonomy:
<<<EXCEPTION_TAXONOMY>>>
{json.dumps(exception_taxonomy)}
<<<END_EXCEPTION_TAXONOMY>>>
"""

input_bbva= f"""
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

Exception taxonomy:
<<<EXCEPTION_TAXONOMY>>>
{json.dumps(exception_taxonomy)}
<<<END_EXCEPTION_TAXONOMY>>>
"""

input_barclays= f"""
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

Exception taxonomy:
<<<EXCEPTION_TAXONOMY>>>
{json.dumps(exception_taxonomy)}
<<<END_EXCEPTION_TAXONOMY>>>
"""

input_ca= f"""
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

Exception taxonomy:
<<<EXCEPTION_TAXONOMY>>>
{json.dumps(exception_taxonomy)}
<<<END_EXCEPTION_TAXONOMY>>>
"""

input_danske= f"""
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

Exception taxonomy:
<<<EXCEPTION_TAXONOMY>>>
{json.dumps(exception_taxonomy)}
<<<END_EXCEPTION_TAXONOMY>>>
"""