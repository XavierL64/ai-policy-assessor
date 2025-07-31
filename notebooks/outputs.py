# No commitment
output1 = {
    "commitment": False,
    "exceptions": []
}

# Commitment, no exceptions
output2 = {
    "commitment": True,
    "exceptions": []
}

# Commitment with exceptions
output3 = {
    "commitment": True,
    "exceptions": [
        {
            "exception_id": "CP.EX1", # id of the exception - can be found in the exceptions taxonomy
            "applies": False, #  boolean to flag if the exception applies or not
            "description": None, # short description to be returned by the tool if exception applies, based on exception definition and policy extract
            "exception_type": "material", # original type (technical or material) assigned to the exception in the exception taxonomy
            "mitigated": False, # boolean to flag if an exception is mitigated
            "mitigant": None, # short description of the mitigant to be returned by the tool, based on mitigant definition  and policy extract
            "final_type": "no exception" # final type (technical, material, no exception) based on whether the exception is mitigated or not
        },
        {
            "exception_id": "CP.EX4",
            "applies": True,
            "description": "expansion that doesn't increase production by more than 10%.",
            "exception_type": "material",
            "mitigated": False,
            "mitigant": None,
            "final_type": "material"
        },
        {
            "exception_id": "CP.EX9",
            "applies": True,
            "description": "expansion via corporate mergers and acquisition.",
            "exception_type": "material",
            "mitigated": True,
            "mitigant": "client has confirmed phase-out of these assets will be in line with HSBC’s 2030/40 timelines.",
            "final_type": "no exception"
        },
        {
            "exception_id": "CP.EX13",
            "applies": False,
            "description": None,
            "exception_type": "technical",
            "mitigated": False,
            "mitigant": None,
            "final_type": "no exception"
        }
    ]
}