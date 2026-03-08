"""
RAG-specific function-calling schema for programmatic citations.

The model returns evidence as chunk ID lists (not free-form references),
which Python resolves into citation objects after the call.
"""

tools = [
    {
        "type": "function",
        "function": {
            "name": "assess_commitment_exceptions_with_evidence_ids",
            "description": (
                "Assess whether the policy contains the specified commitment and "
                "identify applicable exceptions/mitigants, citing evidence via "
                "retrieved chunk IDs."
            ),
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "commitment": {
                        "type": "boolean",
                        "description": "True if the commitment is explicitly supported by evidence."
                    },
                    "commitment_evidence_chunk_ids": {
                        "type": "array",
                        "description": "Chunk IDs supporting commitment=true. Empty when commitment=false.",
                        "items": {"type": "string"},
                    },
                    "exceptions": {
                        "type": "array",
                        "description": (
                            "Exception assessments. Include all exceptions in taxonomy when commitment=true; "
                            "empty when commitment=false."
                        ),
                        "items": {
                            "type": "object",
                            "properties": {
                                "exception_id": {
                                    "type": "string",
                                    "description": "ID from the provided exception taxonomy."
                                },
                                "applies": {
                                    "type": "boolean",
                                    "description": "True if exception applies."
                                },
                                "description": {
                                    "type": ["string", "null"],
                                    "description": "Short explanation if applies=true, else null."
                                },
                                "mitigated": {
                                    "type": "boolean",
                                    "description": "True if exception is mitigated by evidence."
                                },
                                "mitigant": {
                                    "type": ["string", "null"],
                                    "description": "Short mitigant explanation if mitigated=true, else null."
                                },
                                "evidence_chunk_ids": {
                                    "type": "array",
                                    "description": (
                                        "Chunk IDs supporting this exception assessment "
                                        "(applies and/or mitigated conclusions)."
                                    ),
                                    "items": {"type": "string"},
                                },
                            },
                            "required": [
                                "exception_id",
                                "applies",
                                "description",
                                "mitigated",
                                "mitigant",
                                "evidence_chunk_ids",
                            ],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": [
                    "commitment",
                    "commitment_evidence_chunk_ids",
                    "exceptions",
                ],
                "additionalProperties": False,
            },
        },
    }
]
