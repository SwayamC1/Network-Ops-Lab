\# Meridian Solutions — IP Addressing Plan



\## Network Overview

\*\*Organization:\*\* Meridian Solutions (fictional 25-person company)  

\*\*Design:\*\* VLAN-segmented network with inter-VLAN routing (router-on-a-stick)  

\*\*Router:\*\* Cisco ISR 4331 (Meridian-Router)  

\*\*Switches:\*\* Cisco 2960-24TT x2 (Dept-Switch, Server-Switch)



\---



\## VLAN Table



| VLAN | Name             | Subnet           | Gateway        | Purpose                        |

|------|------------------|------------------|----------------|--------------------------------|

| 10   | IT-Admin         | 192.168.10.0/24  | 192.168.10.1   | IT Administration staff        |

| 20   | Finance          | 192.168.20.0/24  | 192.168.20.1   | Finance department             |

| 30   | Operations       | 192.168.30.0/24  | 192.168.30.1   | Operations department          |

| 40   | Servers          | 192.168.40.0/24  | 192.168.40.1   | Internal servers (isolated)    |

| 50   | Guest            | 192.168.50.0/24  | 192.168.50.1   | Guest WiFi (restricted access) |



\---



\## Host Assignments



| Hostname         | IP Address      | VLAN | Department        | Switch Port  |

|------------------|-----------------|------|-------------------|--------------|

| Meridian-Router  | 192.168.10.1    | 10   | IT Administration | —            |

| IT-Admin-PC      | 192.168.10.10   | 10   | IT Administration | Fa0/2        |

| Finance-PC       | 192.168.20.10   | 20   | Finance           | Fa0/3        |

| Ops-PC           | 192.168.30.10   | 30   | Operations        | Fa0/4        |

| Guest-PC         | 192.168.50.10   | 50   | Guest             | Fa0/5        |

| Server           | 192.168.40.10   | 40   | Servers           | Fa0/2 (Server-Switch) |



\---



\## Trunk Ports



| Device       | Port       | Mode  | VLANs Carried     |

|--------------|------------|-------|-------------------|

| Dept-Switch  | Gig0/1     | Trunk | 1, 10, 20, 30, 50 |

| Server-Switch| Gig0/1     | Trunk | 1, 40             |



\---



\## Access Control List



\*\*ACL Name:\*\* BLOCK-GUEST  

\*\*Applied to:\*\* GigabitEthernet0/0/0.50 (Guest sub-interface), inbound  



| Rule | Action | Source              | Destination         | Purpose                        |

|------|--------|---------------------|---------------------|--------------------------------|

| 1    | DENY   | 192.168.50.0/24     | 192.168.40.0/24     | Block Guest from Server VLAN   |

| 2    | PERMIT | any                 | any                 | Allow all other traffic        |



\---



\## Subnet Summary



All subnets use /24 (255.255.255.0), providing 254 usable host addresses per VLAN.  

This gives Meridian Solutions room to grow each department to 254 devices before requiring a redesign.

