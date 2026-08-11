
import json

import streamlit as st

from core.hybrid_parser import parse_hybrid, OffTopicResponse
from core.query_engine import execute

from ui.formatter import (
    format_query_context,
    format_result,
    records_to_rows,
    summarize_result,
    prettify_metric,
)

from ui.charts import show_chart

from config import COLLECTION_NAME, DATABASE_NAME


# ============================================================
# Page config
# ============================================================

st.set_page_config(
    page_title="BootProfile AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# Custom CSS
# ============================================================

st.markdown("""
<style>
    /* Header bar */
    .app-header {
        background: linear-gradient(90deg, #0f172a 0%, #1e3a5f 100%);
        padding: 1.2rem 2rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .app-header h1 {
        color: #f0f9ff;
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
    }
    .app-header p {
        color: #94a3b8;
        font-size: 0.85rem;
        margin: 0;
    }

    /* Answer card */
    .answer-card {
        background: #f0fdf4;
        border-left: 4px solid #16a34a;
        border-radius: 6px;
        padding: 0.9rem 1.2rem;
        margin-bottom: 1rem;
        font-size: 1.05rem;
        color: #14532d;
        font-weight: 500;
    }
    .answer-card-offtopic {
        background: #eff6ff;
        border-left: 4px solid #3b82f6;
        border-radius: 6px;
        padding: 0.9rem 1.2rem;
        margin-bottom: 1rem;
        color: #1e3a8a;
    }

    /* Context pill row */
    .context-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    .context-pill {
        background: #e2e8f0;
        color: #334155;
        border-radius: 20px;
        padding: 0.2rem 0.75rem;
        font-size: 0.78rem;
        font-weight: 500;
    }
    .context-pill-highlight {
        background: #dbeafe;
        color: #1d4ed8;
        border-radius: 20px;
        padding: 0.2rem 0.75rem;
        font-size: 0.78rem;
        font-weight: 600;
    }

    /* Stat tile */
    [data-testid="metric-container"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem 1rem;
    }

    /* Dataframe */
    [data-testid="stDataFrame"] {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }

    /* Section header */
    .section-label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748b;
        margin-bottom: 0.4rem;
        margin-top: 1rem;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #f8fafc;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# Cached execution
# ============================================================

@st.cache_data(show_spinner=False, ttl=60)
def execute_cached(query_dict):
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
# Sidebar
# ============================================================

with st.sidebar:
    st.markdown("### ⚡ BootProfile AI")
    st.caption("Boot performance dashboard assistant")
    st.divider()

    st.markdown("**Example questions**")
    examples = [
        "Show OVERALL_TOTAL for rc136-031-19-s3 SPI",
        "Which host has the lowest SBL_TOTAL?",
        "Show TBL_TOTAL on 2026-07-31",
        "Plot OVERALL_TOTAL for rc136-031-19-s3",
        "Count records for EB0"
    ]
    for ex in examples:
        st.caption(f"• {ex}")

    st.divider()
    show_debug = st.checkbox("🔧 Show debug info", value=False)


# ============================================================
# Header
# ============================================================

st.markdown("""
<div class="app-header">
    <div>
        <h1>⚡ BootProfile AI Dashboard</h1>
        <p>Ask questions about boot performance metrics, hosts, and timing data</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# Question input
# ============================================================

with st.form("question_form", clear_on_submit=False):
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        question = st.text_input(
            "Your question",
            placeholder="e.g. Which host has the slowest OVERALL_TOTAL for SPI?",
            label_visibility="collapsed",
        )
    with col_btn:
        submitted = st.form_submit_button("Ask ▶", use_container_width=True)


# ============================================================
# Process question
# ============================================================

if submitted and question:

    try:
        with st.spinner("Analysing question..."):
            query, routing = parse_hybrid(question)

        with st.spinner("Querying database..."):
            result = execute_cached(query.to_dict())

        rows = records_to_rows(result["records"])
        q = result["query"]

        # ── Answer card ──────────────────────────────────────
        summary = summarize_result(result)
        st.markdown(
            f'<div class="answer-card">✅ {summary}</div>',
            unsafe_allow_html=True,
        )

        # ── Context pills ─────────────────────────────────────
        pills = []
        if q.get("metric"):
            pills.append(
                f'<span class="context-pill-highlight">'
                f'📊 {prettify_metric(q["metric"])}</span>'
            )
        if q.get("hostname"):
            pills.append(
                f'<span class="context-pill">🖥 {q["hostname"]}</span>'
            )
        if q.get("bootType"):
            pills.append(
                f'<span class="context-pill">🔧 {q["bootType"]}</span>'
            )
        if q.get("sku"):
            pills.append(
                f'<span class="context-pill">💾 {q["sku"]}</span>'
            )
        if q.get("date_from"):
            label = q["date_from"] if q["date_from"] == q.get("date_to") \
                else f'{q["date_from"]} → {q["date_to"]}'
            pills.append(
                f'<span class="context-pill">📅 {label}</span>'
            )
        if pills:
            st.markdown(
                '<div class="context-row">' + "".join(pills) + "</div>",
                unsafe_allow_html=True,
            )

        # ── Stat tiles ────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Records", result["record_count"])
        c2.metric("Operation", q.get("operation", "list").title())
        c3.metric("Metric", (q.get("metric") or "All").replace("_", " "))
        c4.metric("Parser", routing.get("path", "—").title())

        # ── Chart ─────────────────────────────────────────────
        # Show automatically for explicit chart/trend requests.
        # Show as collapsed expander for metric queries with multiple rows.
        _has_metric = bool(result["query"].get("metric"))
        _multi_row = result["record_count"] > 1

        if query.operation == "chart" and rows and _has_metric:
            st.markdown('<p class="section-label">Charts</p>', unsafe_allow_html=True)
            show_chart(result)
        elif _has_metric and _multi_row and query.operation not in {"highest", "lowest", "count", "average"}:
            with st.expander("📈 View Charts"):
                show_chart(result)

        # ── Results table ─────────────────────────────────────
        if rows:
            st.markdown(
                f'<p class="section-label">Results — {len(rows)} row(s)</p>',
                unsafe_allow_html=True,
            )
            st.dataframe(rows, use_container_width=True, hide_index=True)

        # ── Debug expanders ───────────────────────────────────
        if show_debug:
            with st.expander("📋 Detailed view"):
                st.markdown(format_result(result))

            with st.expander("🗄 MongoDB Query"):
                pipeline_str = json.dumps(result["pipeline"], indent=2, default=str)
                st.caption(f"Collection: **{DATABASE_NAME}.{COLLECTION_NAME}**")
                st.code(
                    f"db.{COLLECTION_NAME}.aggregate(\n{pipeline_str}\n)",
                    language="javascript",
                )

            with st.expander("🐛 Debug"):
                st.json({
                    "routing": routing,
                    "query": query.to_dict(),
                    "record_count": result["record_count"],
                    "pipeline": result["pipeline"],
                })

    except OffTopicResponse as off_topic:
        st.markdown(
            f'<div class="answer-card-offtopic">💬 {off_topic.answer}</div>',
            unsafe_allow_html=True,
        )

    except Exception as exc:
        st.error(f"**{type(exc).__name__}:** {exc}")
        if show_debug:
            with st.expander("Error details"):
                st.exception(exc)

