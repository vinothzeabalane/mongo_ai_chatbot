
from core.parser import (
    Query,
    KNOWN_METRICS,
    KNOWN_BOOT_TYPES,
    DEFAULT_LIMIT,
    MAX_LIMIT,
)


VALID_OPERATIONS = {
    "list",
    "metric",
    "lowest",
    "highest",
    "average",
    "count",
    "chart",
}


def _clean(value):
    if value is None:
        return None

    if not isinstance(value, str):
        return None

    value = value.strip()

    if not value:
        return None

    return value


def validate_llm_query(data, original_question):
    """
    Convert LLM JSON into our trusted Query object.

    The LLM is never allowed to create MongoDB syntax.
    """

    if not isinstance(data, dict):
        raise ValueError(
            "LLM query must be a JSON object."
        )

    operation = _clean(
        data.get("operation")
    )

    if operation not in VALID_OPERATIONS:
        operation = "list"

    metric = _clean(
        data.get("metric")
    )

    if metric:
        metric = metric.upper()

        if metric not in KNOWN_METRICS:
            raise ValueError(
                f"Unknown metric from LLM: {metric}"
            )

    hostname = _clean(
        data.get("hostname")
    )

    sku = _clean(
        data.get("sku")
    )

    boot_type = _clean(
        data.get("bootType")
    )

    if boot_type:
        boot_type = boot_type.upper()

        # LLM sometimes returns combined values like "EB0,SPI" — discard them.
        if boot_type not in KNOWN_BOOT_TYPES:
            boot_type = None

    date_from = _clean(
        data.get("date_from")
    )

    date_to = _clean(
        data.get("date_to")
    )

    group_by = _clean(
        data.get("group_by")
    )

    if group_by not in {
        None,
        "hostname",
        "sku",
        "bootType",
        "date",
    }:
        group_by = None

    # Infer group_by from the original question when the LLM missed it.
    q_lower = original_question.lower()
    if group_by is None:
        if "each boot type" in q_lower or "by boot type" in q_lower or "per boot" in q_lower:
            group_by = "bootType"
        elif "each host" in q_lower or "by host" in q_lower or "per host" in q_lower:
            group_by = "hostname"
        elif "each sku" in q_lower or "by sku" in q_lower:
            group_by = "sku"

    limit = data.get(
        "limit",
        DEFAULT_LIMIT,
    )

    try:
        limit = int(limit)
    except (
        TypeError,
        ValueError,
    ):
        limit = DEFAULT_LIMIT

    limit = max(
        1,
        min(limit, MAX_LIMIT),
    )

    return Query(
        question=original_question,
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

