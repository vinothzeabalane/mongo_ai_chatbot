import re
from dataclasses import dataclass, asdict
from typing import Optional, Tuple


# ============================================================
# Known values
# ============================================================

KNOWN_METRICS = {
    "SBL_TOTAL",
    "OVERALL_TOTAL",
    "SBL",
    "OVERALL",
}

KNOWN_BOOT_TYPES = {
    "EB0",
    "SPI",
}

METRIC_ALIASES = {
    "overall total": "OVERALL_TOTAL",
    "overall time": "OVERALL_TOTAL",
    "boot time": "OVERALL_TOTAL",
    "sbl total": "SBL_TOTAL",
    "overall": "OVERALL",
    "sbl": "SBL",
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
