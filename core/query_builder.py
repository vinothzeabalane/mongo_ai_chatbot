from core.parser import Query


# ============================================================
# Build MongoDB match filter
# ============================================================

def build_match(query: Query):
    match = {}

    if query.hostname:
        match["hostname"] = query.hostname

    if query.sku:
        match["sku"] = query.sku

    if query.bootType:
        match["bootType"] = query.bootType

    if query.metric:
        match[f"data.{query.metric}"] = {
            "$exists": True
        }

    if query.date_from and query.date_to:
        match["date"] = {
            "$gte": query.date_from,
            "$lte": query.date_to,
        }

    elif query.date_from:
        match["date"] = {
            "$gte": query.date_from,
        }

    elif query.date_to:
        match["date"] = {
            "$lte": query.date_to,
        }

    return match


def _metric_field_path(query: Query, field_name: str):
    if not query.metric:
        return None

    return f"$data.{query.metric}.{field_name}"


def _timing_to_seconds_expr(field_path):
    parts = {
        "$split": [
            {
                "$ifNull": [field_path, ""]
            },
            ".",
        ]
    }

    return {
        "$cond": [
            {
                "$eq": [
                    {
                        "$size": parts
                    },
                    3,
                ]
            },
            {
                "$add": [
                    {
                        "$toDouble": {
                            "$arrayElemAt": [parts, 0]
                        }
                    },
                    {
                        "$divide": [
                            {
                                "$toDouble": {
                                    "$arrayElemAt": [parts, 1]
                                }
                            },
                            1000,
                        ]
                    },
                    {
                        "$divide": [
                            {
                                "$toDouble": {
                                    "$arrayElemAt": [parts, 2]
                                }
                            },
                            1000000,
                        ]
                    },
                ]
            },
            None,
        ]
    }


def _metric_projection(query: Query):
    min_path = _metric_field_path(query, "min")
    max_path = _metric_field_path(query, "max")

    projection = {
        "_id": 0,
        "hostname": 1,
        "sku": 1,
        "bootType": 1,
        "date": 1,
    }

    if query.metric:
        projection.update(
            {
                "metric": {
                    "$literal": query.metric
                },
                "min": min_path,
                "max": max_path,
                "min_seconds": _timing_to_seconds_expr(min_path),
                "max_seconds": _timing_to_seconds_expr(max_path),
            }
        )

    return projection


def _with_optional_match(pipeline, match):
    if match:
        return [{"$match": match}] + pipeline

    return pipeline


# ============================================================
# Basic metric/list query
# ============================================================

def build_metric_pipeline(query: Query):
    match = build_match(query)

    pipeline = []

    pipeline.append(
        {
            "$project": _metric_projection(query)
        }
    )

    pipeline.append(
        {
            "$sort": {
                "date": 1,
                "hostname": 1,
                "bootType": 1,
            }
        }
    )

    if query.limit:
        pipeline.append(
            {
                "$limit": query.limit
            }
        )

    return _with_optional_match(pipeline, match)


# ============================================================
# List hosts
# ============================================================

def build_host_pipeline(query: Query):
    match = {}

    if query.hostname:
        match["hostname"] = query.hostname

    if query.sku:
        match["sku"] = query.sku

    if query.bootType:
        match["bootType"] = query.bootType

    pipeline = [
        {
            "$group": {
                "_id": {
                    "hostname": "$hostname",
                    "sku": "$sku",
                    "bootType": "$bootType",
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "hostname": "$_id.hostname",
                "sku": "$_id.sku",
                "bootType": "$_id.bootType",
            }
        },
        {
            "$sort": {
                "hostname": 1,
                "sku": 1,
                "bootType": 1,
            }
        }
    ]

    if query.limit:
        pipeline.append(
            {
                "$limit": query.limit
            }
        )

    return _with_optional_match(pipeline, match)


# ============================================================
# Lowest / highest
# ============================================================

def build_extreme_pipeline(query: Query):
    match = build_match(query)

    min_path = _metric_field_path(query, "min")
    max_path = _metric_field_path(query, "max")

    pipeline = [
        {
            "$project": {
                **_metric_projection(query),
            }
        }
    ]

    value_field = "min_seconds"

    if query.operation == "highest":
        value_field = "max_seconds"

    pipeline.extend([
        {
            "$match": {
                value_field: {
                    "$ne": None
                }
            }
        },
        {
            "$sort": {
                value_field: (
                    1 if query.operation == "lowest" else -1
                )
            }
        },
        {
            "$limit": 1
        },
    ])

    return _with_optional_match(pipeline, match)


# ============================================================
# Count
# ============================================================

def build_count_pipeline(query: Query):
    match = build_match(query)

    pipeline = [
        {
            "$count": "count"
        }
    ]

    return _with_optional_match(pipeline, match)


# ============================================================
# Average
# ============================================================

def build_average_pipeline(query: Query):
    match = build_match(query)

    max_path = _metric_field_path(query, "max")

    pipeline = [
        {
            "$project": {
                "max_seconds": _timing_to_seconds_expr(max_path)
            }
        },
        {
            "$match": {
                "max_seconds": {
                    "$ne": None
                }
            }
        },
        {
            "$group": {
                "_id": None,
                "average_seconds": {
                    "$avg": "$max_seconds"
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "average_seconds": 1,
            }
        }
    ]

    return _with_optional_match(pipeline, match)


# ============================================================
# Main builder
# ============================================================

def build_pipeline(query: Query):

    if query.operation == "lowest":
        return build_extreme_pipeline(query)

    if query.operation == "highest":
        return build_extreme_pipeline(query)

    if query.operation == "average":
        return build_average_pipeline(query)

    if query.operation == "count":
        return build_count_pipeline(query)

    # Host/list query with no metric.
    if (
        query.operation == "list"
        and not query.metric
    ):
        return build_host_pipeline(query)

    return build_metric_pipeline(query)