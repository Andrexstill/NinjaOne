# NinjaOne for Industrial Environments — Phase 0: Voice-of-Customer & Evidence Inventory

**Project:** NinjaOne OT/IT Segmentation Lab — Business Case & Reference Architecture
**Document status:** Working inventory, v0.1 — 2026-10-01
**Classification:** INTERNAL. Contains references to pre-release product work and named customer opportunities. Do not distribute outside NinjaOne without sanitizing Sections 2, 3 and 5.
**Author:** Andres (Sales Engineering) with research assistance
**Sources:** NinjaOne Slack (public and private channels the author has access to), Confluence (EP, MDM spaces), ninjaone.com public pages. Observation window: Apr 2024 – Sep 2026.

---

## 1. Purpose of this document

Before building a business model and reference architecture around the OT lab, we need to prove that the problem the lab solves is one the field is actually asking about. This inventory collects every internal signal found about operational technology (OT), SCADA/PLC, air-gapped and plant-floor environments, classifies it, and extracts the recurring questions, objections and competitors.

The output feeds Phase 1 (business model), Phase 2 (reference architecture) and the Product Feedback deliverable.

---

## 2. Executive summary of findings

1. **Demand is real, recurring and unanswered.** Between Apr 2025 and Sep 2026 at least **nine distinct field requests** about OT, SCADA or air-gapped segments were raised in Slack. None received a reusable architecture answer; most received "it works like any other environment" or a link to the proxy KB article.
2. **The gating question is always the same:** *how does the agent reach the cloud from a segment that is not allowed to talk to the internet?* Every OT conversation collapses into connectivity (proxy, relay, air-gap), not into features.
3. **The largest opportunity in the dataset was lost on exactly that point.** BMW (85,000 OT devices for patching, ~200,000 additional devices as expansion potential) went to OT-specialist tooling because NinjaOne could not offer an on-premise relay/proxy shape in time.
4. **NinjaOne already has customers running the agent on SCADA servers** (mining, water treatment) and a published manufacturing story (JSW Steel Italy) claiming office-IT plus plant-floor OT visibility. The capability exists; the *architectural guidance* does not.
5. **A product answer is in flight but is not GA.** "NinjaOne Airgap (formerly Relay)" is an Enterprise Architecture build with three operating modes that map one-to-one onto Purdue/IEC 62443 zone boundaries. A separate first-party **Proxy** is in alpha/pre-beta. Status statements across Slack and Confluence conflict and must be verified with the owning PM before any external use.
6. **Public positioning has a gap.** ninjaone.com has a Manufacturing vertical page (with Porsche, Siemens, Hyundai, Mitsubishi Motors logos) but no content about OT segmentation, Purdue levels, or how NinjaOne coexists with IEC 62443 zone-and-conduit designs. Competitors in this space lead with exactly that content.

**Implication for the lab:** the lab is the missing artifact. It demonstrates, in a reproducible environment, the architecture the field cannot currently articulate, and it gives Product a concrete testbed for Airgap/Proxy.

---

## 3. Field signals — deal and prospect inventory

| # | Date | Channel | Who raised it | Customer / context | What they asked | Internal answer given | Gap exposed |
|---|---|---|---|---|---|---|---|
| S-01 | 2026-09-09 | #emea-ae-csm-pss-se | Carla Bruno (AE) | Large MSP, ~50K endpoints | Architecture docs showing NinjaOne monitoring/patching OT; guidance for OT levels that cannot reach the internet; validation of a **proxy at Purdue Level 4**; security considerations on flows, access and identity | "No different from any other environment"; proxy supported; 2FA, IP allowlisting, RBAC | No reference architecture, no Purdue-aware guidance, no statement on which levels the agent should and should not live in |
| S-02 | 2026-05-27 | #product-management | David Madaan | Existing customer, client with OT security mandate; Windows workstations on an internet-isolated segment | Keep RMM connectivity through "a proxy of some sort" | Proxy KB + patch caching KB; first-party Proxy (alpha) offered by PM Reed Woods; customer requested a call | Customer willing to pilot a proxy product; no standard shape to deploy |
| S-03 | 2026-05-11 | #ae-questions | Ryan Falla | Customer deploying security controls via dual-homed on-prem intermediary (one NIC isolated, one NIC internet) | Does NinjaOne support this architecture; requirements and limitations | Yes via proxy; **NinjaOne Backup does not work through a proxy**; own proxy in alpha | Documented limitation: Backup is the exception; dual-homed intermediary is exactly the lab's JUMP01 pattern |
| S-04 | 2026-09-08 | #ae-questions | Ryan Falla; Lionel Merkel | Request to demo Relay; separate "pretty big" deal with air-gapped WSUS chain | Can Relay be demoed; can NinjaOne patch without direct Microsoft Update access via Relay as proxy | Relay has no web-app UI, all manual, "not really demo-able"; **no**, devices still need a device-level proxy to Microsoft update services | Patching path in isolated segments remains dependent on upstream proxy; demo gap |
| S-05 | 2026-08-07 | #product-management | Raul Bernal | Customer asking for setup details for Relay on air-gapped devices | What does it take to set up | Thread escalated (7 replies) | Dojo text advertises a capability Sales cannot fulfil |
| S-06 | 2026-06-09 | #ae-questions | Katie Bobbin | FedRAMP prospect replacing Lansweeper; OT equipment with no agent and no SNMP | Document agentless OT devices; licensing | ITAM available in FedRAMP; create **unmanaged devices** | Viable answer exists; not framed as an OT asset-inventory story |
| S-07 | 2026-04-23 | #ae-questions | Ryan Falla | Prospect | Export network diagrams including OT devices, connectivity type, critical dependencies; tag assets as **critical IT / critical OT** | No answer in channel | Feature gap: OT asset classification and topology |
| S-08 | 2025-09 → 2026-01 | #bmw-onpremise-opp-85000-devices-relais-server | Sascha Kabalawi, Stefan Jooss, Tom Molden | **BMW** — 85,000 OT devices, patching only, "on-premise-like" setup; ~200,000 further devices as potential | Relay/proxy server in production; no direct device-to-internet connections allowed; no capacity to deploy production proxies themselves | Requirements largely met *except* connectivity; competitors: **ondeso** (OT-specific), **Ivanti** hybrid (unreleased), **ManageEngine** on-prem; Claroty referenced as Gartner MQ OT leader | Loss driver was deployment shape, not features. Internal consensus: co-develop a relay shape that is resellable across industries |
| S-09 | 2025-04-22 | #ae-questions | Andrew Lehmann | Generic | "Can we work with SCADA/OT networks?" | — | Baseline enablement gap for AEs |
| S-10 | 2025-01-08 | #backup-demo-questions | Tommaso Bastoni | Generic | Does NinjaOne Backup cover SCADA devices | — | Backup positioning for Level 2/3 hosts unclear |
| S-11 | 2024-04-24 | #sdr-questions-for-sales-engineers | Brandon Stiers | NASA / US Federal | Federal agencies require on-prem tooling because of air-gapped or SCADA environments | "Nothing we can do today" | Historic; shows the request predates Relay by two years |

**Observed existing deployments on supervisory hosts (from agent-log requests in #qa-agent-logs):**

| Customer / partner | Device name pattern | Sector | Purdue level implied |
|---|---|---|---|
| Core Information Technologies / DeLamar Mining Company (USA) | `DEL-SCADA-02 — SCADA Server (Backup)` | Mining | Level 2–3 |
| Kent County Levy Court / WTP | `WTP-DT-… / MFabres SCADA` | Water treatment (municipal) | Level 2 |
| Browns Hill Engineering & Controls / Idaho Springs WTP | `IDAHOSPWTP-VMD — vmSCADA` | Water treatment (integrator-managed) | Level 2 |

These prove the agent is already in production on SCADA servers through MSP/integrator channels, including a backup SCADA server and a virtualized SCADA host. They are the proof points for the "Level 2 managed via DMZ" pattern the lab will demonstrate.

---

## 4. Published proof: JSW Steel Italy customer story (Aug 2026)

- Industry: Manufacturing (steel). Part of JSW Group, Fortune Global 2000; parent is a top-15 global steel producer.
- Persona: Head of IT (Marco Bruni).
- Products: Autonomous Patch Management, Endpoint Management, Remote, Ticketing, SentinelOne integration.
- Headline outcomes (paraphrased from the internal announcement): complete endpoint visibility spanning office IT and production OT; critical patches now deployed in hours rather than weeks; remote troubleshooting removed the need for onsite technician visits; early detection of storage, service and performance anomalies before they affect production.
- Assets: ninjaone.com customer story (EN/IT), Highspot items (EN/IT), Airtable quote library.

**How the lab uses it:** JSW is the "it works" proof. The lab supplies the "here is *how* it works without breaking segmentation" layer that the story does not explain.

---

## 5. Product state relevant to OT (verify before external use)

| Capability | Status as found | Source | Owner / contact | Relevance to lab |
|---|---|---|---|---|
| Agent over customer-supplied HTTP proxy | GA, documented in Dojo | KB 115001285923 | — | Primary supported path for Level 2/3 hosts today |
| Patch caching | GA, documented | KB 30624563717133 | — | Reduces egress from plant networks |
| NinjaOne Backup through proxy | **Not supported** | S-03 (Reed Woods) | Backup PM | Must be stated honestly in architecture; Backup lives in Level 4/DMZ only |
| First-party **Proxy** | Alpha → pre-beta (May–Sep 2026); not integrated in web app | S-02, S-03, Relay thread | Reed Woods (PM) | Candidate to run on JUMP01 as the DMZ egress point |
| **NinjaOne Airgap (formerly Relay)** | Enterprise Architecture build; Confluence page updated 2026-07-31; Slack (May 2026) says prototype for a specific contract, "would not offer it", "no long-term plans"; Dojo text to be removed | Confluence EP page 6301941972; #tech-nexus thread | James Hoscheit (EA) | Three modes map directly onto IEC 62443 conduits (see §7). Treat as **internal roadmap context only** |
| Unmanaged devices (ITAM) | GA, incl. FedRAMP | S-06 | — | Vehicle for documenting PLCs, HMIs, drives as assets without agents |
| Critical IT / critical OT asset tagging, topology export | Not available | S-07 | — | Product feedback item |

### 5.1 NinjaOne Airgap — operating modes (from Confluence, internal)

| Mode | Connectivity | Customer-facing shape | Purdue/IEC 62443 fit |
|---|---|---|---|
| A — `ninjaone_bridged` | Two-way cloud sync | Bridged, fully connected | Relay in Level 3.5 DMZ; devices in Level 2/3 appear in NinjaOne console |
| B — `one_way` | Diode-out only | Bundle pair over one-way guard | Strict conduit from Level 3 → DMZ with no return path |
| C — `air_gap` | None | Standalone console on-site | Fully isolated plant; audit via syslog TCP+TLS |
| D-conn / D-iso | Sneakernet bundles | Bundle pair by courier | Regulated sites (defence, utilities) |

Agent-to-relay is mutual TLS on 8443; operator console 8444; bundle import 9443. Supports Solaris/AIX/BSD/embedded Linux, i.e. the legacy OS population typical of Level 2/3. Includes SCAP compliance (OpenSCAP, DISA SCC), hash-chained audit log, FIPS build, CAC/PIV. A scoped-but-unbuilt item is an HTTP forward proxy inside the relay (deny-by-default).

**Caution:** the Slack and Confluence statements about Airgap's future conflict. The lab's deliverables must position it as "roadmap context the lab can help validate", never as a sellable component, until Product confirms.

---

## 6. Recurring questions, objections and competitors

### 6.1 Questions the field keeps asking (ranked by frequency)

1. How does the agent reach NinjaOne from a segment with no internet? (S-01, S-02, S-03, S-04, S-05, S-08, S-11)
2. Can NinjaOne be used safely in OT at all — is there an architecture document? (S-01, S-09)
3. How do we patch Windows hosts in isolated segments, including WSUS-chained ones? (S-04, S-08)
4. How do we inventory OT devices that cannot take an agent or SNMP? (S-06, S-07)
5. Does Backup cover SCADA hosts / work through a proxy? (S-03, S-10)
6. Which identity and access controls apply? (S-01)

### 6.2 Objections to pre-empt

| Objection | Source | Response the lab must demonstrate |
|---|---|---|
| "Cloud RMM has no place below the DMZ." | Implicit in S-01, S-08 | Agreed. NinjaOne lives in Level 4 and the Level 3.5 DMZ; Level 0–2 is observed, never agented. Show the firewall/route table. |
| "Our OT levels cannot reach the internet." | S-01, S-02, S-08 | Single egress point in the DMZ (proxy today, relay/Airgap tomorrow); plant networks have no default route. Demonstrate with `OT-SW` having no host TCP/IP binding. |
| "Legacy OS on the plant floor." | S-01 (Brian Melville), Airgap OS list | Honest statement of supported OS; unmanaged-device inventory for the rest; Airgap roadmap for Solaris/AIX/legacy Linux. |
| "You'll need an on-prem instance per plant." | S-08 (Tom Molden) | One tenant, one DMZ egress per site, no per-plant server farm. Cost comparison vs ondeso/ManageEngine on-prem. |
| "Backup for SCADA?" | S-03, S-10 | Backup agent on Level 4/DMZ hosts only; SCADA project files exported to a DMZ share and backed up from there. |
| "Can't demo Relay." | S-04 | The lab *can* demo the architecture Relay targets, with the proxy path that exists today. |

### 6.3 Competitive landscape observed

| Competitor | Where seen | Positioning | NinjaOne counter |
|---|---|---|---|
| ondeso | BMW | OT-specific asset management and patching; on-premise | Single console for IT + OT governance; no per-site infrastructure |
| Ivanti (hybrid, unreleased) | BMW | Incumbent; promised hybrid | Modern, cloud-native, lower operational overhead; incumbent fatigue acknowledged by Tom Molden |
| ManageEngine on-prem | BMW | On-prem alternative | TCO of running and patching the management tool itself |
| Lansweeper | S-06 | Agentless inventory incl. OT | ITAM unmanaged devices + NMS in one platform; FedRAMP |
| Claroty | BMW channel (Gartner MQ reference) | OT visibility/security leader | Not a competitor; a coexistence/integration story (Claroty discovers, NinjaOne remediates the IT-managed layer) |
| BigFix | VA RFI | Legacy enterprise patching | Zero-infrastructure SaaS |

---

## 7. Nomenclature decision: standards-aligned zone model for the lab

Deliverables will use **IEC 62443-3-2 zones and conduits** mapped to **Purdue Enterprise Reference Architecture (ISA-95) levels**. This is the vocabulary OT customers, auditors and OT-security vendors (Claroty, Nozomi, Dragos) already use, and it is what the S-01 prospect used ("Level 4").

| Zone (IEC 62443) | Purdue level | Lab realization | NinjaOne posture |
|---|---|---|---|
| **Enterprise Zone** | Level 4–5 | `NAT-SW` 10.10.10.0/24 — DC01, DEPLOY01, provisioned Windows/Linux endpoints; NinjaOne Cloud | Full agent: patching, policies, zero-touch provisioning (existing PXE/API platform) |
| **Industrial DMZ (IDMZ)** | Level 3.5 | JUMP01 — dual-homed 10.10.10.124 / 10.10.30.2 | Agent + egress point (proxy today, Airgap mode A as roadmap); Modbus/OPC-UA observers; historian + Grafana publication |
| **Site Operations Zone** | Level 3 | `ot-historian` 172.30.3.0/24 (PostgreSQL/Grafana, planned) | Managed via IDMZ; read-only consumers of process data |
| **Supervisory Control Zone** | Level 2 | SCADA01 (Rapid SCADA 6.5) on `OT-SW` 10.10.30.0/24; `ot-scada` 172.30.2.0/24 | Two variants to be demonstrated: (A) agent egressing only via IDMZ proxy; (B) agentless, observed from IDMZ, documented as unmanaged device |
| **Basic Control / Process Zone** | Level 0–1 | `ot-field` 172.30.0.0/24 (internal) — plc01, plc02 (OpenPLC v4) | **Never agented.** Observed indirectly (Modbus from IDMZ). Documented as unmanaged devices |

Conduits to be documented explicitly in Phase 2: IDMZ → Level 2 (Modbus 502/5020 read-only), Level 2 → Level 0–1 (Modbus), IDMZ → Cloud (HTTPS 443 outbound only), Enterprise → IDMZ (SSH/RDP jump only). Nothing from Enterprise reaches Level 2 or below directly; nothing below Level 3.5 has a route to the internet.

---

## 8. What this means for the business case (input to Phase 1)

- **Primary segment:** mid-market and enterprise manufacturers, utilities (water, mining), and the MSPs/integrators serving them. Evidence: JSW, DeLamar, two WTPs, BMW, 50K-endpoint MSP.
- **Core value proposition:** *govern everything around the process without touching the process.* IT-grade lifecycle management for Levels 3.5–5 and supervisory hosts, respecting IEC 62443 boundaries.
- **Value drivers with lab-measurable metrics:** time to detect a controller outage from the IT console; time to provision an AD-joined supervisory server (existing `adonly` profile); patch window execution on Level 2 host with process state gating; single-pane inventory of IT + OT assets.
- **Honest limits to state up front:** no agent below Level 2; Backup not through proxy; legacy OS coverage; Airgap not GA.
- **Product feedback to carry:** OT asset tagging and topology (S-07); Backup via proxy (S-03); patching in WSUS-chained isolated segments (S-04); a demoable relay/proxy (S-04, S-08); public Purdue/IEC 62443 architecture content.

---

## 9. Open items before Phase 1

1. Confirm with Reed Woods (Proxy) and James Hoscheit (Airgap) what may be referenced in internal vs external versions of the deliverables.
2. Pull the BMW requirements document (shared in channel by Sascha Kabalawi, 2025-09-17) to extract concrete requirement language for the reference architecture.
3. Retrieve JSW Steel Italy Highspot asset and Airtable quotes for approved external wording.
4. Optional: query Salesforce for open opportunities tagged Manufacturing / Utilities / Energy to size the pipeline exposed to the connectivity objection.

---

*End of Phase 0 inventory.*
