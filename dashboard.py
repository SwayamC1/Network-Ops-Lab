# ============================================================
# Meridian Solutions | Network Operations Dashboard
# File: dashboard.py
# Description: Real-time host status, uptime %, and incidents
# Author: Swayam Chopra
# ============================================================

import os
import pyodbc
import pandas as pd
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────

st.set_page_config(
    page_title="Meridian Network Operations",
    page_icon="🖥️",
    layout="wide"
)

st.title("🖥️ Meridian Solutions — Network Operations Dashboard")
st.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ─────────────────────────────────────────
# DATABASE CONNECTION
# ─────────────────────────────────────────

def get_connection():
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USER')};"
        f"PWD={os.getenv('DB_PASSWORD')};"
    )
    return pyodbc.connect(conn_str)


@st.cache_data(ttl=30)
def load_current_status():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM v_current_status", conn)
    conn.close()
    return df


@st.cache_data(ttl=30)
def load_uptime():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM v_host_uptime", conn)
    conn.close()
    return df


@st.cache_data(ttl=30)
def load_incidents():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT
            i.incident_id,
            h.hostname,
            h.department,
            i.started_at,
            i.resolved_at,
            i.description,
            i.resolution,
            CASE WHEN i.resolved_at IS NULL THEN 'Open' ELSE 'Resolved' END AS status
        FROM incidents i
        JOIN hosts h ON h.host_id = i.host_id
        ORDER BY i.started_at DESC
    """, conn)
    conn.close()
    return df


@st.cache_data(ttl=30)
def load_uptime_history():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT
            h.hostname,
            u.checked_at,
            u.is_online,
            u.response_ms
        FROM uptime_log u
        JOIN hosts h ON h.host_id = u.host_id
        ORDER BY u.checked_at DESC
    """, conn)
    conn.close()
    return df


# ─────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────

status_df  = load_current_status()
uptime_df  = load_uptime()
incident_df = load_incidents()

total_hosts   = len(status_df)
online_hosts  = len(status_df[status_df["status"] == "Online"])
offline_hosts = total_hosts - online_hosts
open_incidents = len(incident_df[incident_df["status"] == "Open"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Hosts",     total_hosts)
c2.metric("Online",          online_hosts,  delta=None)
c3.metric("Offline",         offline_hosts, delta=f"-{offline_hosts}" if offline_hosts else None, delta_color="inverse")
c4.metric("Open Incidents",  open_incidents)

st.divider()

# ─────────────────────────────────────────
# HOST STATUS TABLE
# ─────────────────────────────────────────

st.subheader("Current Host Status")

for _, row in status_df.iterrows():
    icon = "🟢" if row["status"] == "Online" else "🔴"
    ms   = f"{row['response_ms']}ms" if row["response_ms"] else "---"
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        col1.markdown(f"{icon} **{row['hostname']}**  \n`{row['ip_address']}`")
        col2.caption(f"Dept: {row['department']}")
        col3.caption(f"Status: **{row['status']}**")
        col4.caption(f"Response: {ms}")

st.divider()

# ─────────────────────────────────────────
# UPTIME PERCENTAGES
# ─────────────────────────────────────────

st.subheader("Uptime % by Host")

for _, row in uptime_df.iterrows():
    pct = float(row["uptime_pct"])
    st.progress(
        pct / 100,
        text=f"{row['hostname']} ({row['department']}) — {pct:.1f}% uptime"
    )

st.divider()

# ─────────────────────────────────────────
# INCIDENTS
# ─────────────────────────────────────────

st.subheader("Incidents")

tab_open, tab_all = st.tabs(["🔴 Open", "📋 All Incidents"])

with tab_open:
    open_df = incident_df[incident_df["status"] == "Open"]
    if open_df.empty:
        st.success("No open incidents.")
    else:
        for _, row in open_df.iterrows():
            with st.container(border=True):
                st.markdown(f"🔴 **{row['hostname']}** — {row['department']}")
                st.caption(f"Started: {row['started_at']}")
                st.write(row["description"])

with tab_all:
    if incident_df.empty:
        st.info("No incidents recorded.")
    else:
        st.dataframe(
            incident_df[["hostname", "department", "status", "started_at", "resolved_at", "description", "resolution"]],
            use_container_width=True,
            hide_index=True
        )

st.divider()

# ─────────────────────────────────────────
# UPTIME HISTORY CHART
# ─────────────────────────────────────────

st.subheader("Response Time History")

history_df = load_uptime_history()
online_history = history_df[history_df["is_online"] == True].copy()

if not online_history.empty:
    online_history["checked_at"] = pd.to_datetime(online_history["checked_at"])
    pivot = online_history.pivot_table(
        index="checked_at",
        columns="hostname",
        values="response_ms"
    )
    st.line_chart(pivot, use_container_width=True)
else:
    st.info("No response time data yet — monitor needs online hosts to chart.")

# ─────────────────────────────────────────
# AUTO REFRESH
# ─────────────────────────────────────────

st.caption("Dashboard refreshes every 30 seconds automatically.")
st.button("🔄 Refresh Now")