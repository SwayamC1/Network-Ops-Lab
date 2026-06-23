```python
# ============================================================
# Meridian Solutions | Network Operations Monitor
# File: monitor.py
# Description: Pings all hosts and checks key service ports
#              every 60 seconds. Logs results to SQL Server.
#              Auto-creates and resolves host and service incidents.
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
    "IT-Admin-PC": [(3389, "RDP")],
    "Finance-PC": [(3389, "RDP")],
    "Ops-PC": [(3389, "RDP")],
    "Server": [(80, "HTTP"), (443, "HTTPS"), (1433, "SQL Server")],
    "Guest-PC": [(80, "HTTP")],
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
    This checks whether the service is reachable, not just whether the host is alive.
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
    """Write one monitoring result to uptime_log."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO uptime_log (host_id, checked_at, is_online, response_ms, notes)
        VALUES (?, GETDATE(), ?, ?, ?)
        """,
        (host_id, 1 if is_online else 0, response_ms, notes)
    )
    conn.commit()


def open_host_incident(conn, host_id: int, hostname: str):
    """Create a host-down incident if one is not already open."""
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM incidents
        WHERE host_id = ?
          AND incident_type = 'HOST'
          AND resolved_at IS NULL
        """,
        (host_id,)
    )

    if cursor.fetchone()[0] == 0:
        description = f"HOST DOWN: {hostname} is not responding to ping."

        cursor.execute(
            """
            INSERT INTO incidents
                (host_id, incident_type, service_name, port_number,
                 started_at, description)
            VALUES
                (?, 'HOST', NULL, NULL, GETDATE(), ?)
            """,
            (host_id, description)
        )

        conn.commit()
        print(f"  ⚠️  Host incident opened: {hostname}")


def resolve_host_incident(conn, host_id: int, hostname: str):
    """Resolve an open host-down incident when the host comes back online."""
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE incidents
        SET resolved_at = GETDATE(),
            resolution = ?
        WHERE host_id = ?
          AND incident_type = 'HOST'
          AND resolved_at IS NULL
        """,
        (
            f"{hostname} resumed responding to ping. Auto-resolved by monitor.",
            host_id
        )
    )

    if cursor.rowcount > 0:
        conn.commit()
        print(f"  ✅  Host incident resolved: {hostname}")


def open_service_incident(conn, host_id: int, hostname: str,
                          service_name: str, port_number: int):
    """Create a service-down incident if one is not already open."""
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM incidents
        WHERE host_id = ?
          AND incident_type = 'SERVICE'
          AND service_name = ?
          AND port_number = ?
          AND resolved_at IS NULL
        """,
        (host_id, service_name, port_number)
    )

    if cursor.fetchone()[0] == 0:
        description = (
            f"SERVICE DOWN: {service_name} port {port_number} "
            f"is closed on {hostname}."
        )

        cursor.execute(
            """
            INSERT INTO incidents
                (host_id, incident_type, service_name, port_number,
                 started_at, description)
            VALUES
                (?, 'SERVICE', ?, ?, GETDATE(), ?)
            """,
            (host_id, service_name, port_number, description)
        )

        conn.commit()
        print(f"  ⚠️  Service incident opened: {hostname} {service_name}({port_number})")


def resolve_service_incident(conn, host_id: int, hostname: str,
                             service_name: str, port_number: int):
    """Resolve an open service incident when the port becomes reachable again."""
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE incidents
        SET resolved_at = GETDATE(),
            resolution = ?
        WHERE host_id = ?
          AND incident_type = 'SERVICE'
          AND service_name = ?
          AND port_number = ?
          AND resolved_at IS NULL
        """,
        (
            f"{service_name} port {port_number} on {hostname} is reachable again. "
            "Auto-resolved by monitor.",
            host_id,
            service_name,
            port_number
        )
    )

    if cursor.rowcount > 0:
        conn.commit()
        print(f"  ✅  Service incident resolved: {hostname} {service_name}({port_number})")


# ─────────────────────────────────────────
# INCIDENT HANDLING
# ─────────────────────────────────────────

def handle_host_incident(conn, host_id: int, hostname: str, is_online: bool):
    """Open or resolve host-level incidents."""
    if is_online:
        resolve_host_incident(conn, host_id, hostname)
    else:
        open_host_incident(conn, host_id, hostname)


def handle_service_incident(conn, host_id: int, hostname: str,
                            service_name: str, port_number: int, is_open: bool):
    """Open or resolve service-level incidents."""
    if is_open:
        resolve_service_incident(conn, host_id, hostname, service_name, port_number)
    else:
        open_service_incident(conn, host_id, hostname, service_name, port_number)


# ─────────────────────────────────────────
# MAIN MONITOR LOOP
# ─────────────────────────────────────────

def run_monitor(interval_seconds: int = 60):
    print("=" * 70)
    print("  Meridian Solutions — Network Operations Monitor")
    print(f"  Polling every {interval_seconds} seconds | Ctrl+C to stop")
    print("=" * 70)

    while True:
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT host_id, hostname, ip_address
                FROM hosts
                WHERE is_active = 1
                ORDER BY host_id
                """
            )

            hosts = cursor.fetchall()

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{timestamp}] Checking {len(hosts)} hosts...\n")
            print(f"  {'Hostname':<20} {'IP':<18} {'Ping':<10} {'ms':<8} {'Ports'}")
            print(f"  {'-'*20} {'-'*18} {'-'*10} {'-'*8} {'-'*45}")

            for host in hosts:
                host_id, hostname, ip = host

                # ── ICMP Ping ──────────────────────────────
                is_online, response_ms = ping_host(ip)
                ping_status = "Online" if is_online else "OFFLINE"
                ms_display = f"{response_ms}ms" if response_ms is not None else "---"

                handle_host_incident(conn, host_id, hostname, is_online)

                # ── TCP Port Checks ────────────────────────
                port_results = []
                port_notes = []
                ports_to_check = HOST_PORTS.get(hostname, [])

                for port_number, service_name in ports_to_check:
                    # Only check services if the host responds to ping.
                    # If the host is offline, the host-down incident already covers it.
                    is_open = check_port(ip, port_number) if is_online else False

                    status = "✅" if is_open else "❌"
                    port_results.append(f"{service_name}({port_number}):{status}")

                    if is_online:
                        handle_service_incident(
                            conn,
                            host_id,
                            hostname,
                            service_name,
                            port_number,
                            is_open
                        )

                        if not is_open:
                            port_notes.append(f"{service_name} port {port_number} closed")

                ports_display = "  ".join(port_results) if port_results else "—"
                notes = ", ".join(port_notes) if port_notes else None

                print(
                    f"  {hostname:<20} {ip:<18} "
                    f"{ping_status:<10} {ms_display:<8} {ports_display}"
                )

                log_result(conn, host_id, is_online, response_ms, notes)

            conn.close()

        except KeyboardInterrupt:
            print("\nMonitor stopped by user.")
            break

        except Exception as e:
            print(f"\n  ❌ Error: {e}")

        time.sleep(interval_seconds)


if __name__ == "__main__":
    run_monitor(interval_seconds=60)
```


