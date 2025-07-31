function_schema = {
    "name": "assess_commitment_exceptions",
    "description": "Assess whether the policy contains a commitment for the relevant criteria and identify exceptions, including types and mitigation outcomes, based on the exemption taxonomy.",
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
                        "exception_type": {
                            "type": "string",
                            "enum": ["material", "technical"],
                            "description": "Type assigned to the exception in the exceptions taxonomy."
                        },
                        "mitigated": {
                            "type": "boolean",
                            "description": "Whether the exception is mitigated, based on mitigants defined in the exceptions taxonomy."
                        },
                        "mitigant": {
                            "type": ["string", "null"],
                            "description": "Short description of the mitigant if the exception is mitigated."
                        },
                        "final_type": {
                            "type": "string",
                            "enum": ["material", "technical", "no exception"],
                            "description": "Final type after considering mitigation, based on the mitigant outcome defined in the exceptions taxonomy."
                        }
                    },
                    "required": [
                        "exception_id",
                        "applies",
                        "exception_type",
                        "mitigated",
                        "final_type"
                    ]
                }
            }
        },
        "required": ["commitment", "exceptions"]
    }
}