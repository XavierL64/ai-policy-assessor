from utils import load_criteria, load_exceptions
from assessment_examples import POLICY_EXTRACT_ABN, POLICY_PAGES_ABN, POLICY_EXTRACT_HSBC, POLICY_PAGES_HSBC, POLICY_EXTRACT_BBVA, POLICY_PAGES_BBVA, POLICY_EXTRACT_BARCLAYS, POLICY_PAGES_BARCLAYS
import json

# Load criteria and exceptions
criteria = load_criteria("CP.1", "criteria/criteria.csv")
criteria_description = criteria['criteria_description']
criteria_guidelines = criteria['criteria_guidelines']
exception_taxonomy = load_exceptions("exceptions/exceptions.csv")

# Prepare input for the model
input_abn= f"""
Policy pages to assess:
<<<POLICY_PAGES>>>
{POLICY_PAGES_ABN}
<<<END_POLICY_PAGES>>>

Criteria description:
<<<CRITERIA_DESCRIPTION>>>
{criteria_description}
<<<END_CRITERIA_DESCRIPTION>>>

Criteria assessment guidelines:
<<<CRITERIA_GUIDELINES>>>
{criteria_guidelines}
<<<END_CRITERIA_GUIDELINES>>>

Exception taxonomy (list of dictionaries with keys: "ID", "definition", "mitigant"):
<<<EXCEPTION_TAXONOMY>>>
{json.dumps(exception_taxonomy)}
<<<END_EXCEPTION_TAXONOMY>>>
"""

input_hsbc= f"""
Policy pages to assess:
<<<POLICY_PAGES>>>
{POLICY_PAGES_HSBC}
<<<END_POLICY_PAGES>>>

Criteria description:
<<<CRITERIA_DESCRIPTION>>>
{criteria_description}
<<<END_CRITERIA_DESCRIPTION>>>

Criteria assessment guidelines:
<<<CRITERIA_GUIDELINES>>>
{criteria_guidelines}
<<<END_CRITERIA_GUIDELINES>>>

Exception taxonomy (list of dictionaries with keys: "ID", "definition", "mitigant"):
<<<EXCEPTION_TAXONOMY>>>
{json.dumps(exception_taxonomy)}
<<<END_EXCEPTION_TAXONOMY>>>
"""

input_bbva= f"""
Policy pages to assess:
<<<POLICY_PAGES>>>
{POLICY_PAGES_BBVA}
<<<END_POLICY_PAGES>>>

Criteria description:
<<<CRITERIA_DESCRIPTION>>>
{criteria_description}
<<<END_CRITERIA_DESCRIPTION>>>

Criteria assessment guidelines:
<<<CRITERIA_GUIDELINES>>>
{criteria_guidelines}
<<<END_CRITERIA_GUIDELINES>>>

Exception taxonomy (list of dictionaries with keys: "ID", "definition", "mitigant"):
<<<EXCEPTION_TAXONOMY>>>
{json.dumps(exception_taxonomy)}
<<<END_EXCEPTION_TAXONOMY>>>
"""

input_barclays= f"""
Policy pages to assess:
<<<POLICY_PAGES>>>
{POLICY_PAGES_BARCLAYS}
<<<END_POLICY_PAGES>>>

Criteria description:
<<<CRITERIA_DESCRIPTION>>>
{criteria_description}
<<<END_CRITERIA_DESCRIPTION>>>

Criteria assessment guidelines:
<<<CRITERIA_GUIDELINES>>>
{criteria_guidelines}
<<<END_CRITERIA_GUIDELINES>>>

Exception taxonomy (list of dictionaries with keys: "ID", "definition", "mitigant"):
<<<EXCEPTION_TAXONOMY>>>
{json.dumps(exception_taxonomy)}
<<<END_EXCEPTION_TAXONOMY>>>
"""
