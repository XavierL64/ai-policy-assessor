import os
from dotenv import load_dotenv
from openai import OpenAI
from utils import load_criteria, load_exceptions, filter_exceptions
from function_schema import tools
from assessment_examples import POLICY_EXTRACT_ABN, ASSESSMENT_ABN, POLICY_EXTRACT_HSBC, ASSESSMENT_HSBC, POLICY_EXTRACT_BBVA, ASSESSMENT_BBVA, POLICY_EXTRACT_BARCLAYS
from prompt import ROLE, TASK, INPUTS, STEPS, RULES
import json

# Load environment variables from .env file
load_dotenv()

# Get the key from the environment
api_key = os.getenv("OPENAI_API_KEY")


# Load criteria and exceptions
criteria = load_criteria("CP.1", "criteria/criteria.csv")
criteria_description = criteria['criteria_description']
criteria_guidelines = criteria['criteria_guidelines']
exception_taxonomy = load_exceptions("exceptions/exceptions.csv")

# Prepare input for the model
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
{json.dumps(exception_taxonomy)}
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
{json.dumps(exception_taxonomy)}
<<<END_EXCEPTION_TAXONOMY>>>
"""

input_bbva= f"""
Policy extract to assess:
<<<POLICY_EXTRACT>>>
{POLICY_EXTRACT_BBVA}
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
{json.dumps(exception_taxonomy)}
<<<END_EXCEPTION_TAXONOMY>>>
"""

input_barclays= f"""
Policy extract to assess:
<<<POLICY_EXTRACT>>>
{POLICY_EXTRACT_BARCLAYS}
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
{json.dumps(exception_taxonomy)}
<<<END_EXCEPTION_TAXONOMY>>>
"""

# Create messages for the model
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
        "content": json.dumps(ASSESSMENT_ABN)
    },
    {
        "role": "user",
        "content": input_hsbc
    },
    {
        "role": "assistant",
        "content": json.dumps(ASSESSMENT_HSBC)
    },
    {
        "role": "user",
        "content": input_barclays
    }
]

# Create OpenAI client
client = OpenAI(api_key=api_key)

# Create chat completion
response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
    tool_choice={
        "type": "function",
        "function": {"name": "assess_commitment_exceptions"}
    },
    # response_format="json",
    # max_response_output_tokens=800,
    temperature=0
)

output = response.choices[0].message.tool_calls[0].function.arguments

print(filter_exceptions(json.loads(output)))


