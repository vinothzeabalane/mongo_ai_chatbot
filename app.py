import json

import streamlit as st

from parser import parse_question

from dashboard_tools import (
    list_hosts,
    query_metric,
)

from analytics import analyze

from formatter import format_result


# ============================================================
# Page
# ============================================================

st.set_page_config(
    page_title="Dashboard AI Assistant",
    layout="wide"
)

st.title(
    "Dashboard AI Assistant"
)

st.write(
    "Ask questions about hosts, metrics, boot types and performance."
)


# ============================================================
# Question
# ============================================================

question = st.text_input(
    "Question",
    placeholder=(
        "Example: "
        "which host has the highest overall time?"
    )
)


# ============================================================
# Ask
# ============================================================

if st.button("Ask"):

    if not question.strip():

        st.warning(
            "Please enter a question."
        )

        st.stop()


    try:

        # ====================================================
        # 1. Parse
        # ====================================================

        parsed = parse_question(
            question.strip()
        )


        # ====================================================
        # 2. Show parser result
        # ====================================================

        operation = parsed[
            "operation"
        ]

        hostname = parsed[
            "hostname"
        ]

        boot_type = parsed[
            "bootType"
        ]

        sku = parsed[
            "sku"
        ]

        metric = parsed[
            "metric"
        ]

        date_from = parsed[
            "date_from"
        ]

        date_to = parsed[
            "date_to"
        ]


        # ====================================================
        # 3. List hosts
        # ====================================================

        if operation == "list_hosts":

            result = list_hosts(

                bootType=boot_type,

                sku=sku
            )

            answer = format_result(
                operation,
                result
            )


        # ====================================================
        # 4. Metric question
        # ====================================================

        elif metric:

            result = query_metric(

                hostname=hostname,

                bootType=boot_type,

                sku=sku,

                metric=metric,

                date_from=date_from,

                date_to=date_to
            )


            # ------------------------------------------------
            # Analysis requested?
            # ------------------------------------------------

            if operation in (
                "average",
                "highest",
                "lowest",
                "compare",
                "change",
            ):

                analysis = analyze(
                    operation,
                    result[
                        "records"
                    ]
                )

                answer = format_result(

                    operation,

                    result,

                    analysis
                )

            else:

                answer = format_result(

                    operation,

                    result
                )


        # ====================================================
        # 5. Unknown question
        # ====================================================

        else:

            answer = (
                "I could not determine the metric or "
                "operation from the question."
            )


        # ====================================================
        # Answer
        # ====================================================

        st.subheader(
            "Answer"
        )

        st.markdown(
            answer
        )


        # ====================================================
        # Debug
        # ====================================================

        with st.expander(
            "Debug",
            expanded=False
        ):

            st.json({
                "parsed":
                    parsed,

                "operation":
                    operation,

                "metric":
                    metric,

                "hostname":
                    hostname,

                "bootType":
                    boot_type,

                "sku":
                    sku,

                "date_from":
                    date_from,

                "date_to":
                    date_to,
            })


            if "result" in locals():

                st.markdown(
                    "### MongoDB result"
                )

                st.json(
                    result
                )


    except Exception as exc:

        st.error(
            "Error: {}".format(
                exc
            )
        )