ROLE = """
You are a highly specialized sustainable finance analyst trained to evaluate banks’ thermal coal policies. You are meticulous, consistent, and strictly neutral,  relying only on information explicitly stated in the policies.
"""

TASK = """
Your task is to:
- Assess whether the policy meets the specified criteria based on the criteria guidelines.
- Determine if any exceptions apply based on the exception taxonomy.
"""

# for few-shot prompting
INPUTS1 = """
- excerpt: policy extract to assess.
- criteria_description: criteria to assess.
- criteria_guidelines: instructions for assessing the criteria.
- exception_taxonomy: a list of exceptions with IDs, definitions, and mitigants.
"""

# without few-shot prompting
INPUTS2 = f"""
Policy extract to assess:
<<<POLICY_EXTRACT>>>
{policy_extract}
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

STEPS = f"""
Follow these steps:

1. Determine commitment
- If the policy includes a clear commitment for the criteria, set `"commitment": true`; otherwise, false.
	
2. Assess exceptions
- If `"commitment"` is true, evaluate every exception in the taxonomy.
- For each exception, return:
	○ "exception_id": ID from the taxonomy.  
	○ "applies": true if the exception applies, otherwise false.  
	○ "description": short description ≤ {DESCRIPTION_LENGTH} words if applies, else null.
	○ "mitigated": true if a mitigant clearly applies, else false.  
	○ "mitigant": short description ≤ {DESCRIPTION_LENGTH} words if mitigated, else null. 
- If `"commitment"` is false, return `"exceptions": []`.
"""

RULES = """
Strict rules:
- Include all exceptions from the taxonomy, even if they do not apply.  
- Never invent IDs, exceptions, or mitigants not in the taxonomy.  
- Never infer commitments, exceptions, or mitigants not explicitly supported by the policy extract.  
- Output valid JSON strictly following the function schema.  
- Return only the JSON object. Do not include any other text.
- For borderline cases, only mark as true if explicit evidence exists.
"""

policy_extract_hsbc = """
HSBC will not provide new finance, or new advisory services, for the specific purposes of activities that do not align with HSBC’s Phase Out Commitment timelines as outlined below:
creation of new thermal coal assets; thermal coal expansion; extensions to the unabated operating lifetime of existing thermal coal assets; new captive thermal coal-fired power plants or new captive thermal coal mines; thermal coal assets or metallurgical coal mines operating in environmentally and socially critical areas or using Mountaintop Removal (including clients who derive more than 30% of their annual revenues from Mountaintop Removal coal mining).

[p4; Thermal Coal Phase-out Policy (Feb 2025); https://www.hsbc.com/-/files/hsbc/our-approach/risk-and-responsibility/pdfs/250219-hsbc-thermal-coal-phase-out-policy.pdf?download=1]

Captive thermal coal mines: thermal coal mines dedicated to providing thermal coal for captive thermal coal-fired  power plants. 
[...]
Exempted activities: Means the following: 
• existing captive thermal coal-fired power plants; 
• existing captive thermal coal mines;
• coal services: Coal trading, coal logistics, coal processing, transmission from thermal coal-fired power plants, coal-related operation & maintenance (O&M) services, coal mining  services, coal-related engineering, procurement and construction services, coal exploration, coal equipment manufacturing and coal advisory services. For the avoidance of doubt, the Policy does apply to clients engaged in new captive  thermal coal-fired power plants and new captive thermal coal mines.
[...]
Thermal coal assets: thermal coal mines, thermal coal-fired power plants and coal to gas / liquids plants.
[...] 
New thermal coal assets: means new thermal coal mines, new thermal coal-fired  power plants and new coal to gas / liquids plants.
The terms thermal coal assets and new thermal coal assets do not include exempted activities.
[...] 
Thermal coal expansion: Means expansion via new thermal coal assets and/or expanding existing thermal coal assets, as per: i) for thermal coal mining, increases in total tonnage of thermal coal extracted, in each case where such expansion: was not already either: (a) contractually committed (via power purchase  agreement for thermal coal-fired power generation); or (b) under construction,  in each case before 01 January 2021; and does not include exempted activities. This includes expansion via corporate mergers and acquisition unless the client has confirmed phase-out of these assets will be line with HSBC’s 2030/40 timelines, and  the transaction does not involve a global increase in tonnage or power capacity.
[...]
Thermal coal mines: All mines where more than 30% of either production or the coal reserve is thermal coal. new thermal coal mines: i) the creation and commercialisation of new thermal coal mines or major capital  equipment for new thermal coal mines; or ii) expansions to existing thermal coal mines that involve geographically separate  locations and/or major new infrastructure that was not already either: a) contractually committed or b) under construction, in  each case before 1 January 2021.
The terms thermal coal mines and new thermal coal mines do not include exempted  activities.

[p 8-10; Thermal Coal Phase-out Policy (Feb 2025); https://www.hsbc.com/-/files/hsbc/our-approach/risk-and-responsibility/pdfs/250219-hsbc-thermal-coal-phase-out-policy.pdf?download=1]
"""

criteria_description = """
Does the bank exclude dedicated finance for thermal coal power projects?
"""

criteria_guidelines = """
Exclusion of dedicated finance for new projects or expansions of existing projects. 
Dedicated finance includes project finance, direct finance, and any financing with a known use of proceeds.
It excludes general corporate purpose or client financing unless the funds are explicitly provided for a specific project or activity, in which case it is considered dedicated finance.
"""

USER_EXAMPLE_HSBC = f"""
- excerpt: {policy_extract_hsbc}
- criteria_description: {criteria_description}
- criteria_guidelines: {criteria_guidelines}
- exception_taxonomy: {exception_taxonomy}
"""

ASSISTANT_EXAMPLE_HSBC = {
    "commitment": True,
    "exceptions": [
        {
            "exception_id": "CP.EX1",
            "applies": False,
            "description": None,
            "mitigated": False,
            "mitigant": None
        },
        {
            "exception_id": "CP.EX2",
            "applies": False,
            "description": None,
            "mitigated": False,
            "mitigant": None
        },
		{
			"exception_id": "CP.EX3",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
        {
			"exception_id": "CP.EX4",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
		{
			"exception_id": "CP.EX5",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
		{
			"exception_id": "CP.EX6",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
		{
			"exception_id": "CP.EX7",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
		{
			"exception_id": "CP.EX8",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
		{
			"exception_id": "CP.EX9",
			"applies": True,
			"description": "expansion via corporate mergers and acquisition.",
			"mitigated": True,
			"mitigant": "client has confirmed phase-out of these assets will be in line with HSBC’s 2030/40 timelines."
		},
        {
            "exception_id": "CP.EX10",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
        {
            "exception_id": "CP.EX11",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
        {
            "exception_id": "CP.EX12",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
        {
            "exception_id": "CP.EX13",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
        {
            "exception_id": "CP.EX14",
			"applies": True,
			"description": "expansion that was already contractually committed.",
			"mitigated": False,
			"mitigant": None
		},
        {
            "exception_id": "CP.EX15",
			"applies": True,
			"description": "existing captive thermal coal-fired power plants.",
			"mitigated": False,
			"mitigant": None
		},
        {
            "exception_id": "CP.EX16",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
        {
            "exception_id": "CP.EX17",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
        {
            "exception_id": "CP.EX18",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
        {
            "exception_id": "CP.EX19",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
        {
            "exception_id": "CP.EX20",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
        {
            "exception_id": "CP.EX21",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
        {
            "exception_id": "CP.EX22",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
        {
            "exception_id": "CP.EX23",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
        {
            "exception_id": "CP.EX24",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
        {
            "exception_id": "CP.EX25",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
        {
            "exception_id": "CP.EX26",
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
    ]
}

 