import os
from dotenv import load_dotenv
from openai import OpenAI
from utils import filter_exceptions
from function_schema import tools, tools_ref
from assessment_examples import ASSESSMENT_ABN, ASSESSMENT_HSBC, ASSESSMENT_BBVA, ASSESSMENT_BARCLAYS
from inputs import input_abn, input_hsbc, input_bbva, input_barclays
from prompt import ROLE, TASK, INPUTS, STEPS, RULES
import json

# Load environment variables from .env file
load_dotenv()

# Get the key from the environment
api_key = os.getenv("OPENAI_API_KEY")

# Create messages for the model
messages = [
    {
        "role": "system",
        "content" : ROLE + TASK + INPUTS + STEPS + RULES
    },
    {
        "role": "user",
        "content": input_bbva
    },
    {
        "role": "assistant",
        "content": json.dumps(ASSESSMENT_BBVA)
    },
    {
        "role": "user",
        "content": input_barclays
    },
    {
        "role": "assistant",
        "content": json.dumps(ASSESSMENT_BARCLAYS)
    },
    {
        "role": "user",
        "content": input_abn
    }
]

# Create OpenAI client
client = OpenAI(api_key=api_key)

# Create chat completion
response = client.chat.completions.create(
    model="gpt-4o",
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

# tool response
output = response.choices[0].message.tool_calls[0].function.arguments

# filtered response
print(output)


