"""Iceberg Lakehouse — Live Analytics Dashboard.

Connects to Trino and renders real-time business metrics from the gold layer.
"""
from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import trino

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Iceberg Lakehouse Analytics",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.metric-card {
    background: linear-gradient(135deg, #1a1d2e 0%, #1e2240 100%);
    border: 1px solid #2d3461;
    border-radius: 14px;
    padding: 22px 20px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 30px rgba(102,126,234,0.2);
}
.metric-icon { font-size: 1.6rem; margin-bottom: 8px; }
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2;
}
.metric-label {
    font-size: 0.75rem;
    color: #6b7a99;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-top: 8px;
    font-weight: 600;
}
.section-header {
    font-size: 1rem;
    font-weight: 600;
    color: #a0aec0;
    padding-bottom: 10px;
    border-bottom: 1px solid #2d3461;
    margin-bottom: 14px;
}
.tech-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    margin: 2px;
    letter-spacing: 0.5px;
}
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Trino connection ───────────────────────────────────────────────────────────
TRINO_HOST = os.getenv("TRINO_HOST", "trino")
TRINO_PORT = int(os.getenv("TRINO_PORT", "8080"))

PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#a0aec0", family="Inter, sans-serif", size=12),
    margin=dict(l=10, r=10, t=35, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#6b7a99", size=11)),
)
PALETTE = ["#667eea", "#764ba2", "#f093fb", "#f5576c", "#4facfe", "#43e97b"]


@st.cache_data(ttl=60, show_spinner=False)
def query(sql: str) -> pd.DataFrame:
    """Run a Trino query; cache results for 60 seconds."""
    try:
        conn = trino.dbapi.connect(
            host=TRINO_HOST, port=TRINO_PORT,
            user="streamlit", catalog="lakehouse",
        )
        cur = conn.cursor()
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=cols)
    except Exception as exc:
        st.error(f"⚠️ Trino unavailable: {exc}")
        return pd.DataFrame()


# ── Header ─────────────────────────────────────────────────────────────────────
left, right = st.columns([4, 1])
with left:
    st.markdown("# 🧊 Iceberg Lakehouse")
    badges = [
        ("#667eea20", "#667eea", "Apache Iceberg"),
        ("#764ba220", "#764ba2", "Apache Spark"),
        ("#f093fb20", "#f093fb", "Nessie"),
        ("#4facfe20", "#4facfe", "MinIO"),
        ("#43e97b20", "#43e97b", "Trino"),
    ]
    badge_html = " ".join(
        f"<span class='tech-badge' style='background:{bg};color:{fg};border:1px solid {fg}40'>{lbl}</span>"
        for bg, fg, lbl in badges
    )
    st.markdown(badge_html, unsafe_allow_html=True)
with right:
    st.markdown(
        f"<div style='text-align:right;color:#4a5568;font-size:0.78rem;padding-top:20px'>"
        f"🕐 {datetime.now().strftime('%H:%M:%S')}<br>"
        f"<span style='color:#2d3461'>Auto-refresh: 60s</span></div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ── Fetch KPI data ─────────────────────────────────────────────────────────────
kpi_df = query("""
    SELECT
        ROUND(SUM(gross_sales), 2)                                AS total_revenue,
        SUM(order_count)                                          AS total_orders,
        ROUND(SUM(gross_sales) / NULLIF(SUM(order_count), 0), 2) AS avg_order_value,
        COUNT(DISTINCT order_date)                                AS trading_days
    FROM lakehouse.gold.daily_sales
""")

audit_kpi = query("""
    SELECT
        ROUND(100.0 * SUM(quarantined_rows) / NULLIF(SUM(bronze_rows), 0), 2) AS quarantine_pct,
        COUNT(*) AS total_runs
    FROM lakehouse.monitoring.pipeline_runs
""")

# ── KPI Cards ──────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📊 Key Performance Indicators</div>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)

def metric_card(col, icon, value, label):
    with col:
        st.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-icon'>{icon}</div>"
            f"<div class='metric-value'>{value}</div>"
            f"<div class='metric-label'>{label}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

if not kpi_df.empty:
    rev   = float(kpi_df["total_revenue"].iloc[0] or 0)
    orders = int(kpi_df["total_orders"].iloc[0] or 0)
    aov   = float(kpi_df["avg_order_value"].iloc[0] or 0)
    qpct  = float(audit_kpi["quarantine_pct"].iloc[0] or 0) if not audit_kpi.empty else 0.0
    metric_card(c1, "💰", f"${rev:,.0f}",   "Total Revenue")
    metric_card(c2, "🛒", f"{orders:,}",     "Total Orders")
    metric_card(c3, "📈", f"${aov:,.2f}",   "Avg Order Value")
    metric_card(c4, "🔍", f"{qpct}%",        "Quarantine Rate")
else:
    st.info("Waiting for pipeline data…")

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 1: Daily trend + Channel donut ─────────────────────────────────────────
r1a, r1b = st.columns([3, 2])

with r1a:
    st.markdown("<div class='section-header'>📅 Daily Sales Trend</div>", unsafe_allow_html=True)
    trend = query("""
        SELECT order_date, SUM(gross_sales) AS daily_sales
        FROM lakehouse.gold.daily_sales
        GROUP BY order_date ORDER BY order_date
    """)
    if not trend.empty:
        trend["order_date"] = pd.to_datetime(trend["order_date"])
        trend["rolling_7d"] = trend["daily_sales"].rolling(7, min_periods=1).mean().round(2)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend["order_date"], y=trend["daily_sales"],
            name="Daily Sales",
            line=dict(color="#667eea", width=1.5),
            fill="tozeroy", fillcolor="rgba(102,126,234,0.08)",
            hovertemplate="$%{y:,.2f}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=trend["order_date"], y=trend["rolling_7d"],
            name="7-day Avg",
            line=dict(color="#f093fb", width=2, dash="dot"),
            hovertemplate="$%{y:,.2f}<extra></extra>",
        ))
        fig.update_layout(
            **PLOTLY_THEME, height=280,
            xaxis=dict(gridcolor="#1a1d2e", showgrid=True),
            yaxis=dict(gridcolor="#1a1d2e", tickprefix="$"),
        )
        st.plotly_chart(fig, use_container_width=True)

with r1b:
    st.markdown("<div class='section-header'>🍩 Channel Mix</div>", unsafe_allow_html=True)
    ch = query("""
        SELECT sales_channel, ROUND(SUM(gross_sales), 2) AS revenue
        FROM lakehouse.gold.daily_sales
        GROUP BY sales_channel ORDER BY revenue DESC
    """)
    if not ch.empty:
        fig = go.Figure(go.Pie(
            labels=ch["sales_channel"],
            values=ch["revenue"],
            hole=0.58,
            marker=dict(colors=PALETTE, line=dict(color="#0e1117", width=2)),
            textfont=dict(color="#a0aec0", size=12),
            hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<extra></extra>",
        ))
        fig.update_layout(**PLOTLY_THEME, height=280)
        st.plotly_chart(fig, use_container_width=True)

# ── Row 2: Category bar + Currency comparison ──────────────────────────────────
r2a, r2b = st.columns([2, 3])

with r2a:
    st.markdown("<div class='section-header'>🏷️ Revenue by Category</div>", unsafe_allow_html=True)
    cat = query("""
        SELECT category, ROUND(SUM(gross_sales), 2) AS total_sales
        FROM lakehouse.gold.daily_sales
        GROUP BY category ORDER BY total_sales ASC
    """)
    if not cat.empty:
        fig = go.Figure(go.Bar(
            x=cat["total_sales"], y=cat["category"],
            orientation="h",
            marker=dict(
                color=cat["total_sales"],
                colorscale=[[0, "#667eea"], [1, "#764ba2"]],
                showscale=False,
            ),
            text=cat["total_sales"].apply(lambda v: f"${v:,.0f}"),
            textposition="outside",
            textfont=dict(color="#a0aec0", size=11),
            hovertemplate="<b>%{y}</b>: $%{x:,.2f}<extra></extra>",
        ))
        fig.update_layout(
            **PLOTLY_THEME, height=280,
            xaxis=dict(visible=False),
            yaxis=dict(gridcolor="#1a1d2e"),
        )
        st.plotly_chart(fig, use_container_width=True)

with r2b:
    st.markdown("<div class='section-header'>💱 Revenue by Currency</div>", unsafe_allow_html=True)
    curr = query("""
        SELECT
            currency,
            ROUND(SUM(gross_sales), 2) AS revenue,
            SUM(order_count)           AS orders
        FROM lakehouse.gold.daily_sales
        GROUP BY currency ORDER BY revenue DESC
    """)
    if not curr.empty:
        fig = px.bar(
            curr, x="currency", y="revenue",
            color="currency", color_discrete_sequence=PALETTE,
            text_auto=False,
            hover_data={"orders": True, "revenue": ":.2f"},
        )
        fig.update_traces(
            texttemplate="$%{y:,.0f}", textposition="outside",
            textfont=dict(color="#a0aec0"),
        )
        fig.update_layout(
            **PLOTLY_THEME, height=280, showlegend=False,
            xaxis=dict(gridcolor="#1a1d2e"),
            yaxis=dict(gridcolor="#1a1d2e", tickprefix="$"),
        )
        st.plotly_chart(fig, use_container_width=True)

# ── Pipeline Audit Table ────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>⚙️ Pipeline Audit — Last 10 Runs</div>", unsafe_allow_html=True)
runs = query("""
    SELECT
        CAST(run_at AS VARCHAR)                                           AS run_at,
        bronze_rows,
        silver_rows,
        quarantined_rows,
        gold_rows,
        ROUND(100.0 * quarantined_rows / NULLIF(bronze_rows, 0), 2)     AS quarantine_pct,
        run_status
    FROM lakehouse.monitoring.pipeline_runs
    ORDER BY run_at DESC
    LIMIT 10
""")

if not runs.empty:
    def _colour_status(val):
        return (
            "color: #22c55e; font-weight: 600" if val == "success"
            else "color: #ef4444; font-weight: 600"
        )
    styled = runs.style.map(_colour_status, subset=["run_status"])
    st.dataframe(styled, use_container_width=True, hide_index=True)
else:
    st.info("No pipeline runs recorded yet. Run `run_pipeline.ps1` first.")

# ── Iceberg Snapshot History ───────────────────────────────────────────────────
st.markdown("<div class='section-header'>🕐 Iceberg Snapshot History (Silver Orders)</div>", unsafe_allow_html=True)
snaps = query("""
    SELECT
        snapshot_id,
        CAST(committed_at AS VARCHAR) AS committed_at,
        operation,
        summary['added-records']      AS added_records
    FROM lakehouse.silver."orders$snapshots"
    ORDER BY committed_at DESC
    LIMIT 5
""")
if not snaps.empty:
    st.dataframe(snaps, use_container_width=True, hide_index=True)
else:
    st.info("No snapshot history yet.")

# ── Footer ──────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#2d3461;font-size:0.72rem;padding:4px'>"
    "Iceberg Lakehouse Platform · Apache Iceberg + Spark + Nessie + MinIO + Trino · "
    "Built with Streamlit · Auto-refresh every 60s"
    "</div>",
    unsafe_allow_html=True,
)
