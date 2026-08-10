def average(records):

    values = [
        r["max_seconds"]
        for r in records
        if r.get("max_seconds") is not None
    ]

    if not values:

        return None

    return sum(values) / len(values)


def highest(records):

    valid = [
        r
        for r in records
        if r.get("max_seconds") is not None
    ]

    if not valid:

        return None

    return max(
        valid,
        key=lambda r:
            r["max_seconds"]
    )


def lowest(records):

    valid = [
        r
        for r in records
        if r.get("max_seconds") is not None
    ]

    if not valid:

        return None

    return min(
        valid,
        key=lambda r:
            r["max_seconds"]
    )


def compare(records):

    grouped = {}

    for record in records:

        host = record.get(
            "hostname"
        )

        value = record.get(
            "max_seconds"
        )

        if host is None:
            continue

        if value is None:
            continue

        grouped.setdefault(
            host,
            []
        ).append(value)

    result = []

    for hostname, values in grouped.items():

        result.append({

            "hostname":
                hostname,

            "average":
                sum(values) / len(values),

            "minimum":
                min(values),

            "maximum":
                max(values),

            "count":
                len(values),
        })

    result.sort(
        key=lambda x:
            x["average"],
        reverse=True
    )

    return result


def percentage_change(
    records
):

    valid = [
        r
        for r in records
        if r.get(
            "max_seconds"
        ) is not None
    ]

    valid.sort(
        key=lambda r:
            r.get("date") or ""
    )

    if len(valid) < 2:

        return None

    first = valid[0]["max_seconds"]

    latest = valid[-1]["max_seconds"]

    if first == 0:

        return None

    return (
        (latest - first)
        / first
    ) * 100.0


def analyze(
    operation,
    records
):

    if operation == "average":

        return {
            "type":
                "average",

            "value":
                average(records)
        }


    if operation == "highest":

        return {
            "type":
                "highest",

            "result":
                highest(records)
        }


    if operation == "lowest":

        return {
            "type":
                "lowest",

            "result":
                lowest(records)
        }


    if operation == "compare":

        return {
            "type":
                "comparison",

            "results":
                compare(records)
        }


    if operation == "change":

        return {
            "type":
                "percentage_change",

            "value":
                percentage_change(
                    records
                )
        }


    return {
        "type":
            "records",

        "records":
            records
    }