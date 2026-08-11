import streamlit as st

from parser import parse_question
from query_engine import execute
from formatter import (
    format_query_context,
    format_result,
    records_to_rows,
    summarize_result,
)
from charts import show_chart


st.set_page_config(
    page_title="BootProfile Dashboard AI Chatbot",
    page_icon="📊",
    layout="wide",
)


st.title("BootProfile Dashboard AI Chatbot")

st.caption(
    "Ask questions about hosts, metrics, "
    "boot types and performance."
)


@st.cache_data(show_spinner=False, ttl=60)
def execute_cached(query_payload):
    query = parse_question(query_payload["question"])
    return execute(query)


with st.form("question_form"):

    question = st.text_input(
        "Question",
        placeholder=(
            "Example: Show OVERALL_TOTAL for "
            "rc136-031-19-s3 SPI"
        ),
    )

    submitted = st.form_submit_button("Ask")


if submitted and question:

    try:

        query = parse_question(question)
        result = execute_cached({"question": query.question})
        rows = records_to_rows(result["records"])

        st.success(summarize_result(result))
        st.caption(
            format_query_context(
                result["query"],
                result["record_count"],
            )
        )

        stats = st.columns(3)
        stats[0].metric("Rows", result["record_count"])
        stats[1].metric(
            "Operation",
            result["query"].get("operation", "list").title(),
        )
        stats[2].metric(
            "Metric",
            (result["query"].get("metric") or "All").replace("_", " "),
        )

        if query.operation == "chart":
            show_chart(result)

        if rows:
            st.subheader("Results")
            st.dataframe(
                rows,
                use_container_width=True,
                hide_index=True,
            )

        with st.expander("Detailed view"):
            st.markdown(
                format_result(result)
            )

        with st.expander("Debug"):

            st.json(
                {
                    "query": query.to_dict(),
                    "record_count":
                        result["record_count"],
                    "pipeline":
                        result["pipeline"],
                }
            )

    except Exception as exc:

        st.error(
            f"{type(exc).__name__}: {exc}"
        )

        with st.expander("Error details"):
            st.exception(exc)