import re


KNOWN_METRICS = [
    "OVERALL_TOTAL",

    "BOOTLOADERS_TOTAL",

    "SBL_TOTAL",
    "PBL_TOTAL",
    "TBL_TOTAL",

    "SBL_SPI_INIT",
    "SBL_FCONFIG_LOAD",
    "SBL_CRYPTO_INIT",
    "SBL_CRITICAL_BOOT_LOAD",
    "SBL_UFH_LOAD_AND_VERIFY",
    "SBL_DIGEST_COMPUTE",
    "SBL_LOAD_TBL_IMAGE",
    "SBL_RIOT",

    "TBL_PRETOTAL",
    "TBL_SPI_INIT",
    "TBL_FCONFIG_LOAD",
    "TBL_PCIE_INIT",
    "TBL_LOAD_PBL_IMAGE",
    "TBL_RIOT",

    "PBL_SPI_INIT",
    "PBL_PARSE_FCONFIG",
    "PBL_PMIC_INIT",
    "PBL_DRAM_INIT",
    "PBL_SCRUB_MAINFW_DRAM",
    "PBL_CRYPTO_INIT",
    "PBL_NAND_INIT",
    "PBL_LOAD_MAIN_FW",
    "PBL_RIOT",
    "PBL_WAKE_CORES_JUMP",

    "MAINFW_BSS_INIT",
    "MAINFW_PCM_BSS_INIT",
    "MAINFW_SPI_SEC_INIT",
]


# ============================================================
# Host
# ============================================================

def extract_hostname(question):

    patterns = [

        r"\b(rc\d{3}-\d{3}-\d{2}-s\d+)\b",

        r"\b(lm-\d{3}-\d{2}-s\d+)\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            question,
            re.IGNORECASE
        )

        if match:

            return match.group(1)

    return None


# ============================================================
# Boot type
# ============================================================

def extract_boot_type(question):

    match = re.search(
        r"\b(SPI|EB0)\b",
        question,
        re.IGNORECASE
    )

    if match:

        return match.group(1).upper()

    return None


# ============================================================
# SKU
# ============================================================

def extract_sku(question):

    match = re.search(
        r"\b(\d+(?:\.\d+)?TB)\b",
        question,
        re.IGNORECASE
    )

    if match:

        return match.group(1).upper()

    return None


# ============================================================
# Metric
# ============================================================

def extract_metric(question):

    upper = question.upper()

    # Exact known metrics first.

    for metric in sorted(
        KNOWN_METRICS,
        key=len,
        reverse=True
    ):

        if metric in upper:

            return metric

    # Natural language mappings.

    mappings = {

        "overall total":
            "OVERALL_TOTAL",

        "overall time":
            "OVERALL_TOTAL",

        "overall boot time":
            "OVERALL_TOTAL",

        "total boot time":
            "OVERALL_TOTAL",

        "bootloader total":
            "BOOTLOADERS_TOTAL",

        "bootloaders total":
            "BOOTLOADERS_TOTAL",

        "sbl total":
            "SBL_TOTAL",

        "pbl total":
            "PBL_TOTAL",

        "tbl total":
            "TBL_TOTAL",
    }

    lower = question.lower()

    for phrase, metric in mappings.items():

        if phrase in lower:

            return metric

    return None


# ============================================================
# Dates
# ============================================================

def extract_dates(question):

    dates = re.findall(
        r"\b\d{4}-\d{2}-\d{2}\b",
        question
    )

    if len(dates) >= 2:

        return dates[0], dates[1]

    if len(dates) == 1:

        return dates[0], dates[0]

    return None, None


# ============================================================
# Operation
# ============================================================

def detect_operation(question):

    q = question.lower().strip()

    # --------------------------------------------------------
    # Average
    # --------------------------------------------------------

    if any(
        word in q
        for word in [
            "average",
            "avg",
            "mean"
        ]
    ):

        return "average"


    # --------------------------------------------------------
    # Comparison
    # --------------------------------------------------------

    if any(
        word in q
        for word in [
            "compare",
            "comparison",
            "versus",
            "vs"
        ]
    ):

        return "compare"


    # --------------------------------------------------------
    # Highest
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "highest",
            "maximum",
            "max",
            "slowest",
            "higher",
            "largest",
            "worst",
            "which host",
        ]
    ):

        # Important:
        # "which host the overall time is higher"
        # should become highest.

        if (
            "which host" in q
            or "which hosts" in q
            or "host" in q
        ):

            return "highest"

        if "highest" in q:
            return "highest"

        if "maximum" in q:
            return "highest"

        if "slowest" in q:
            return "highest"


    # --------------------------------------------------------
    # Lowest
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "lowest",
            "minimum",
            "min",
            "fastest",
            "lower",
            "smallest",
            "best",
        ]
    ):

        return "lowest"


    # --------------------------------------------------------
    # Percentage / change
    # --------------------------------------------------------

    if any(
        word in q
        for word in [
            "percentage",
            "percent",
            "change",
            "increase",
            "decrease",
            "improved",
            "degraded",
            "trend",
        ]
    ):

        return "change"


    # --------------------------------------------------------
    # Unique hosts
    # --------------------------------------------------------

    if (
        "host" in q
        and any(
            word in q
            for word in [
                "list",
                "show",
                "unique",
                "all",
                "which",
                "what",
            ]
        )
        and extract_metric(question) is None
    ):

        return "list_hosts"


    # --------------------------------------------------------
    # Show / history
    # --------------------------------------------------------

    if any(
        word in q
        for word in [
            "show",
            "display",
            "give",
            "get",
            "history",
            "details",
        ]
    ):

        return "show"


    # Default.

    if extract_metric(question):

        return "show"

    return "unknown"


# ============================================================
# Complete parser
# ============================================================

def parse_question(question):

    date_from, date_to = extract_dates(
        question
    )

    result = {

        "question": question,

        "operation":
            detect_operation(question),

        "hostname":
            extract_hostname(question),

        "bootType":
            extract_boot_type(question),

        "sku":
            extract_sku(question),

        "metric":
            extract_metric(question),

        "date_from":
            date_from,

        "date_to":
            date_to,
    }

    return result