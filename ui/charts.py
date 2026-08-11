import pandas as pd
import streamlit as st


def show_chart(result):

    query = result.get(
        "query",
        {}
    )

    records = result.get(
        "records",
        []
    )

    metric = query.get(
        "metric"
    )

    if not records:
        st.info(
            "No data available for chart."
        )
        return

    if not metric:
        st.info(
            "A metric is required for a chart."
        )
        return

    rows = []

    for record in records:

        date = record.get(
            "date"
        )

        value = record.get("max_seconds")

        if value is None:
            value = record.get("min_seconds")

        if value is None:
            value = record.get(metric)

        if date is None or value is None:
            continue

        try:
            value = float(value)
        except (
            TypeError,
            ValueError,
        ):
            continue

        rows.append(
            {
                "date": date,
                metric: value,
            }
        )

    if not rows:
        st.info(
            "No numeric values available for chart."
        )
        return

    df = pd.DataFrame(rows)

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["date"]
    )

    df = df.sort_values(
        "date"
    )

    if df.empty:
        st.info(
            "No valid dates available."
        )
        return

    df = df.set_index(
        "date"
    )

    st.line_chart(
        df[[metric]]
    )