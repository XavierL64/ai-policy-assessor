from openai import OpenAI
from utils import load_criteria, load_exceptions
from function_schema import tools
from assessment_examples import POLICY_EXTRACT_ABN, ASSESSMENT_ABN, POLICY_EXTRACT_HSBC, ASSESSMENT_HSBC
from prompt import ROLE, TASK, INPUTS, STEPS, RULES

criteria = load_criteria("CP.1", "criteria/criteria.csv")
criteria_description = criteria['criteria_description']
criteria_guidelines = criteria['criteria_guidelines']
exception_taxonomy = load_exceptions("exceptions/exceptions.csv")

input_abn= f"""
Policy extract to assess:
<<<POLICY_EXTRACT>>>
{POLICY_EXTRACT_ABN}
<<<END_POLICY_EXTRACT>>>

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
{exception_taxonomy}
<<<END_EXCEPTION_TAXONOMY>>>
"""

input_hsbc= f"""
Policy extract to assess:
<<<POLICY_EXTRACT>>>
{POLICY_EXTRACT_HSBC}
<<<END_POLICY_EXTRACT>>>

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
{exception_taxonomy}
<<<END_EXCEPTION_TAXONOMY>>>
"""

messages = [
    {
        "role": "system",
        "content" : ROLE + TASK + INPUTS + STEPS + RULES
    },
    {
        "role": "user",
        "content": input_abn
    },
    {
        "role": "assistant",
        "content": ASSESSMENT_ABN
    },
    {
        "role": "user",
        "content": input_hsbc
    },
    {
        "role": "assistant",
        "content": ASSESSMENT_HSBC
    }
    
]

client = OpenAI(api_key="ENTER YOUR KEY HERE")

response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=[tools],
    tool_choice={
        "type": "function",
        "function": {"name": "assess_commitment_exceptions"}
    },
    response_format="json",
    temperature=0,
    # max_response_output_tokens=800
)

