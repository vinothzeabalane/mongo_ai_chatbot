from utils import seconds_to_timing


def format_number(value):

    if value is None:

        return "N/A"

    return "{:.6f}".format(
        value
    )


def format_hosts(result):

    records = result.get(
        "records",
        []
    )

    if not records:

        return "No hosts found."

    lines = []

    lines.append(
        "**Unique hosts:** {}".format(
            len(records)
        )
    )

    lines.append("")

    lines.append(
        "| Hostname | SKU | Boot Type |"
    )

    lines.append(
        "|---|---|---|"
    )

    for record in records:

        lines.append(
            "| {} | {} | {} |".format(
                record.get(
                    "hostname",
                    ""
                ),
                record.get(
                    "sku",
                    ""
                ),
                record.get(
                    "bootType",
                    ""
                )
            )
        )

    return "\n".join(lines)


def format_records(
    records
):

    if not records:

        return "No matching records found."

    lines = []

    lines.append(
        "| Date | Hostname | Boot Type | Metric | Min | Max |"
    )

    lines.append(
        "|---|---|---|---|---|---|"
    )

    for record in records:

        lines.append(
            "| {} | {} | {} | {} | {} | {} |".format(

                record.get(
                    "date",
                    ""
                ),

                record.get(
                    "hostname",
                    ""
                ),

                record.get(
                    "bootType",
                    ""
                ),

                record.get(
                    "metric",
                    ""
                ),

                record.get(
                    "min",
                    ""
                ),

                record.get(
                    "max",
                    ""
                )
            )
        )

    return "\n".join(lines)


def format_analysis(
    analysis
):

    analysis_type = analysis.get(
        "type"
    )


    # ========================================================
    # Average
    # ========================================================

    if analysis_type == "average":

        value = analysis.get(
            "value"
        )

        if value is None:

            return "No numeric data found."

        return (
            "**Average OVERALL metric:** `{}` seconds"
            .format(
                format_number(value)
            )
        )


    # ========================================================
    # Highest
    # ========================================================

    if analysis_type == "highest":

        result = analysis.get(
            "result"
        )

        if not result:

            return "No numeric data found."

        return (
            "**Highest:** `{}`\n\n"
            "- Host: `{}`\n"
            "- SKU: `{}`\n"
            "- Boot type: `{}`\n"
            "- Date: `{}`\n"
            "- Max: `{}`\n"
            "- Max seconds: `{}`"
        ).format(

            result.get(
                "metric",
                "OVERALL_TOTAL"
            ),

            result.get(
                "hostname"
            ),

            result.get(
                "sku"
            ),

            result.get(
                "bootType"
            ),

            result.get(
                "date"
            ),

            result.get(
                "max"
            ),

            format_number(
                result.get(
                    "max_seconds"
                )
            )
        )


    # ========================================================
    # Lowest
    # ========================================================

    if analysis_type == "lowest":

        result = analysis.get(
            "result"
        )

        if not result:

            return "No numeric data found."

        return (
            "**Lowest:** `{}`\n\n"
            "- Host: `{}`\n"
            "- SKU: `{}`\n"
            "- Boot type: `{}`\n"
            "- Date: `{}`\n"
            "- Max: `{}`\n"
            "- Max seconds: `{}`"
        ).format(

            result.get(
                "metric",
                "OVERALL_TOTAL"
            ),

            result.get(
                "hostname"
            ),

            result.get(
                "sku"
            ),

            result.get(
                "bootType"
            ),

            result.get(
                "date"
            ),

            result.get(
                "max"
            ),

            format_number(
                result.get(
                    "max_seconds"
                )
            )
        )


    # ========================================================
    # Comparison
    # ========================================================

    if analysis_type == "comparison":

        results = analysis.get(
            "results",
            []
        )

        if not results:

            return "No comparison data found."

        lines = []

        lines.append(
            "| Host | Average | Minimum | Maximum | Records |"
        )

        lines.append(
            "|---|---:|---:|---:|---:|"
        )

        for item in results:

            lines.append(
                "| {} | {:.6f} | {:.6f} | {:.6f} | {} |".format(

                    item["hostname"],

                    item["average"],

                    item["minimum"],

                    item["maximum"],

                    item["count"]
                )
            )

        return "\n".join(lines)


    # ========================================================
    # Percentage
    # ========================================================

    if analysis_type == "percentage_change":

        value = analysis.get(
            "value"
        )

        if value is None:

            return "Not enough data to calculate percentage change."

        return (
            "**Change:** `{:.2f}%`"
            .format(
                value
            )
        )


    return "No analysis result."


def format_result(
    operation,
    result,
    analysis=None
):

    if operation == "list_hosts":

        return format_hosts(
            result
        )

    if analysis is not None:

        return format_analysis(
            analysis
        )

    return format_records(
        result.get(
            "records",
            []
        )
    )