### ABN Amro ###

POLICY_EXTRACT_ABN = """
ABN AMRO will not knowingly provide financial products or services that directly facilitate:
[...]
New coal-fired power plants. 
"""

POLICY_PAGES_ABN = """
=== DOC: Exclusion list (Mar 2021) | PAGE: 1 ===
ABN AMRO will not knowingly provide financial products or services that directly facilitate:
=== DOC: Exclusion list (Mar 2021) | PAGE: 2 ===
New coal-fired power plants.
"""

ASSESSMENT_ABN = {
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
			"applies": True,
			"description": "expansion of existing plants.",
			"mitigated": False,
			"mitigant": None
		},
		{
			"exception_id": "CP.EX9",
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
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
        {
            "exception_id": "CP.EX15",
			"applies": False,
			"description": None,
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
            "exception_id": "CP.EX19",
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
            "exception_id": "CP.EX23",
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
    ],
    "references": [
        {
            "excerpt": "ABN AMRO will not knowingly provide financial products or services that directly facilitate: New coal-fired power plants.",
            "document_name": "Exclusion list (Mar 2021)",
            "page_start": 1,
            "page_end": 2
		}
	]
}

### HSBC ###

POLICY_EXTRACT_HSBC = """
HSBC will not provide new finance, or new advisory services, for the specific purposes of activities that do not align with HSBC's Phase Out Commitment timelines as outlined below:
creation of new thermal coal assets; thermal coal expansion; extensions to the unabated operating lifetime of existing thermal coal assets; new captive thermal coal-fired power plants or new captive thermal coal mines; thermal coal assets or metallurgical coal mines operating in environmentally and socially critical areas or using Mountaintop Removal (including clients who derive more than 30% of their annual revenues from Mountaintop Removal coal mining).
 
[...]
Exempted activities: Means the following: 
-  existing captive thermal coal-fired power plants; 
-  existing captive thermal coal mines;
-  coal services: Coal trading, coal logistics, coal processing, transmission from thermal coal-fired power plants, coal-related operation & maintenance (O&M) services, coal mining  services, coal-related engineering, procurement and construction services, coal exploration, coal equipment manufacturing and coal advisory services. For the avoidance of doubt, the Policy does apply to clients engaged in new captive  thermal coal-fired power plants and new captive thermal coal mines.
[...]
Thermal coal assets: thermal coal mines, thermal coal-fired power plants and coal to gas / liquids plants.
[...] 
New thermal coal assets: means new thermal coal mines, new thermal coal-fired  power plants and new coal to gas / liquids plants.
The terms thermal coal assets and new thermal coal assets do not include exempted activities.
[...] 
Thermal coal expansion: Means expansion via new thermal coal assets and/or expanding existing thermal coal assets, as per: i) for thermal coal mining, increases in total tonnage of thermal coal extracted, in each case where such expansion: was not already either: (a) contractually committed (via power purchase  agreement for thermal coal-fired power generation); or (b) under construction,  in each case before 01 January 2021; and does not include exempted activities. This includes expansion via corporate mergers and acquisition unless the client has confirmed phase-out of these assets will be line with HSBC's 2030/40 timelines, and  the transaction does not involve a global increase in tonnage or power capacity.
[...]
Thermal coal mines: All mines where more than 30% of either production or the coal reserve is thermal coal. new thermal coal mines: i) the creation and commercialisation of new thermal coal mines or major capital  equipment for new thermal coal mines; or ii) expansions to existing thermal coal mines that involve geographically separate  locations and/or major new infrastructure that was not already either: a) contractually committed or b) under construction, in  each case before 1 January 2021.
The terms thermal coal mines and new thermal coal mines do not include exempted  activities.
"""

POLICY_PAGES_HSBC = """
=== DOC: Thermal Coal Phase-out Policy (Feb 2025) | PAGE: 4 ===
HSBC will not provide new finance, or new advisory services, for the specific purposes of activities that do not align with HSBC's Phase Out Commitment timelines as outlined below: -  creation of new thermal coal assets; -  thermal coal expansion; -  extensions to the unabated operating lifetime of existing thermal coal assets; -  new captive thermal coal-fired power plants or new captive thermal coal mines; -  conversion of existing coal-to-gas-fired power plants, unless a) the client demonstrates to HSBC its intention to achieve abated power generation and b) the plants do not operate in environmentally and socially critical areas; -  new thermal coal infrastructure; -  new metallurgical coal mines; or -  thermal coal assets or metallurgical coal mines operating in environmentally and socially critical areas or using Mountaintop Removal (including clients who derive more than 30% of their annual revenues from Mountaintop Removal coal mining).
=== DOC: Thermal Coal Phase-out Policy (Feb 2025) | PAGE: 8 ===
exempted activities Means the following: -  existing captive thermal coal-fired power plants; -  existing captive thermal coal mines; -  coal services; -  underground coal gasification (coal bed methane); and -  all other activities of clients. For the avoidance of doubt, the Policy does apply to clients engaged in new captive thermal coal-fired power plants and new captive thermal coal mines.
=== DOC: Thermal Coal Phase-out Policy (Feb 2025) | PAGE: 9 ===
thermal coal assets new thermal coal assets thermal coal mines, thermal coal-fired power plants and coal to gas / liquids plants. new thermal coal assets means new thermal coal mines, new thermal coal-fired power plants and new coal to gas / liquids plants. The terms thermal coal assets and new thermal coal assets do not include exempted activities.
thermal coal expansion Means expansion via new thermal coal assets and/or expanding existing thermal coal assets, as per: i) for thermal coal mining, increases in total tonnage of thermal coal extracted; ii) for coal to gas / liquid production, increases in total tonnage of thermal coal utilised; or iii) for power, increases in net operational thermal coal power capacity, in each case where such expansion
=== DOC: Thermal Coal Phase-out Policy (Feb 2025) | PAGE: 10 ===
-  was not already either: (a) contractually committed (via power purchase agreement for thermal coal-fired power generation); or (b) under construction, in each case before 01 January 2021; and -  does not include exempted activities. This includes expansion via corporate mergers and acquisition unless the client has confirmed phase-out of these assets will be line with HSBC's 2030/40 timelines, and the transaction does not involve a global increase in tonnage or power capacity.
"""

ASSESSMENT_HSBC = {
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
			"exception_id": "CP.EX9",
			"applies": True,
			"description": "expansion via corporate mergers and acquisition.",
			"mitigated": True,
			"mitigant": "client has confirmed phase-out of these assets will be in line with HSBC's 2030/40 timelines."
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
            "exception_id": "CP.EX19",
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
            "exception_id": "CP.EX23",
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
    ],
    "references": [
        {
            "excerpt": "HSBC will not provide new finance, or new advisory services, for the specific purposes of activities that do not align with HSBC's Phase Out Commitment timelines as outlined below: -  creation of new thermal coal assets; -  thermal coal expansion; -  extensions to the unabated operating lifetime of existing thermal coal assets; -  new captive thermal coal-fired power plants or new captive thermal coal mines; -  conversion of existing coal-to-gas-fired power plants, unless a) the client demonstrates to HSBC its intention to achieve abated power generation and b) the plants do not operate in environmentally and socially critical areas; -  new thermal coal infrastructure; -  new metallurgical coal mines; or -  thermal coal assets or metallurgical coal mines operating in environmentally and socially critical areas or using Mountaintop Removal (including clients who derive more than 30% of their annual revenues from Mountaintop Removal coal mining).",
            "document_name": "Thermal Coal Phase-out Policy (Feb 2025)",
            "page_start": 4,
            "page_end": 4
        },
        {
            "excerpt": "exempted activities Means the following: -  existing captive thermal coal-fired power plants; -  existing captive thermal coal mines; -  coal services; -  underground coal gasification (coal bed methane); and -  all other activities of clients. For the avoidance of doubt, the Policy does apply to clients engaged in new captive thermal coal-fired power plants and new captive thermal coal mines. thermal coal assets new thermal coal assets thermal coal mines, thermal coal-fired power plants and coal to gas / liquids plants. new thermal coal assets means new thermal coal mines, new thermal coal-fired power plants and new coal to gas / liquids plants. The terms thermal coal assets and new thermal coal assets do not include exempted activities. thermal coal expansion Means expansion via new thermal coal assets and/or expanding existing thermal coal assets, as per: i) for thermal coal mining, increases in total tonnage of thermal coal extracted; ii) for coal to gas / liquid production, increases in total tonnage of thermal coal utilised; or iii) for power, increases in net operational thermal coal power capacity, in each case where such expansion -  was not already either: (a) contractually committed (via power purchase agreement for thermal coal-fired power generation); or (b) under construction, in each case before 01 January 2021; and -  does not include exempted activities. This includes expansion via corporate mergers and acquisition unless the client has confirmed phase-out of these assets will be line with HSBC's 2030/40 timelines, and the transaction does not involve a global increase in tonnage or power capacity.",
            "document_name": "Thermal Coal Phase-out Policy (Feb 2025)",
            "page_start": 8,
            "page_end": 10
        }
    ]
}

### BBVA ###

POLICY_EXTRACT_BBVA = """
BBVA will not finance new projects for the construction of new thermal coal-fired power plants, including new self-consumption plants, or for the expansion of an existing thermal coal-fired power plant (regardless of the type of client).
"""

POLICY_PAGES_BBVA = """
=== DOC: Environmental and Social Framework (Dec 2024) | PAGE: 8 ===
BBVA will not finance new projects for the construction of new thermal coal-fired power plants, including new self-consumption plants, or for the expansion of an existing thermal coal-fired power plant (regardless of the type of client).
"""

ASSESSMENT_BBVA = {
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
			"exception_id": "CP.EX9",
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
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
        {
            "exception_id": "CP.EX15",
			"applies": False,
			"description": None,
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
            "exception_id": "CP.EX19",
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
            "exception_id": "CP.EX23",
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
    ],
    "references": [
        {
            "excerpt": "BBVA will not finance new projects for the construction of new thermal coal-fired power plants, including new self-consumption plants, or for the expansion of an existing thermal coal-fired power plant (regardless of the type of client).",
            "document_name": "Environmental and Social Framework (Dec 2024)",
            "page_start": 8,
            "page_end": 8
        }
	]
}

### BARCLAYS ###

POLICY_EXTRACT_BARCLAYS = """
No project finance to enable the construction or material expansion of thermal coal-fired power plants anywhere in the world, including captives.

Material expansion: In relation to Thermal Coal Power, production refers to an investment to (i) extend the unabated operating lifetime of existing thermal coal power plants including captives or (ii) increase net operational thermal power capacity, including captives, by more than 10% measure from a baseline of maximum capacity for preceding 3 years reported.
"""

POLICY_PAGES_BARCLAYS = """
=== DOC: Climate change statement (Feb 2024) | PAGE: 6 ===
No project finance to enable the construction or material expansion of thermal coal-fired power plants anywhere in the world, including captives.
=== DOC: Climate change statement (Feb 2024) | PAGE: 11 ===
Material expansion In relation to Thermal Coal Power, production refers to an investment to (i) extend the unabated operating lifetime of existing thermal coal power plants including captives or (ii) increase net operational thermal power capacity, including captives, by more than 10% measure from a baseline of maximum capacity for preceding 3 years reported. Material expansion in such cases relates to absolute global increases rather than increases for an entity or Group as a result of mergers or acquisitions. 
"""

ASSESSMENT_BARCLAYS = {
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
			"exception_id": "CP.EX9",
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
			"applies": False,
			"description": None,
			"mitigated": False,
			"mitigant": None
		},
        {
            "exception_id": "CP.EX15",
			"applies": False,
			"description": None,
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
            "exception_id": "CP.EX19",
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
            "exception_id": "CP.EX23",
			"applies": True,
			"description": "expansion that doesn't increase production by more than 10%.",
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
    ],
    "references": [
		{
			"excerpt": "No project finance to enable the construction or material expansion of thermal coal-fired power plants anywhere in the world, including captives.",
			"document_name": "Climate change statement (Feb 2024)",
			"page_start": 6,
			"page_end": 6
		},
		{
			"excerpt": "Material expansion In relation to Thermal Coal Power, production refers to an investment to (i) extend the unabated operating lifetime of existing thermal coal power plants including captives or (ii) increase net operational thermal power capacity, including captives, by more than 10% measure from a baseline of maximum capacity for preceding 3 years reported.",
			"document_name": "Climate change statement (Feb 2024)",
			"page_start": 11,
			"page_end": 11
		}
	]
}