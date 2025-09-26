import os
from dotenv import load_dotenv
from openai import OpenAI
from utils import filter_exceptions, validate_references, load_pdf_pages
from function_schema import tools, tools_ref
from assessment_examples import ASSESSMENT_ABN, ASSESSMENT_HSBC, ASSESSMENT_BBVA, ASSESSMENT_BARCLAYS
from inputs_definitions import input_abn, input_hsbc, input_bbva, input_barclays, input_ca, input_danske
from prompt_definitions import ROLE, TASK, INPUTS, STEPS, RULES
import json

# Load environment variables
load_dotenv()

# Get the key from the environment
api_key = os.getenv("OPENAI_API_KEY")

# Create messages for the model
messages = [
    {
        "role": "system",
        "content" : ROLE + TASK + INPUTS + STEPS + RULES
    },
    # {
    #     "role": "user",
    #     "content": input_abn
    # },
    # {
    #     "role": "assistant",
    #     "content": json.dumps(ASSESSMENT_ABN)
    # },
    # {
    #     "role": "user",
    #     "content": input_hsbc
    # },
    # {
    #     "role": "assistant",
    #     "content": json.dumps(ASSESSMENT_HSBC)
    # },
    {
        "role": "user",
        "content": input_abn
    }
]

# Create OpenAI client
client = OpenAI(api_key=api_key)

# Create chat completion
response = client.chat.completions.create(
    model="gpt-4.1",
    messages=messages,
    tools=tools_ref,
    tool_choice={
        "type": "function",
        "function": {"name": "assess_commitment_exceptions"}
    },
    # response_format="json",
    # max_response_output_tokens=800,
    temperature=0
)

# Parse the raw tool response
raw_output = response.choices[0].message.tool_calls[0].function.arguments
assessment = json.loads(raw_output)

# Filter exceptions to only those that apply
filtered_assessment = filter_exceptions(assessment)

print(filtered_assessment)

# # Load original pages for reference validation
# document_path = "sources/BBVA/Environmental and Social Framework (Dec 2024).pdf"
# original_pages = load_pdf_pages(document_path)

# # Validate references against original document
# validated_assessment = validate_references(filtered_assessment, original_pages)

# # Print the final processed output
# print("=== FILTERED AND VALIDATED ASSESSMENT ===")
# print(json.dumps(validated_assessment, indent=2))


