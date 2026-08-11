
import json

import streamlit as st

from core.hybrid_parser import parse_hybrid, OffTopicResponse
from core.query_engine import execute

from ui.formatter import (
    format_query_context,
    format_result,
    records_to_rows,
    summarize_result,
)

from ui.charts import show_chart

from config import (
    COLLECTION_NAME,
    DATABASE_NAME,
)


st.set_page_config(
    page_title="Platform Service AI Chatbot",
    page_icon="📊",
    layout="wide",
)


st.title(
    "BootProfile Dashboard AI Chatbot"
)

st.caption(
    "Ask questions about hosts, metrics, "
    "boot types and performance."
)


show_debug = st.sidebar.checkbox(
    "Show debug info",
    value=False,
)


# ============================================================
# Cached execution
# ============================================================

@st.cache_data(
    show_spinner=False,
    ttl=60,
)
def execute_cached(query_dict):
    """
    Execute a trusted Query represented as a dictionary.
    """

    from core.parser import Query

    query = Query(
        question=query_dict["question"],
        operation=query_dict["operation"],
        metric=query_dict.get("metric"),
        hostname=query_dict.get("hostname"),
        sku=query_dict.get("sku"),
        bootType=query_dict.get("bootType"),
        date_from=query_dict.get("date_from"),
        date_to=query_dict.get("date_to"),
        group_by=query_dict.get("group_by"),
        limit=query_dict.get("limit", 100),
    )

    return execute(query)


# ============================================================
# Question form
# ============================================================

with st.form("question_form"):

    question = st.text_input(
        "Question",
        placeholder=(
            "Example: Which host had the "
            "slowest OVERALL_TOTAL?"
        ),
    )

    submitted = st.form_submit_button(
        "Ask"
    )


# ============================================================
# Process question
# ============================================================

if submitted and question:

    try:

        with st.spinner("Understanding your question..."):
            query, routing = parse_hybrid(question)

        # ----------------------------------------------------
        # Execute MongoDB query
        # ----------------------------------------------------

        with st.spinner(
            "Querying MongoDB..."
        ):

            result = execute_cached(
                query.to_dict()
            )

        rows = records_to_rows(
            result["records"]
        )

        # ----------------------------------------------------
        # Answer
        # ----------------------------------------------------

        st.success(
            summarize_result(result)
        )

        st.caption(
            format_query_context(
                result["query"],
                result["record_count"],
            )
        )

        # ----------------------------------------------------
        # Statistics
        # ----------------------------------------------------

        stats = st.columns(4)

        stats[0].metric(
            "Rows",
            result["record_count"],
        )

        stats[1].metric(
            "Operation",
            result["query"]
            .get("operation", "list")
            .title(),
        )

        stats[2].metric(
            "Metric",
            (
                result["query"]
                .get("metric")
                or "All"
            ).replace("_", " "),
        )

        stats[3].metric(
            "Parser",
            routing.get(
                "path",
                "unknown",
            ).title(),
        )

        # ----------------------------------------------------
        # Chart
        # ----------------------------------------------------

        if query.operation == "chart":
            show_chart(result)

        # ----------------------------------------------------
        # Table
        # ----------------------------------------------------

        if rows:

            st.subheader(
                "Results"
            )

            st.dataframe(
                rows,
                use_container_width=True,
                hide_index=True,
            )

        # ----------------------------------------------------
        # Debug
        # ----------------------------------------------------

        if show_debug:

            with st.expander(
                "Detailed view"
            ):

                st.markdown(
                    format_result(result)
                )

            with st.expander(
                "MongoDB Query"
            ):

                pipeline_str = json.dumps(
                    result["pipeline"],
                    indent=2,
                    default=str,
                )

                st.caption(
                    "Collection: "
                    f"**{DATABASE_NAME}."
                    f"{COLLECTION_NAME}**"
                )

                st.code(
                    (
                        f"db.{COLLECTION_NAME}"
                        ".aggregate(\n"
                        f"{pipeline_str}\n"
                        ")"
                    ),
                    language="javascript",
                )

            with st.expander(
                "Debug"
            ):

                st.json(
                    {
                        "routing": routing,
                        "query": query.to_dict(),
                        "record_count":
                            result["record_count"],
                        "pipeline":
                            result["pipeline"],
                    }
                )

    except OffTopicResponse as off_topic:
        st.info(off_topic.answer)

    except Exception as exc:

        st.error(
            f"{type(exc).__name__}: {exc}"
        )

        if show_debug:

            with st.expander(
                "Error details"
            ):
                st.exception(exc)

