from parser import Query
from query_builder import build_pipeline
from mongo import find_many


def execute(query):
    """
    Execute a parsed Query against MongoDB.
    """

    if not isinstance(query, Query):
        raise TypeError(
            "execute() expects a Query object"
        )

    pipeline = build_pipeline(query)

    records = find_many(pipeline)

    return {
        "query": query.to_dict(),
        "record_count": len(records),
        "pipeline": pipeline,
        "records": records,
    }