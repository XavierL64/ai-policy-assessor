tools = [
    {
        "type": "function",
        "function": {
            "name": "assess_commitment_exceptions",
            "description": "Assess whether the policy contains the specified commitment and identify any applicable exceptions and their mitigants.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "commitment": {
                        "type": "boolean",
                        "description": "True if the policy contains the specified commitment."
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

tools_ref = [
    {
        "type": "function",
        "function": {
            "name": "assess_commitment_exceptions",
            "description": "Assess whether the policy contains the specified commitment and identify any applicable exceptions and their mitigants.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "commitment": {
                        "type": "boolean",
                        "description": "True if the policy contains the specified commitment."
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
                    },
                    "references": {
                        "type": "array",
                        "description": "List of text excerpts from the policy that support the assessment (empty array if none).",
                        "items": {
                            "type": "object",
                            "properties": {
                                "excerpt": {
                                    "type": "string",
                                    "description": "Verbatim excerpt of the relevant policy text."
                                },
                                "document_name": {
                                    "type": "string",
                                    "description": "The name of the source document."
                                },
                                "page_start": {
                                    "type": "integer",
                                    "description": "The page number where the excerpt starts."
                                },
                                "page_end": {
                                    "type": "integer",
                                    "description": "The page number where the excerpt ends (same as start if within one page)."
                                }
                            },
                            "required": ["excerpt", "document_name", "page_start", "page_end"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["commitment", "exceptions", "references"],
                "additionalProperties": False
            }
        }
    }
]

tools_deprecated_format = [
    {
        "type": "function",
        "name": "assess_commitment_exceptions",
        "description": "Assess whether the policy contains the specified commitment and identify any applicable exceptions and their mitigants.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "commitment": {
                    "type": "boolean",
                    "description": "True if the policy contains the specified commitment."
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
                            },
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

]