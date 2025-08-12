tools = [
    {
        "type": "function",
        "function": {
            "name": "assess_commitment_exceptions",
            "description": "Assess whether the policy contains a commitment for the relevant criteria and identify any applicable exceptions and their mitigants.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "commitment": {
                        "type": "boolean",
                        "description": "True if the policy contains a commitment for the relevant criteria."
                    },
                    "exceptions": {
                        "type": "array",
                        "description": "List of exceptions identified in the policy (empty array if none).",
                        "items": {
                            "type": "object",
                            "properties": {
                                "exception_id": {
                                    "type": "string",
                                    "description": "ID of the exception from the exceptions taxonomy."
                                },
                                "applies": {
                                    "type": "boolean",
                                    "description": "True if the exception applies."
                                },
                                "description": {
                                    "type": ["string", "null"],
                                    "description": "Short description of the exception if it applies."
                                },
                                "mitigated": {
                                    "type": "boolean",
                                    "description": "True if the exception is mitigated, based on mitigants defined in the exceptions taxonomy."
                                },
                                "mitigant": {
                                    "type": ["string", "null"],
                                    "description": "Short description of the mitigant if the exception is mitigated."
                                }
                            },
                            "required": [
                                "exception_id",
                                "applies",
                                "description",
                                "mitigated",
                                "mitigant"
                            ],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["commitment", "exceptions"],
                "additionalProperties": False
            }
        }
    }
]


# tools = [
#     {
#         "type": "function",
#         "name": "assess_commitment_exceptions",
#         "description": "Assess whether the policy contains a commitment for the relevant criteria and identify any applicable exceptions and their mitigants.",
#         "strict": True,
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "commitment": {
#                     "type": "boolean",
#                     "description": "True if the policy contains a commitment for the relevant criteria."
#                 },
#                 "exceptions": {
#                     "type": "array",
#                     "description": "List of exceptions identified in the policy (empty array if none).",
#                     "items": {
#                         "type": "object",
#                         "properties": {
#                             "exception_id": {
#                                 "type": "string",
#                                 "description": "ID of the exception from the exceptions taxonomy."
#                             },
#                             "applies": {
#                                 "type": "boolean",
#                                 "description": "True if the exception applies."
#                             },
#                             "description": {
#                                 "type": ["string", "null"],
#                                 "description": "Short description of the exception if it applies."
#                             },
#                             "mitigated": {
#                                 "type": "boolean",
#                                 "description": "True if the exception is mitigated, based on mitigants defined in the exceptions taxonomy."
#                             },
#                             "mitigant": {
#                                 "type": ["string", "null"],
#                                 "description": "Short description of the mitigant if the exception is mitigated."
#                             },
#                         },
#                         "required": [
#                             "exception_id",
#                             "applies",
#                             "description",
#                             "mitigated",
#                             "mitigant"
#                         ],
#                         "additionalProperties": False
#                     }
#                 }
#             },
#             "required": ["commitment", "exceptions"],
#             "additionalProperties": False
#         }
#     }

# ]