from pymongo import MongoClient

from config import (
    MONGO_URI,
    DATABASE_NAME,
    COLLECTION_NAME,
)

from utils import timing_to_seconds


# ============================================================
# MongoDB
# ============================================================

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client[DATABASE_NAME]

collection = db[COLLECTION_NAME]


# ============================================================
# Serialization
# ============================================================

def serialize(value):

    try:

        from bson import ObjectId

        if isinstance(value, ObjectId):

            return str(value)

    except Exception:
        pass

    if isinstance(value, dict):

        return {
            key: serialize(val)
            for key, val in value.items()
        }

    if isinstance(value, list):

        return [
            serialize(item)
            for item in value
        ]

    return value


# ============================================================
# Base filter
# ============================================================

def build_filter(
    hostname=None,
    bootType=None,
    sku=None,
    date_from=None,
    date_to=None,
):

    mongo_filter = {}

    if hostname:

        mongo_filter["hostname"] = hostname

    if bootType:

        mongo_filter["bootType"] = bootType

    if sku:

        mongo_filter["sku"] = sku

    if date_from or date_to:

        date_filter = {}

        if date_from:

            date_filter["$gte"] = date_from

        if date_to:

            date_filter["$lte"] = date_to

        mongo_filter["date"] = date_filter

    return mongo_filter


# ============================================================
# Get documents
# ============================================================

def get_documents(
    hostname=None,
    bootType=None,
    sku=None,
    date_from=None,
    date_to=None,
):

    mongo_filter = build_filter(
        hostname=hostname,
        bootType=bootType,
        sku=sku,
        date_from=date_from,
        date_to=date_to,
    )

    documents = list(
        collection.find(
            mongo_filter,
            {"_id": 0}
        )
    )

    return {
        "records":
            serialize(documents),

        "mongo_filter":
            mongo_filter,

        "record_count":
            len(documents),
    }


# ============================================================
# Unique hosts
# ============================================================

def list_hosts(
    bootType=None,
    sku=None,
):

    match = {}

    if bootType:

        match["bootType"] = bootType

    if sku:

        match["sku"] = sku

    pipeline = [

        {
            "$match": match
        },

        {
            "$group": {

                "_id": {

                    "hostname":
                        "$hostname",

                    "sku":
                        "$sku",

                    "bootType":
                        "$bootType",
                }
            }
        },

        {
            "$project": {

                "_id": 0,

                "hostname":
                    "$_id.hostname",

                "sku":
                    "$_id.sku",

                "bootType":
                    "$_id.bootType",
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

    records = list(
        collection.aggregate(
            pipeline
        )
    )

    return {
        "records":
            serialize(records),

        "mongo_filter":
            match,

        "mongo_pipeline":
            pipeline,

        "record_count":
            len(records),
    }


# ============================================================
# Extract metric
# ============================================================

def get_metric_value(
    record,
    metric
):

    data = record.get(
        "data",
        {}
    )

    if not isinstance(
        data,
        dict
    ):

        return None

    metric_data = data.get(
        metric
    )

    if isinstance(
        metric_data,
        dict
    ):

        return metric_data

    return None


# ============================================================
# Add metric to records
# ============================================================

def extract_metric_records(
    records,
    metric
):

    output = []

    for record in records:

        metric_data = get_metric_value(
            record,
            metric
        )

        if metric_data is None:

            continue

        item = {

            "hostname":
                record.get(
                    "hostname"
                ),

            "sku":
                record.get(
                    "sku"
                ),

            "bootType":
                record.get(
                    "bootType"
                ),

            "date":
                record.get(
                    "date"
                ),

            "metric":
                metric,

            "min":
                metric_data.get(
                    "min"
                ),

            "max":
                metric_data.get(
                    "max"
                ),

            "min_seconds":
                timing_to_seconds(
                    metric_data.get(
                        "min"
                    )
                ),

            "max_seconds":
                timing_to_seconds(
                    metric_data.get(
                        "max"
                    )
                ),
        }

        output.append(item)

    return output


# ============================================================
# Query metric
# ============================================================

def query_metric(
    hostname=None,
    bootType=None,
    sku=None,
    metric=None,
    date_from=None,
    date_to=None,
):

    if not metric:

        raise ValueError(
            "Metric is required."
        )

    result = get_documents(
        hostname=hostname,
        bootType=bootType,
        sku=sku,
        date_from=date_from,
        date_to=date_to,
    )

    metric_records = extract_metric_records(
        result["records"],
        metric
    )

    return {

        "records":
            metric_records,

        "mongo_filter":
            result["mongo_filter"],

        "record_count":
            len(metric_records),
    }