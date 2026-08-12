import re
from dataclasses import dataclass, asdict
from typing import Optional, Tuple


# ============================================================
# Known values
# ============================================================

KNOWN_METRICS = {
    # SBL metrics
    "SBL_SPI_INIT", "SBL_FCONFIG_LOAD", "SBL_CRYPTO_INIT",
    "SBL_CRITICAL_BOOT_LOAD", "SBL_UFH_LOAD_AND_VERIFY",
    "SBL_DIGEST_COMPUTE", "SBL_LOAD_TBL_IMAGE", "SBL_RIOT", "SBL_TOTAL",
    # TBL metrics
    "TBL_PRETOTAL", "TBL_SPI_INIT", "TBL_FCONFIG_LOAD", "TBL_PCIE_INIT",
    "TBL_LOAD_PBL_IMAGE", "TBL_RIOT", "TBL_TOTAL",
    # PBL metrics
    "PBL_SPI_INIT", "PBL_PARSE_FCONFIG", "PBL_PMIC_INIT", "PBL_DRAM_INIT",
    "PBL_SCRUB_MAINFW_DRAM", "PBL_CRYPTO_INIT", "PBL_NAND_INIT",
    "PBL_LOAD_MAIN_FW", "PBL_RIOT", "PBL_WAKE_CORES_JUMP", "PBL_TOTAL",
    # BOOTLOADERS
    "BOOTLOADERS_TOTAL",
    # MAINFW metrics
    "MAINFW_BSS_INIT", "MAINFW_PCM_BSS_INIT", "MAINFW_SPI_SEC_INIT",
    "MAINFW_ENABLE_ADDR_PARITY_CHECKING", "MAINFW_UART_INIT",
    "MAINFW_GPIO_INIT_LOCKS", "MAINFW_GPIO_INIT_DCSU", "MAINFW_BL_SPINLOCK_SETUP",
    "MAINFW_LLOG_INIT", "MAINFW_MGR_REG_INIT", "MAINFW_MEM_PRINT_INIT",
    "MAINFW_PRE_PMU_INIT", "MAINFW_GIC_LOCK_INIT", "MAINFW_APP_TIMER_LOCK_INIT",
    "MAINFW_ULOG_INIT", "MAINFW_PMU_INIT", "MAINFW_SMBUS_INIT",
    "MAINFW_INT_INIT", "MAINFW_RNG_INIT", "MAINFW_KERNEL_INIT_EARLY",
    "MAINFW_PS_INIT_0", "MAINFW_PS_INIT_1", "MAINFW_PS_INIT_2",
    "MAINFW_DRAM_SCRUB_WAIT", "MAINFW_DRAM_SCRUB_3",
    "MAINFW_DRIVER_SUB_INIT", "MAINFW_TASK_CREATE",
    "MAINFW_SAVE_AND_CLEAR_BRAM", "MAINFW_CORESIGHT_INIT",
    # Totals
    "OVERALL_TOTAL",
    # Short aliases kept for backward compatibility
    "PBL", "SBL", "TBL", "OVERALL",
}

KNOWN_BOOT_TYPES = {
    "EB0",
    "SPI",
}

METRIC_ALIASES = {
    "bootloaders total": "BOOTLOADERS_TOTAL",
    "overall total": "OVERALL_TOTAL",
    "overall time": "OVERALL_TOTAL",
    "boot time": "OVERALL_TOTAL",
    "pbl total": "PBL_TOTAL",
    "sbl total": "SBL_TOTAL",
    "tbl total": "TBL_TOTAL",
    "bootloaders": "BOOTLOADERS_TOTAL",
    "overall": "OVERALL",
    "pbl": "PBL",
    "sbl": "SBL",
    "tbl": "TBL",
}

MAX_LIMIT = 500
DEFAULT_LIMIT = 100


# ============================================================
# Query model
# ============================================================

@dataclass
class Query:
    question: str
    operation: str = "list"
    metric: Optional[str] = None
    hostname: Optional[str] = None
    sku: Optional[str] = None
    bootType: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    group_by: Optional[str] = None
    limit: int = DEFAULT_LIMIT
    # "min" or "max" — which timing field to sort/aggregate on
    value_field: Optional[str] = None

    def to_dict(self):
        return asdict(self)


# ============================================================
# Cleaning
# ============================================================

def clean_question(question: str) -> str:
    if not isinstance(question, str):
        return ""

    return " ".join(question.strip().split())


def normalize_text(question: str) -> str:
    return clean_question(question).lower()


# ============================================================
# Extraction helpers
# ============================================================

def extract_hostname(question: str) -> Optional[str]:
    patterns = [
        r"\b(?:rc|lm)-\d+-\d+-\d+-s\d+\b",
        r"\b[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)+-s\d+\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            return match.group(0)

    return None


def extract_sku(question: str) -> Optional[str]:
    match = re.search(
        r"\b\d+(?:TB|GB|PB)\b",
        question,
        re.IGNORECASE,
    )

    if match:
        return match.group(0).upper()

    return None


def extract_boot_type(question: str) -> Optional[str]:
    upper = question.upper()

    for boot_type in KNOWN_BOOT_TYPES:
        if re.search(r"\b" + re.escape(boot_type) + r"\b", upper):
            return boot_type

    return None


def extract_metric(question: str) -> Optional[str]:
    upper = question.upper()
    normalized = normalize_text(question)

    for phrase, metric in sorted(
        METRIC_ALIASES.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if re.search(r"\b" + re.escape(phrase) + r"\b", normalized):
            return metric

    for metric in sorted(KNOWN_METRICS, key=len, reverse=True):
        if re.search(r"\b" + re.escape(metric) + r"\b", upper):
            return metric

    match = re.search(
        r"\b[A-Z][A-Z0-9_]*_[A-Z0-9_]+\b",
        upper,
    )

    if match:
        return match.group(0)

    return None


def extract_dates(question: str) -> Tuple[Optional[str], Optional[str]]:
    dates = [
        value.replace("/", "-")
        for value in re.findall(
            r"\b\d{4}[-/]\d{2}[-/]\d{2}\b",
            question,
        )
    ]

    if len(dates) >= 2:
        return dates[0], dates[1]

    if len(dates) == 1:
        return dates[0], dates[0]

    return None, None


def extract_limit(question: str) -> int:
    patterns = [
        r"\btop\s+(\d{1,4})\b",
        r"\bfirst\s+(\d{1,4})\b",
        r"\blatest\s+(\d{1,4})\b",
        r"\blast\s+(\d{1,4})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            value = int(match.group(1))
            return max(1, min(value, MAX_LIMIT))

    return DEFAULT_LIMIT


def extract_group_by(question: str) -> Optional[str]:
    lower = normalize_text(question)

    if " by host" in lower or " by hostname" in lower:
        return "hostname"

    if " by sku" in lower:
        return "sku"

    if " by boot" in lower or " by boot type" in lower:
        return "bootType"

    if " by date" in lower or " trend" in lower:
        return "date"

    return None


def infer_metric(question: str, operation: str, metric: Optional[str]) -> Optional[str]:
    if metric:
        return metric

    lower = normalize_text(question)

    if operation in {"highest", "lowest", "average", "chart"}:
        if _contains_word(lower, ["time", "fastest", "slowest"]):
            return "OVERALL_TOTAL"

    return metric


# ============================================================
# Operation detection
# ============================================================

def _contains_word(text: str, words) -> bool:
    for word in words:
        if re.search(r"\b" + re.escape(word) + r"\b", text):
            return True

    return False


def _contains_phrase(text: str, phrases) -> bool:
    for phrase in phrases:
        if phrase in text:
            return True

    return False


def detect_operation(question: str, metric: Optional[str]) -> str:
    q = normalize_text(question)

    # fastest/slowest → explicit value_field semantics handled in parse_question
    if _contains_word(q, ["fastest", "best"]):
        return "lowest"

    if _contains_word(q, ["slowest", "worst"]):
        return "highest"

    if _contains_word(q, ["lowest", "minimum", "min", "smallest"]):
        return "lowest"

    if _contains_word(
        q,
        ["highest", "maximum", "max", "largest"],
    ):
        return "highest"

    if _contains_word(q, ["average", "avg", "mean"]):
        return "average"

    if _contains_word(q, ["count"]) or _contains_phrase(
        q,
        ["how many", "number of"],
    ):
        return "count"

    if _contains_word(q, ["plot", "graph", "chart", "trend"]):
        return "chart"

    if metric:
        return "metric"

    if _contains_word(q, ["list", "show", "display", "give", "which"]):
        return "list"

    return "list"


def _detect_value_field(question: str, operation: str) -> Optional[str]:
    """Determine which timing column to sort/aggregate on."""
    q = normalize_text(question)

    # fastest/slowest → use max (worst-case time = representative performance)
    if _contains_word(q, ["fastest", "best", "slowest", "worst"]):
        return "max"

    # explicit minimum/lowest → use min column
    if _contains_word(q, ["minimum", "min", "lowest", "smallest"]) and operation == "lowest":
        return "min"

    # default: use max for extreme/average operations
    if operation in {"highest", "lowest", "average"}:
        return "max"

    return None


# ============================================================
# Main parser
# ============================================================

def parse_question(question: str) -> Query:
    question = clean_question(question)

    metric = extract_metric(question)
    hostname = extract_hostname(question)
    sku = extract_sku(question)
    boot_type = extract_boot_type(question)
    date_from, date_to = extract_dates(question)
    limit = extract_limit(question)
    group_by = extract_group_by(question)

    operation = detect_operation(question, metric)
    metric = infer_metric(question, operation, metric)
    value_field = _detect_value_field(question, operation)

    return Query(
        question=question,
        operation=operation,
        metric=metric,
        hostname=hostname,
        sku=sku,
        bootType=boot_type,
        date_from=date_from,
        date_to=date_to,
        group_by=group_by,
        limit=limit,
        value_field=value_field,
    )


# ============================================================
# Compatibility helpers
# ============================================================

def is_deterministic_query(question):
    if isinstance(question, Query):
        return True

    if not isinstance(question, str):
        return False

    q = parse_question(question)

    return q.operation in {
        "list",
        "metric",
        "lowest",
        "highest",
        "average",
        "count",
        "chart",
    }


DASHBOARD_KEYWORDS = {
    # top-level document fields
    "host", "hostname", "filename", "date", "sku", "records",
    "boottype", "boot", "spi", "eb0", "spiflow", "eb0flow",
    # metric prefixes / aliases
    "metric", "metrics",
    "sbl", "pbl", "tbl", "overall", "mainfw",
    "bootloaders", "performance",
    # operations
    "fastest", "slowest", "highest", "lowest", "average",
    "trend", "plot", "graph", "chart", "compare", "count",
}

# Matches UPPER_CASE_WITH_UNDERSCORES metric names.
_METRIC_PATTERN = re.compile(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b")
# Matches SKU values like 60TB, 30TB, 16GB.
_SKU_PATTERN = re.compile(r"\b\d+(?:TB|GB|PB)\b", re.IGNORECASE)
# Matches YYYY-MM-DD or YYYY/MM/DD dates.
_DATE_PATTERN = re.compile(r"\b\d{4}[-/]\d{2}[-/]\d{2}\b")


def is_dashboard_question(question: str) -> bool:
    """Return True when the question is likely about dashboard data."""
    if _METRIC_PATTERN.search(question):
        return True
    if _SKU_PATTERN.search(question):
        return True
    if _DATE_PATTERN.search(question):
        return True
    lower = normalize_text(question)
    return any(
        re.search(r"\b" + re.escape(kw) + r"\b", lower)
        for kw in DASHBOARD_KEYWORDS
    )

def is_simple_dashboard_question(question: str) -> bool:
    """
    Decide whether the existing deterministic parser is
    reliable enough to handle the question.

    Simple questions use regex parsing.

    More natural-language questions are sent to Ollama.
    """

    if not isinstance(question, str):
        return False

    q = normalize_text(question)

    # Explicit complex language.
    complex_phrases = [
        "which host",
        "which hosts",
        "what host",
        "what hosts",
        "tell me",
        "compare",
        "compared with",
        "compared to",
        "relative to",
        "among",
        "across",
        "for each",
        "per host",
        "per sku",
        "per boot",
        "between",
        "during",
        "last month",
        "this month",
        "last week",
        "this week",
        "previous month",
        "recent",
    ]

    if any(
        phrase in q
        for phrase in complex_phrases
    ):
        return False

    # Existing parser is reliable for explicit metric names.
    if _METRIC_PATTERN.search(question):
        return True

    # Explicit hostname + any filter.
    if extract_hostname(question):
        if (
            extract_metric(question)
            or extract_boot_type(question)
            or extract_sku(question)
            or extract_dates(question)[0]
        ):
            return True

    # Any extractable filter with a simple action verb → deterministic.
    _date_from, _ = extract_dates(question)
    simple_words = ["list", "show", "display", "give", "get", "all"]

    if (
        any(
            re.search(r"\b" + re.escape(word) + r"\b", q)
            for word in simple_words
        )
        and (
            extract_metric(question)
            or extract_hostname(question)
            or extract_boot_type(question)
            or extract_sku(question)
            or _date_from
        )
    ):
        return True

    # Date-only question: "show SBL on 2026-07-31"
    if _date_from and (extract_metric(question) or extract_boot_type(question) or extract_sku(question)):
        return True

    return False

