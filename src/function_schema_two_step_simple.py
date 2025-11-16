# Function schemas for two-step simple analysis approach

# Step 1: Assess commitment
assess_commitment_schema = [
    {
        "type": "function",
        "function": {
            "name": "assess_commitment",
            "description": "Assess whether the policy contains the specified commitment.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "commitment": {
                        "type": "boolean",
                        "description": "True if the policy contains the specified commitment."
                    },
                    "references": {
                        "type": "array",
                        "description": "List of text excerpts from the policy that support the commitment assessment (empty array if none).",
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
                "required": ["commitment", "references"],
                "additionalProperties": False
            }
        }
    }
]

# Step 2: Assess all exceptions 
assess_all_exceptions_schema = [
    {
        "type": "function",
        "function": {
            "name": "assess_all_exceptions",
            "description": "Assess whether exceptions apply to the policy and if they are mitigated.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
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
                                "references": {
                                    "type": "array",
                                    "description": "List of text excerpts from the policy that support the exception assessment (empty array if none).",
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
                            "required": ["exception_id", "applies", "description", "mitigated", "mitigant", "references"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["exceptions"],
                "additionalProperties": False
            }
        }
    }
]
