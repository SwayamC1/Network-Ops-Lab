# ============================================================
# Meridian Solutions | Network Operations Monitor
# File: monitor.py
# Description: Pings all hosts every 60 seconds and logs
#              results to SQL Server. Auto-creates incidents
#              when a host goes offline.
# Author: Swayam Chopra
# ============================================================

import os
import time
import struct
import socket
import pyodbc
import platform
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

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


# ─────────────────────────────────────────
# PING FUNCTION
# ─────────────────────────────────────────

def ping_host(ip: str) -> tuple[bool, int | None]:
    """
    Ping a host once. Returns (is_online, response_ms).
    Works on both Windows and Linux.
    """
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "1", "-w", "1000", ip]

    start = time.time()
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3
        )
        elapsed_ms = int((time.time() - start) * 1000)
        if result.returncode == 0:
            return True, elapsed_ms
        else:
            return False, None
    except subprocess.TimeoutExpired:
        return False, None


# ─────────────────────────────────────────
# LOGGING FUNCTIONS
# ─────────────────────────────────────────

def log_result(conn, host_id: int, is_online: bool, response_ms: int | None):
    """Write one ping result to uptime_log."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO uptime_log (host_id, checked_at, is_online, response_ms)
        VALUES (?, GETDATE(), ?, ?)
        """,
        (host_id, 1 if is_online else 0, response_ms)
    )
    conn.commit()


def open_incident(conn, host_id: int, hostname: str):
    """Create a new incident when a host goes offline."""
    cursor = conn.cursor()
    # Only open if no existing open incident for this host
    cursor.execute(
        """
        SELECT COUNT(*) FROM incidents
        WHERE host_id = ? AND resolved_at IS NULL
        """,
        (host_id,)
    )
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            """
            INSERT INTO incidents (host_id, started_at, description)
            VALUES (?, GETDATE(), ?)
            """,
            (host_id, f"{hostname} is not responding to ping.")
        )
        conn.commit()
        print(f"  ⚠️  Incident opened for {hostname}")


def resolve_incident(conn, host_id: int, hostname: str):
    """Close any open incident when a host comes back online."""
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE incidents
        SET resolved_at = GETDATE(),
            resolution  = 'Host resumed responding to ping. Auto-resolved.'
        WHERE host_id = ? AND resolved_at IS NULL
        """,
        (host_id,)
    )
    if cursor.rowcount > 0:
        conn.commit()
        print(f"  ✅  Incident resolved for {hostname}")


# ─────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────

def run_monitor(interval_seconds: int = 60):
    print("=" * 50)
    print("  Meridian Network Monitor — Starting")
    print(f"  Polling every {interval_seconds} seconds")
    print("  Press Ctrl+C to stop")
    print("=" * 50)

    while True:
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Get all active hosts
            cursor.execute(
                "SELECT host_id, hostname, ip_address FROM hosts WHERE is_active = 1"
            )
            hosts = cursor.fetchall()

            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking {len(hosts)} hosts...")

            for host in hosts:
                host_id, hostname, ip = host
                is_online, response_ms = ping_host(ip)

                status = f"{'Online' if is_online else 'OFFLINE'}"
                ms     = f"{response_ms}ms" if response_ms else "---"
                print(f"  {hostname:<20} {ip:<16} {status:<10} {ms}")

                log_result(conn, host_id, is_online, response_ms)

                if not is_online:
                    open_incident(conn, host_id, hostname)
                else:
                    resolve_incident(conn, host_id, hostname)

            conn.close()

        except Exception as e:
            print(f"  ❌ Error: {e}")

        time.sleep(interval_seconds)


if __name__ == "__main__":
    run_monitor(interval_seconds=60)