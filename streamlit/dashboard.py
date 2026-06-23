```python
# ============================================================
# Meridian Solutions | Network Operations Dashboard
# File: dashboard.py
# Description: SQL Server dashboard for host status, uptime,
#              incident history, and response-time monitoring
# Author: Swayam Chopra | UMBC MIS 2026
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
    """
    Connect to SQL Server.

    The dashboard can use a read-only reporting account if these
    optional environment variables are set:

    DB_DASHBOARD_USER
    DB_DASHBOARD_PASSWORD

    If they are not set, the dashboard falls back to DB_USER and DB_PASSWORD.
    """
    db_user = os.getenv("DB_DASHBOARD_USER") or os.getenv("DB_USER")
    db_password = os.getenv("DB_DASHBOARD_PASSWORD") or os.getenv("DB_PASSWORD")

    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={db_user};"
        f"PWD={db_password};"
    )

    return pyodbc.connect(conn_str)


def load_sql(query: str) -> pd.DataFrame:
    """Run a SQL query and return the result as a DataFrame."""
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    return df


@st.cache_data(ttl=30)
def load_current_status():
    return load_sql("""
        SELECT
            hostname,
            ip_address,
            department,
            vlan,
            checked_at,
            status,
            response_ms,
            notes
        FROM dbo.v_current_status
        ORDER BY vlan, hostname;
    """)


@st.cache_data(ttl=30)
def load_uptime():
    return load_sql("""
        SELECT
            hostname,
            ip_address,
            department,
            vlan,
            total_checks,
            online_count,
            uptime_pct,
            avg_response_ms
        FROM dbo.v_host_uptime
        ORDER BY vlan, hostname;
    """)


@st.cache_data(ttl=30)
def load_incidents():
    return load_sql("""
        SELECT
            incident_id,
            hostname,
            department,
            incident_type,
            service_name,
            port_number,
            started_at,
            resolved_at,
            status,
            description,
            resolution
        FROM dbo.v_incident_history
        ORDER BY started_at DESC;
    """)


@st.cache_data(ttl=30)
def load_uptime_history():
    return load_sql("""
        SELECT
            h.hostname,
            u.checked_at,
            u.is_online,
            u.response_ms
        FROM dbo.uptime_log u
        JOIN dbo.hosts h
            ON h.host_id = u.host_id
        ORDER BY u.checked_at ASC;
    """)


# ─────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────

try:
    status_df = load_current_status()
    uptime_df = load_uptime()
    incident_df = load_incidents()
    history_df = load_uptime_history()

except Exception as e:
    st.error("Unable to load dashboard data from SQL Server.")
    st.exception(e)
    st.stop()


# ─────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────

total_hosts = len(status_df)
online_hosts = len(status_df[status_df["status"] == "Online"]) if not status_df.empty else 0
offline_hosts = total_hosts - online_hosts

open_incidents = (
    len(incident_df[incident_df["status"] == "Open"])
    if not incident_df.empty
    else 0
)

service_incidents = (
    len(incident_df[
        (incident_df["status"] == "Open")
        & (incident_df["incident_type"] == "SERVICE")
    ])
    if not incident_df.empty
    else 0
)

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Total Hosts", total_hosts)
c2.metric("Online", online_hosts)
c3.metric(
    "Offline",
    offline_hosts,
    delta=f"-{offline_hosts}" if offline_hosts else None,
    delta_color="inverse"
)
c4.metric("Open Incidents", open_incidents)
c5.metric("Open Service Issues", service_incidents)

st.divider()


# ─────────────────────────────────────────
# CURRENT HOST STATUS
# ─────────────────────────────────────────

st.subheader("Current Host Status")

if status_df.empty:
    st.info("No host status data yet. Start `monitor.py` to populate uptime logs.")
else:
    for _, row in status_df.iterrows():
        icon = "🟢" if row["status"] == "Online" else "🔴"
        response_ms = row["response_ms"]
        ms_display = f"{int(response_ms)}ms" if pd.notna(response_ms) else "---"
        notes = row["notes"] if pd.notna(row["notes"]) else "No service issues noted."

        with st.container(border=True):
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 4])

            col1.markdown(f"{icon} **{row['hostname']}**  \n`{row['ip_address']}`")
            col2.caption(f"Dept: {row['department']}")
            col3.caption(f"VLAN: {row['vlan']}")
            col4.caption(f"Response: {ms_display}")
            col5.caption(f"Notes: {notes}")

st.divider()


# ─────────────────────────────────────────
# UPTIME PERCENTAGES
# ─────────────────────────────────────────

st.subheader("Uptime % by Host")

if uptime_df.empty:
    st.info("No uptime data available yet.")
else:
    for _, row in uptime_df.iterrows():
        pct = float(row["uptime_pct"])
        avg_response = row["avg_response_ms"]

        avg_display = (
            f"{int(avg_response)}ms avg response"
            if pd.notna(avg_response)
            else "No response data"
        )

        st.progress(
            pct / 100,
            text=(
                f"{row['hostname']} ({row['department']}, VLAN {row['vlan']}) — "
                f"{pct:.1f}% uptime, {avg_display}"
            )
        )

st.divider()


# ─────────────────────────────────────────
# INCIDENTS
# ─────────────────────────────────────────

st.subheader("Incidents")

tab_open, tab_service, tab_all = st.tabs(
    ["🔴 Open Incidents", "🛠️ Service Issues", "📋 All Incidents"]
)

with tab_open:
    open_df = incident_df[incident_df["status"] == "Open"].copy()

    if open_df.empty:
        st.success("No open incidents.")
    else:
        for _, row in open_df.iterrows():
            incident_label = row["incident_type"]

            if row["incident_type"] == "SERVICE":
                incident_label = (
                    f"SERVICE — {row['service_name']}({int(row['port_number'])})"
                )

            with st.container(border=True):
                st.markdown(f"🔴 **{row['hostname']}** — {incident_label}")
                st.caption(f"Department: {row['department']}")
                st.caption(f"Started: {row['started_at']}")
                st.write(row["description"])

with tab_service:
    service_df = incident_df[incident_df["incident_type"] == "SERVICE"].copy()

    if service_df.empty:
        st.info("No service-level incidents recorded.")
    else:
        st.dataframe(
            service_df[
                [
                    "hostname",
                    "department",
                    "service_name",
                    "port_number",
                    "status",
                    "started_at",
                    "resolved_at",
                    "description",
                    "resolution",
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

with tab_all:
    if incident_df.empty:
        st.info("No incidents recorded.")
    else:
        st.dataframe(
            incident_df[
                [
                    "hostname",
                    "department",
                    "incident_type",
                    "service_name",
                    "port_number",
                    "status",
                    "started_at",
                    "resolved_at",
                    "description",
                    "resolution",
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

st.divider()


# ─────────────────────────────────────────
# RESPONSE TIME HISTORY
# ─────────────────────────────────────────

st.subheader("Response Time History")

if history_df.empty:
    st.info("No response-time data yet.")
else:
    online_history = history_df[history_df["is_online"] == True].copy()

    if online_history.empty:
        st.info("No online response-time data available yet.")
    else:
        online_history["checked_at"] = pd.to_datetime(online_history["checked_at"])

        pivot = online_history.pivot_table(
            index="checked_at",
            columns="hostname",
            values="response_ms"
        )

        st.line_chart(pivot, use_container_width=True)

st.caption("Dashboard refreshes every 30 seconds. Use the button below to manually refresh cached data.")

if st.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()
```

