# ============================================================
# Meridian Solutions | Network Operations Dashboard
# File: app.py
# Description: Live dashboard reading from SQLite
#              (Production uses SQL Server — see schema.sql)
# Author: Swayam Chopra
# ============================================================

import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime

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
st.info("📡 Live demo using SQLite sample data. Production environment uses SQL Server with real-time Python monitoring.", icon="ℹ️")

# ─────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────

def get_conn():
    return sqlite3.connect("meridian_ops.db", check_same_thread=False)


@st.cache_data(ttl=30)
def load_current_status():
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT
            h.hostname,
            h.ip_address,
            h.department,
            u.checked_at,
            CASE WHEN u.is_online = 1 THEN 'Online' ELSE 'Offline' END AS status,
            u.response_ms
        FROM hosts h
        JOIN uptime_log u ON u.log_id = (
            SELECT log_id FROM uptime_log
            WHERE host_id = h.host_id
            ORDER BY checked_at DESC LIMIT 1
        )
    """, conn)
    conn.close()
    return df


@st.cache_data(ttl=30)
def load_uptime():
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT
            h.hostname,
            h.ip_address,
            h.department,
            h.vlan,
            COUNT(*)                                                AS total_checks,
            SUM(u.is_online)                                        AS online_count,
            ROUND(SUM(u.is_online) * 100.0 / COUNT(*), 2)          AS uptime_pct,
            AVG(CASE WHEN u.is_online = 1 THEN u.response_ms END)  AS avg_response_ms
        FROM hosts h
        JOIN uptime_log u ON u.host_id = h.host_id
        GROUP BY h.host_id, h.hostname, h.ip_address, h.department, h.vlan
    """, conn)
    conn.close()
    return df


@st.cache_data(ttl=30)
def load_incidents():
    conn = get_conn()
    df = pd.read_sql_query("""
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
def load_history():
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT h.hostname, u.checked_at, u.is_online, u.response_ms
        FROM uptime_log u
        JOIN hosts h ON h.host_id = u.host_id
        ORDER BY u.checked_at ASC
    """, conn)
    conn.close()
    return df


# ─────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────

status_df   = load_current_status()
uptime_df   = load_uptime()
incident_df = load_incidents()

total_hosts    = len(status_df)
online_hosts   = len(status_df[status_df["status"] == "Online"])
offline_hosts  = total_hosts - online_hosts
open_incidents = len(incident_df[incident_df["status"] == "Open"])

# ─────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Hosts",    total_hosts)
c2.metric("Online",         online_hosts)
c3.metric("Offline",        offline_hosts,
          delta=f"-{offline_hosts}" if offline_hosts else None,
          delta_color="inverse")
c4.metric("Open Incidents", open_incidents)

st.divider()

# ─────────────────────────────────────────
# HOST STATUS
# ─────────────────────────────────────────

st.subheader("Current Host Status")

for _, row in status_df.iterrows():
    icon = "🟢" if row["status"] == "Online" else "🔴"
    ms   = f"{int(row['response_ms'])}ms" if row["response_ms"] else "---"
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        col1.markdown(f"{icon} **{row['hostname']}**  \n`{row['ip_address']}`")
        col2.caption(f"Dept: {row['department']}")
        col3.caption(f"Status: **{row['status']}**")
        col4.caption(f"Response: {ms}")

st.divider()

# ─────────────────────────────────────────
# UPTIME %
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
        st.success("✅ No open incidents.")
    else:
        for _, row in open_df.iterrows():
            with st.container(border=True):
                st.markdown(f"🔴 **{row['hostname']}** — {row['department']}")
                st.caption(f"Started: {row['started_at']}")
                st.write(row["description"])

with tab_all:
    st.dataframe(
        incident_df[["hostname", "department", "status",
                     "started_at", "resolved_at",
                     "description", "resolution"]],
        use_container_width=True,
        hide_index=True
    )

st.divider()

# ─────────────────────────────────────────
# RESPONSE TIME CHART
# ─────────────────────────────────────────

st.subheader("Response Time History (ms)")

history_df = load_history()
online_history = history_df[history_df["is_online"] == 1].copy()
online_history["checked_at"] = pd.to_datetime(online_history["checked_at"])

pivot = online_history.pivot_table(
    index="checked_at",
    columns="hostname",
    values="response_ms"
)

st.line_chart(pivot, use_container_width=True)

st.caption("Demo data simulates 24 hours of monitoring across 6 network hosts.")
st.button("🔄 Refresh")
