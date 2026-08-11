import pandas as pd
import plotly.express as px
import streamlit as st


def _build_df(records, metric):
    rows = []
    for record in records:
        value = record.get("max_seconds")
        if value is None:
            value = record.get("min_seconds")
        if value is None:
            value = record.get(metric)
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue

        rows.append({
            "date": record.get("date"),
            "hostname": record.get("hostname", "unknown"),
            "bootType": record.get("bootType", ""),
            "sku": record.get("sku", ""),
            "value": value,
        })
    return pd.DataFrame(rows)


def show_chart(result):
    query = result.get("query", {})
    records = result.get("records", [])
    metric = query.get("metric") or "value"
    label = metric.replace("_", " ").title()

    if not records:
        st.info("No data available for chart.")
        return

    df = _build_df(records, metric)

    if df.empty:
        st.info("No numeric values available for chart.")
        return

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date")

    tab_line, tab_bar, tab_pie, tab_box = st.tabs(
        ["📈 Line", "📊 Bar", "🥧 Pie", "📦 Box"]
    )

    color_col = "hostname" if df["hostname"].nunique() > 1 else "bootType"

    # ── Line chart ──────────────────────────────────────────
    with tab_line:
        if "date" in df.columns and df["date"].notna().any():
            fig = px.line(
                df,
                x="date",
                y="value",
                color=color_col,
                markers=True,
                title=f"{label} over time",
                labels={"value": label, "date": "Date"},
            )
            fig.update_layout(
                legend_title_text="",
                plot_bgcolor="#f8fafc",
                paper_bgcolor="white",
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Date information required for a line chart.")

    # ── Bar chart ───────────────────────────────────────────
    with tab_bar:
        group_col = "hostname" if df["hostname"].nunique() > 1 else "bootType"
        # Deduplicate in case group_col and "bootType" are the same.
        group_cols = list(dict.fromkeys([group_col, "bootType"]))
        df_bar = (
            df.groupby(group_cols, as_index=False)["value"]
            .mean()
            .rename(columns={"value": f"Avg {label}"})
        )
        fig = px.bar(
            df_bar,
            x=group_col,
            y=f"Avg {label}",
            color=group_cols[-1],
            barmode="group",
            title=f"Average {label} by {group_col}",
            labels={f"Avg {label}": f"Avg {label} (s)"},
            text_auto=".3f",
        )
        fig.update_layout(
            plot_bgcolor="#f8fafc",
            paper_bgcolor="white",
            legend_title_text="Boot Type",
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Pie chart ───────────────────────────────────────────
    with tab_pie:
        group_col = "bootType" if df["bootType"].nunique() > 1 else "hostname"
        df_pie = (
            df.groupby(group_col, as_index=False)["value"]
            .mean()
            .rename(columns={"value": f"Avg {label}"})
        )
        fig = px.pie(
            df_pie,
            names=group_col,
            values=f"Avg {label}",
            title=f"Share of avg {label} by {group_col}",
            hole=0.35,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(paper_bgcolor="white", showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    # ── Box plot ────────────────────────────────────────────
    with tab_box:
        fig = px.box(
            df,
            x="bootType",
            y="value",
            color="bootType",
            points="all",
            title=f"{label} distribution by Boot Type",
            labels={"value": f"{label} (s)", "bootType": "Boot Type"},
        )
        fig.update_layout(
            plot_bgcolor="#f8fafc",
            paper_bgcolor="white",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
