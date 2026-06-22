# Meridian Solutions — Troubleshooting Log

---

## Incident 1 — IT-Admin-PC: 100% Packet Loss to All Destinations

**Date:** 2026-06-16
**Severity:** High
**Affected host:** IT-Admin-PC (192.168.10.10)
**Detection:** Manual ping test during initial network verification

### Symptoms

* IT-Admin-PC had 100% packet loss to all destinations
* Could not reach default gateway `192.168.10.1`
* Could not reach Finance-PC `192.168.20.10`
* Could not reach Server `192.168.40.10`
* All other hosts on Dept-Switch were reachable and working normally

### Diagnosis

Ran `show ip interface brief` on Meridian-Router and confirmed that all router interfaces and subinterfaces were up with the correct IP addresses. This confirmed the router was not the cause of the issue.

Ran `show vlan brief` on Dept-Switch and found that IT-Admin-PC was physically connected to `Fa0/2`, but the port was assigned to VLAN 40 (Servers) instead of VLAN 10 (IT-Admin).

### Root Cause

During initial switch configuration, a console session reset mid-configuration. The VLAN assignment for `Fa0/2` was saved incorrectly as VLAN 40 instead of VLAN 10, placing IT-Admin-PC in the wrong network segment.

### Fix

Reassigned the access port connected to IT-Admin-PC back to VLAN 10.

```bash
enable
configure terminal
interface FastEthernet0/2
switchport mode access
switchport access vlan 10
no shutdown
end
write memory
```

### Validation

After correcting the VLAN assignment, I re-ran connectivity tests from IT-Admin-PC.

Validation checks completed:

* Ping to default gateway `192.168.10.1` succeeded
* Ping to Finance-PC `192.168.20.10` succeeded
* Ping to Server `192.168.40.10` succeeded
* `show vlan brief` confirmed `Fa0/2` was assigned to VLAN 10
* Other Dept-Switch hosts remained unaffected

**Time to resolve:** 15 minutes
**Status:** Resolved ✅

---

## Incident 2 — Guest-PC Blocked from Server (ACL Verification)

**Date:** 2026-06-16
**Severity:** Informational
**Purpose:** Verify ACL `BLOCK-GUEST` is enforcing the Guest VLAN to Server VLAN restriction

### Test

From Guest-PC command prompt, tested two destinations:

* `ping 192.168.40.10` — Server, should be blocked by ACL
* `ping 192.168.20.10` — Finance-PC, should be allowed

### Expected Result

Guest-PC should not be able to reach the Server VLAN because guest users should not have access to internal server resources. Guest-PC should still be able to reach allowed department VLANs.

### Results

Guest-PC to Server test:

```text
Pinging 192.168.40.10 with 32 bytes of data:
Reply from 192.168.50.1: Destination host unreachable.
Reply from 192.168.50.1: Destination host unreachable.
Reply from 192.168.50.1: Destination host unreachable.
Reply from 192.168.50.1: Destination host unreachable.

Packets: Sent = 4, Received = 0, Lost = 4 (100% loss)
```

Guest-PC to Finance-PC test:

```text
Pinging 192.168.20.10 with 32 bytes of data:
Reply from 192.168.20.10: bytes=32 time<1ms TTL=127
Reply from 192.168.20.10: bytes=32 time<1ms TTL=127
Reply from 192.168.20.10: bytes=32 time<1ms TTL=127
Reply from 192.168.20.10: bytes=32 time<1ms TTL=127

Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)
```

### Conclusion

ACL `BLOCK-GUEST` is working as designed. Guest users cannot reach the Server VLAN, but they can still reach allowed department VLANs. The security policy is enforced correctly at the router subinterface level.

**Status:** Verified ✅

---

## Incident 3 — Server Offline During Maintenance Window

**Date:** 2026-06-16
**Severity:** Medium
**Affected host:** Server (192.168.40.10)
**Detection:** Python monitor auto-opened incident after failed ping checks

### Symptoms

* Python monitor logged Server as offline for approximately 2 hours
* Incident was automatically created in the SQL Server `incidents` table
* Server showed as unavailable in monitoring results
* All other hosts remained online during the outage

### Diagnosis

Checked Server-Switch port assignment and confirmed `Fa0/2` was correctly assigned to VLAN 40.

Checked Meridian-Router interface `GigabitEthernet0/0/1` and confirmed it was up with the correct gateway IP address `192.168.40.1`.

Confirmed the Server was intentionally taken offline for a scheduled maintenance window. The monitoring script was not notified in advance, so it correctly detected the outage but treated the planned downtime as an incident.

### Root Cause

No maintenance notification process existed. The monitoring script correctly detected the outage, but there was no process to distinguish planned maintenance from unplanned downtime.

### Fix

No network configuration change was required. The Server came back online after maintenance completed, and the Python monitor automatically resolved the incident on the next successful ping cycle.

Added a maintenance notification step to the monitoring process so planned outages can be documented before maintenance begins.

### Validation

Confirmed the Server returned online after the maintenance window and the Python monitor automatically resolved the incident.

Validation checks completed:

* Server responded successfully to ping after maintenance
* Server-Switch `Fa0/2` remained assigned to VLAN 40
* Router interface `GigabitEthernet0/0/1` stayed up with gateway IP `192.168.40.1`
* SQL Server `incidents` table showed the incident had a populated `resolved_at` timestamp
* Incident resolution note confirmed the host resumed responding to ping
* Dashboard no longer showed the Server as an open incident

**Time to resolve:** 2 hours (planned maintenance window)
**Status:** Resolved ✅



