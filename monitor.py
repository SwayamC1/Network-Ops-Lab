# ============================================================
# Meridian Solutions | Network Operations Monitor
# File: monitor.py
# Description: Pings all hosts and checks key service ports
#              every 60 seconds. Logs results to SQL Server.
#              Auto-creates and resolves incidents.
# Author: Swayam Chopra | UMBC MIS 2026
# ============================================================

import os
import time
import socket
import pyodbc
import platform
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

# ─────────────────────────────────────────
# PORT DEFINITIONS PER HOST
# Maps hostname → list of (port, service_name) to check
# ─────────────────────────────────────────

HOST_PORTS = {
    "Meridian-Router": [(22, "SSH")],
    "IT-Admin-PC":     [(3389, "RDP")],
    "Finance-PC":      [(3389, "RDP")],
    "Ops-PC":          [(3389, "RDP")],
    "Server":          [(80, "HTTP"), (443, "HTTPS"), (1433, "SQL Server")],
    "Guest-PC":        [(80, "HTTP")],
}

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
    """Ping a host once. Returns (is_online, response_ms)."""
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
        return (True, elapsed_ms) if result.returncode == 0 else (False, None)
    except subprocess.TimeoutExpired:
        return False, None


# ─────────────────────────────────────────
# PORT CHECK FUNCTION
# ─────────────────────────────────────────

def check_port(ip: str, port: int, timeout: float = 2.0) -> bool:
    """
    Attempt a TCP connection to ip:port.
    Returns True if the port is open, False otherwise.
    This checks whether the SERVICE is running, not just if the host is alive.
    """
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


# ─────────────────────────────────────────
# LOGGING FUNCTIONS
# ─────────────────────────────────────────

def log_result(conn, host_id: int, is_online: bool,
               response_ms: int | None, notes: str | None = None):
    """Write one ping result to uptime_log."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO uptime_log (host_id, checked_at, is_online, response_ms, notes)
        VALUES (?, GETDATE(), ?, ?, ?)
        """,
        (host_id, 1 if is_online else 0, response_ms, notes)
    )
    conn.commit()


def open_incident(conn, host_id: int, hostname: str):
    """Create a new incident when a host goes offline."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM incidents WHERE host_id = ? AND resolved_at IS NULL",
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
# MAIN MONITOR LOOP
# ─────────────────────────────────────────

def run_monitor(interval_seconds: int = 60):
    print("=" * 55)
    print("  Meridian Solutions — Network Operations Monitor")
    print(f"  Polling every {interval_seconds} seconds | Ctrl+C to stop")
    print("=" * 55)

    while True:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT host_id, hostname, ip_address FROM hosts WHERE is_active = 1"
            )
            hosts = cursor.fetchall()

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{timestamp}] Checking {len(hosts)} hosts...\n")
            print(f"  {'Hostname':<20} {'IP':<18} {'Ping':<10} {'ms':<8} {'Ports'}")
            print(f"  {'-'*20} {'-'*18} {'-'*10} {'-'*8} {'-'*30}")

            for host in hosts:
                host_id, hostname, ip = host

                # ── ICMP Ping ──────────────────────────────
                is_online, response_ms = ping_host(ip)
                ping_status = "Online" if is_online else "OFFLINE"
                ms_display  = f"{response_ms}ms" if response_ms else "---"

                # ── Port Checks ────────────────────────────
                port_results = []
                port_notes   = []
                ports_to_check = HOST_PORTS.get(hostname, [])

                for port, service in ports_to_check:
                    is_open = check_port(ip, port) if is_online else False
                    status  = "✅" if is_open else "❌"
                    port_results.append(f"{service}({port}):{status}")
                    if not is_open and is_online:
                        port_notes.append(f"{service} port {port} closed")

                ports_display = "  ".join(port_results) if port_results else "—"
                notes = ", ".join(port_notes) if port_notes else None

                print(f"  {hostname:<20} {ip:<18} {ping_status:<10} {ms_display:<8} {ports_display}")

                # ── Log to SQL Server ──────────────────────
                log_result(conn, host_id, is_online, response_ms, notes)

                if not is_online:
                    open_incident(conn, host_id, hostname)
                else:
                    resolve_incident(conn, host_id, hostname)

            conn.close()

        except Exception as e:
            print(f"\n  ❌ Error: {e}")

        time.sleep(interval_seconds)


if __name__ == "__main__":
    run_monitor(interval_seconds=60)
