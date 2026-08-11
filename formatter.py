FRIENDLY_LABELS = {
    "hostname": "Host",
    "sku": "SKU",
    "bootType": "Boot Type",
    "date": "Date",
    "metric": "Metric",
    "min": "Minimum",
    "max": "Maximum",
    "min_seconds": "Min (seconds)",
    "max_seconds": "Max (seconds)",
    "average_seconds": "Average (seconds)",
    "count": "Count",
}

FRIENDLY_METRICS = {
    "SBL_TOTAL": "SBL Total",
    "OVERALL_TOTAL": "Overall Total",
    "SBL": "SBL",
    "OVERALL": "Overall",
}


def prettify_metric(metric):
    if not metric:
        return ""

    if metric in FRIENDLY_METRICS:
        return FRIENDLY_METRICS[metric]

    return str(metric).replace("_", " ").title()


def format_seconds(value):
    if value is None:
        return ""

    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return str(value)


def format_record(record):
    lines = []

    hostname = record.get("hostname")
    sku = record.get("sku")
    boot_type = record.get("bootType")
    date = record.get("date")
    metric = record.get("metric")

    if hostname:
        lines.append(f"**Host:** `{hostname}`")

    if sku:
        lines.append(f"**SKU:** `{sku}`")

    if boot_type:
        lines.append(
            f"**Boot type:** `{boot_type}`"
        )

    if date:
        lines.append(f"**Date:** `{date}`")

    if metric:
        lines.append(
            f"**Metric:** `{prettify_metric(metric)}`"
        )

    if record.get("min") is not None:
        lines.append(
            f"**Min:** `{record['min']}`"
        )

    if record.get("max") is not None:
        lines.append(
            f"**Max:** `{record['max']}`"
        )

    if record.get("min_seconds") is not None:
        lines.append(
            "**Min seconds:** "
            f"`{format_seconds(record['min_seconds'])}`"
        )

    if record.get("max_seconds") is not None:
        lines.append(
            "**Max seconds:** "
            f"`{format_seconds(record['max_seconds'])}`"
        )

    return "\n\n".join(lines)


def format_result(result):

    records = result.get("records", [])

    if not records:
        return "No matching records found."

    operation = result["query"].get(
        "operation"
    )

    if operation == "lowest":
        title = "### Lowest"
    elif operation == "highest":
        title = "### Highest"
    elif operation == "average":
        title = "### Average"
    else:
        title = "### Results"

    output = [title]

    for record in records:
        output.append(
            format_record(record)
        )

    return "\n\n".join(output)


def format_query_context(query, record_count):
    parts = [f"Rows: {record_count}"]

    if query.get("metric"):
        parts.append(
            f"Metric: {prettify_metric(query['metric'])}"
        )

    if query.get("hostname"):
        parts.append(
            f"Host: {query['hostname']}"
        )

    if query.get("bootType"):
        parts.append(
            f"Boot Type: {query['bootType']}"
        )

    if query.get("sku"):
        parts.append(
            f"SKU: {query['sku']}"
        )

    if query.get("date_from") and query.get("date_to"):
        if query["date_from"] == query["date_to"]:
            parts.append(
                f"Date: {query['date_from']}"
            )
        else:
            parts.append(
                "Date Range: "
                f"{query['date_from']} to {query['date_to']}"
            )

    return " | ".join(parts)


def records_to_rows(records):
    rows = []

    for record in records:
        row = {}

        for key in [
            "hostname",
            "sku",
            "bootType",
            "date",
            "metric",
            "min",
            "max",
            "min_seconds",
            "max_seconds",
            "average_seconds",
            "count",
        ]:
            value = record.get(key)

            if value is None:
                continue

            label = FRIENDLY_LABELS[key]

            if key == "metric":
                row[label] = prettify_metric(value)
            elif key in {"min_seconds", "max_seconds", "average_seconds"}:
                row[label] = format_seconds(value)
            else:
                row[label] = value

        if row:
            rows.append(row)

    return rows


def summarize_result(result):
    query = result.get("query", {})
    operation = query.get("operation", "list")
    records = result.get("records", [])
    record_count = result.get("record_count", 0)

    if not records:
        return "No matching records were found for this question."

    if operation == "count":
        count_value = records[0].get("count", 0)
        return f"I found {count_value} matching records."

    if operation == "average":
        value = records[0].get("average_seconds")

        if value is None:
            return "Unable to compute an average for the selected filters."

        return (
            "The average is "
            f"{format_seconds(value)} seconds."
        )

    if operation in {"lowest", "highest"}:
        record = records[0]
        host = record.get("hostname", "unknown host")
        metric = record.get("metric", query.get("metric") or "metric")
        field = "min_seconds" if operation == "lowest" else "max_seconds"
        value = record.get(field)
        label = "Lowest" if operation == "lowest" else "Highest"

        if value is None:
            return f"{label} {prettify_metric(metric)} found for {host}."

        return (
            f"{label} {prettify_metric(metric)} is {format_seconds(value)} seconds "
            f"on {host}."
        )

    if operation == "metric" and query.get("metric"):
        metric = query.get("metric")
        return f"Showing {record_count} result(s) for {prettify_metric(metric)}."

    return f"Showing {record_count} matching result(s)."