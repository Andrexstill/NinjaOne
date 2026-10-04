# NinjaOne for Industrial Environments — Phase 1: Business Model

**Project:** NinjaOne OT/IT Segmentation Lab — Business Case & Reference Architecture
**Document status:** v1.0 — CLOSED 2026-10-01 (scope decisions in §0)
**Classification:** INTERNAL. References pre-release product work and named opportunities.
**Depends on:** Phase 0 — Voice-of-Customer & Evidence Inventory (signals referenced as S-xx)
**Convention:** figures marked **[A]** are assumptions to be validated with Sales Ops / Finance; figures marked **[E]** are evidence from Phase 0 or public NinjaOne material.

---

## 0. Scope decisions (closed 2026-10-01)

| # | Decision | Rationale |
|---|---|---|
| D-1 | **Lab scope is PLCs and SCADA, plus the IDMZ components required to govern them.** No new PXE/provisioning profiles will be built as part of this case study; the existing provisioning platform is reused as-is. | Keep the case study focused on the OT question the field is asking (connectivity and posture per zone), not on provisioning. |
| D-2 | **plc01 and plc02 are ITAM unmanaged devices**, fed from the IDMZ host via Modbus and `ninjarmm-cli unmanaged-set`. Never agented, never routed. | Core demo trigger; answers S-06 and S-07. |
| D-3 | **SCADA01 follows Variant A as the primary path**: NinjaOne agent installed, egress exclusively through a customer-supplied HTTP proxy on the IDMZ host (JUMP01); no default route to the internet. | Answers the connectivity question in S-01/S-02/S-03/S-08; mirrors real deployments on SCADA servers; enables patch/remote/compliance metrics. |
| D-4 | **Variant B is the documented starting state, not a parallel architecture**: SCADA01 exists first as *unmanaged, monitorable*, fed by the same IDMZ observer; installing the agent transitions the same record to *managed*. | Zero extra work; shows the path for customers whose OT team has not yet authorized an agent. |
| D-5 | **Proxy is customer-supplied today (Squid with NinjaOne-domain allowlist), positioned as upgradeable to NinjaOne Proxy.** NinjaOne Airgap is internal roadmap context only. | Matches Product guidance in S-02/S-03; avoids overpromising. |
| D-6 | **No Backup agent on SCADA01** (unsupported via proxy). SCADA project files export to an IDMZ share that is backed up. | Honest limitation, documented workaround. |

## 1. The thesis in one paragraph

Industrial organizations do not need another OT security tool; they already buy Claroty, Nozomi or Dragos for that. What they lack is **IT-grade lifecycle management for everything that surrounds the process** — the domain controllers, provisioning servers, engineering workstations, historians, jump hosts and supervisory servers that sit in Purdue Levels 2 to 5 — delivered in a way that **respects IEC 62443 zone boundaries instead of fighting them**. NinjaOne is positioned to own that layer: one tenant, one console, one DMZ egress per site, no per-plant management infrastructure, and a clear, defensible statement of where the agent does and does not go. The lab proves the model works; this document describes the business built on it.

---

## 2. Market framing

### 2.1 Where the money is

| Signal | Evidence |
|---|---|
| Manufacturing is the most attacked industry, close to a quarter of attacks worldwide | ninjaone.com Manufacturing page **[E]** |
| Enterprise OT device populations are large: BMW alone scoped 85,000 OT devices for patching with ~200,000 further devices as potential | S-08 **[E]** |
| A single MSP with 50,000 endpoints is asking for OT architecture guidance | S-01 **[E]** |
| Hertz-scale enterprises spend US$0.5M → US$1.3M/year on endpoint management as fleets grow | Confluence discovery notes, Sep 2026 **[E]** |
| Federal and utility buyers mandate on-prem or air-gapped shapes | S-11, water-treatment deployments **[E]** |

### 2.2 Why now

1. **Regulation.** NIS2 (EU, in force), IEC 62443 adoption, and US water-sector cybersecurity mandates push plant operators to inventory and patch what they can — and to document what they cannot.
2. **IT/OT convergence is organizational, not just technical.** The Head of IT is increasingly accountable for plant-floor Windows/Linux estates (JSW persona **[E]**), but has no OT-aware tooling.
3. **Incumbent fatigue.** BMW wants off Ivanti; VA wants off BigFix; FedRAMP prospects want off Lansweeper **[E]**. Replacement cycles are open.
4. **NinjaOne's own roadmap.** Proxy (alpha → beta) and Airgap (EA build) are the two components that unlock the connectivity objection. A reference architecture prepared now lands when they ship.

### 2.3 What NinjaOne is *not* selling

Explicitly out of scope — and saying so is part of the value proposition:

- Agents on PLCs, RTUs, drives, safety systems, or any Level 0–1 device.
- Deep-packet OT protocol inspection or anomaly detection (Claroty/Nozomi/Dragos territory).
- Replacement of SCADA, historian, or engineering tooling.

---

## 3. Segments and personas

### 3.1 Target segments (ranked)

| Rank | Segment | Why | Entry product | Evidence |
|---|---|---|---|---|
| 1 | **Mid-market manufacturers** (1–10 plants, lean IT, Head of IT owns plant Windows estate) | Fastest sales cycle; IT already buys RMM; OT estate is mostly Windows/Linux on Level 2–3 | Endpoint Management + Patch + Remote | JSW Steel Italy **[E]** |
| 2 | **MSPs and system integrators serving industrial clients** | Multiplier; they already run the agent on SCADA hosts; need a defensible architecture to sell | Partner tenant + reference architecture | DeLamar Mining, two WTPs via integrators, 50K MSP **[E]** |
| 3 | **Utilities and municipal infrastructure** (water, wastewater, mining) | Regulatory pressure, small IT teams, SCADA on Windows | Endpoint Management + ITAM unmanaged devices | Kent County WTP, Idaho Springs WTP **[E]** |
| 4 | **Enterprise manufacturers with strict no-internet policy** | Largest deals, longest cycle; gated on Proxy/Airgap availability | Enterprise + Proxy/Airgap (roadmap) | BMW **[E]** |
| 5 | **Federal / regulated** | Requires FedRAMP + air-gap shapes; defer until Airgap positioning is confirmed | FedRAMP tenant + Airgap mode C/D | NASA, VA, S-06 **[E]** |

### 3.2 Buying committee

| Persona | Role in deal | What they care about | What the lab shows them |
|---|---|---|---|
| **Head of IT / IT Director** | Economic buyer | One console for office and plant; fewer tools; audit evidence | JSW-style unified visibility; patch compliance across zones |
| **OT / Plant Manager / Automation Lead** | Veto holder | Nothing touches the process; no downtime; who can reach Level 2 | Zone table showing no agent below Level 2; `docker stop plc01` detected from the DMZ without any OT-side software |
| **CISO / Security Architect** | Gatekeeper | IEC 62443 conduits, single egress, identity, logging | Firewall/route matrix; outbound-only 443 from the IDMZ; MFA, RBAC, IP allowlisting; audit trail |
| **Compliance / Internal Audit** | Influencer | Inventory completeness, patch evidence, documented exceptions | Unmanaged-device records for PLCs; patch reports per zone |
| **MSP owner / Service Delivery Manager** | Buyer (segment 2) | Margin, repeatability, defensibility to client's OT team | Reproducible architecture; per-site deployment runbook |

---

## 4. Value proposition by zone

The product does the same things everywhere; the *posture* changes per zone. This is the core of the pitch.

| Zone / Purdue level | What NinjaOne does | What NinjaOne deliberately does not do | Products involved |
|---|---|---|---|
| **Enterprise Zone (L4–5)** | Full lifecycle: zero-touch provisioning, AD integration, patching, policies, software deployment, remote, backup, ticketing | — | Endpoint Mgmt, Patch, Remote, Backup, Ticketing, Documentation |
| **Industrial DMZ (L3.5)** | Hosts the agent and the single egress path (proxy today; Airgap mode A roadmap); runs observers (Modbus/OPC-UA/ICMP/service checks) that feed custom fields, conditions and alerts; jump host for controlled access to L2 | Does not forward OT protocols to the cloud; does not open inbound paths | Endpoint Mgmt, Scripting/Automation, Custom Fields, Conditions, Remote |
| **Site Operations (L3)** | Historian/Grafana hosts managed as servers via the IDMZ; patch windows aligned to production schedule | Does not read process data for its own purposes | Endpoint Mgmt, Patch |
| **Supervisory Control (L2)** | Starts as *unmanaged, monitorable* record fed by the IDMZ observer (D-4); once authorized, agent installed with egress exclusively via the IDMZ proxy (D-3); maintenance windows gated on process state | No direct internet; no Backup agent (Backup not supported via proxy — project files exported to IDMZ share instead) | ITAM unmanaged devices → Endpoint Mgmt, Patch, Remote |
| **Basic Control / Process (L0–1)** | Documented as unmanaged devices with Modbus-derived health written to custom fields from the IDMZ | **Never agented. Never routed.** | ITAM unmanaged devices, Custom Fields |

**One-line version for slides:** *Manage Levels 3.5–5 like IT. Observe Level 2. Document Level 0–1. Never touch the process.*

---

## 5. Value drivers and lab-measurable metrics

Every claim below has a corresponding measurement in the lab (Phase 3) so the case study reports numbers, not adjectives.

| Value driver | Customer pain | Lab metric | Target | Public benchmark |
|---|---|---|---|---|
| **Faster detection of supervisory/controller outages from the IT console** | OT incidents discovered by operators, not IT; no ticket trail | Time from `docker stop plc01` to NinjaOne alert and ticket | < 2 min **[A]** | JSW: anomalies detected before production impact **[E]** |
| **Transition from agentless to managed without re-architecture** | OT team authorizes agents late; tooling must not require redesign | Same SCADA01 record moves from *unmanaged, monitorable* to *managed*; history and custom fields preserved | Demonstrated | — |
| **Patch compliance across zones without production risk** | Patching deferred for years on plant hosts | Patch window on SCADA01 executes only when process state = READY/IDLE; compliance report by zone | 100% of L2–L4 hosts in policy **[A]** | NinjaOne: 90% faster patching **[E, public]**; JSW: hours vs weeks **[E]** |
| **Single inventory of IT and OT assets** | Spreadsheets, Lansweeper, no owner for PLC records | % of lab devices (agented + unmanaged) present in one console | 100% | S-06 FedRAMP replacement **[E]** |
| **No onsite visits for L2–L4 troubleshooting** | Travel to plants for routine fixes | Remote sessions to SCADA01 via IDMZ jump without RDP exposure | Demonstrated | JSW: zero onsite visits **[E]** |
| **No per-plant management infrastructure** | On-prem tools require servers at every site | Infrastructure footprint per site | 1 dual-homed IDMZ host | BMW objection (Tom Molden) **[E]** |
| **Audit-ready segmentation evidence** | Cannot prove to auditors where tooling reaches | Exported route/firewall matrix + conduit table | Delivered as artifact | IEC 62443-3-2 |

---

## 6. Competitive positioning

### 6.1 Map

| Competitor | Category | Strength | Where NinjaOne wins | Where NinjaOne must be honest |
|---|---|---|---|---|
| **ondeso** | OT-specific endpoint/patch management, on-prem | Built for plant floor; offline-first | Single console for IT + OT governance; no per-site servers; modern automation | Offline/air-gap today requires customer proxy; Airgap not GA |
| **Ivanti** (incumbent, hybrid promised) | Enterprise UEM | Installed base | Simplicity, time-to-value, cloud-native; incumbent fatigue is real (S-08) | Hybrid shape not yet available |
| **ManageEngine on-prem** | UEM on-prem | Can sit inside the plant | TCO of operating and patching the management tool itself | Some buyers mandate on-prem regardless |
| **Lansweeper** | Asset inventory incl. agentless OT | Discovery depth | ITAM unmanaged devices + NMS + patching in one platform; FedRAMP | Passive OT discovery depth is lower |
| **BigFix** | Legacy enterprise patching | Scale, air-gap heritage | Zero-infrastructure SaaS; faster deployment | Air-gap parity depends on Airgap |
| **Claroty / Nozomi / Dragos** | OT security (visibility, threat detection) | Gartner MQ leaders | **Not competitors.** Coexistence: they discover and detect; NinjaOne remediates and manages the IT-managed layer | Integration story must be built (future) |

### 6.2 Positioning statement

> For IT leaders accountable for plant-floor systems, NinjaOne is the unified endpoint management platform that governs the Windows and Linux estate around industrial processes — provisioning, patching, monitoring and documenting across Purdue Levels 2 to 5 — without placing anything in the control layer and without opening the plant to the internet. Unlike OT-specialist on-premise tools, it needs no per-plant infrastructure; unlike generic RMM, it ships with a published IEC 62443-aligned reference architecture.

---

## 7. Objection handling matrix

| # | Objection (verbatim style) | Who says it | Response | Lab evidence |
|---|---|---|---|---|
| O-1 | "A cloud tool has no business in my plant." | OT Manager | Correct. It lives in the IDMZ and above. Here is the route table showing plant networks have no path to it. | `OT-SW` host adapter with TCP/IP disabled; `ot-field` internal network; conduit matrix |
| O-2 | "Our OT levels can't reach the internet." | CISO, BMW, MSP | They don't need to. One egress host in the IDMZ (proxy). Plant hosts talk to the IDMZ only. | JUMP01 as sole egress; SCADA01 agent via proxy (Variant A) |
| O-3 | "You'll want to install an agent on the PLC." | Automation Lead | Never. PLCs are unmanaged-device records with Modbus-derived health written from the IDMZ. | plc01/plc02 as unmanaged devices with custom fields |
| O-4 | "Patching will break production." | Plant Manager | Patch windows are gated on process state and production calendar; staged rollout; rollback plan. | Maintenance window on SCADA01 gated on PLC state via custom field condition |
| O-5 | "What about backup of the SCADA server?" | IT | Backup agent is not supported via proxy. SCADA project files export to an IDMZ share that is backed up. State it, don't hide it. | Rapid SCADA project export job → JUMP01 share → Backup |
| O-6 | "Our SCADA runs on Windows 7 / old Linux." | IT, OT | Supported OS list is explicit. Legacy hosts are inventoried as unmanaged devices and isolated; Airgap roadmap targets legacy OS. | Unmanaged device workflow |
| O-7 | "We'd need an on-prem instance per plant." | Enterprise IT (BMW) | One tenant, one IDMZ host per site. Compare footprint with ondeso/ManageEngine per-site servers. | Lab: single JUMP01 serves all zones |
| O-8 | "Who can reach Level 2 and how is it logged?" | CISO, Audit | Access only via the IDMZ jump host; MFA, RBAC, IP allowlisting on the tenant; session logging. | Remote session path demonstrated; activity log export |
| O-9 | "Can you demo the air-gapped shape?" | AE (S-04) | We demo the architecture Airgap targets, with the proxy path that exists today; Airgap positioned as roadmap. | Lab Variant A/B; Airgap modes table |

---

## 8. Business model canvas

| Block | Content |
|---|---|
| **Customer segments** | Mid-market manufacturers; industrial MSPs/integrators; utilities; enterprise manufacturers (gated on Proxy/Airgap); federal (deferred) |
| **Value propositions** | IT-grade lifecycle for Levels 3.5–5; observation of Level 2; documentation of Level 0–1; no per-plant infrastructure; IEC 62443-aligned reference architecture; audit-ready evidence |
| **Channels** | Direct enterprise; MSP partner program; integrator co-sell (SCADA integrators already deploying the agent); content: reference architecture, lab video, customer stories |
| **Customer relationships** | SE-led architecture workshop (using the lab); onboarding runbook per site; CSM review of zone compliance |
| **Revenue streams** | Per-endpoint subscription for agented devices (L2–L5) **[A: existing pricing]**; ITAM/unmanaged-device records **[A: confirm licensing model, S-06 asked this]**; add-ons: Patch, Backup (L4/IDMZ), Remote, Ticketing, Documentation; future: Proxy/Airgap packaging **[A: TBD by Product]** |
| **Key resources** | Agent + cloud platform; Proxy (alpha) and Airgap (EA); the lab as reference implementation; SE enablement content; IEC 62443 architecture collateral |
| **Key activities** | Publish reference architecture; enable SEs/AEs on OT vocabulary; pilot Proxy with willing customers (S-02 customer volunteered); feed Product with lab-derived requirements |
| **Key partners** | SCADA/automation integrators; OT security vendors (coexistence/integration); Microsoft (WSUS/patch path in isolated segments); Zebra-style OEM relationships for rugged endpoints |
| **Cost structure** | Standard SaaS COGS; incremental: SE enablement, lab maintenance, Proxy/Airgap engineering, OT-vertical marketing |

---

## 9. Illustrative TCO comparison (per-site view)

All numbers are **[A] placeholders** for Finance/Sales Ops to replace. The structure is the point: the on-prem alternative carries infrastructure and operations cost at *every* site.

| Cost component (per plant, 3-year) | On-prem OT tool (ondeso / ManageEngine pattern) | NinjaOne |
|---|---|---|
| Management server(s) hardware/VM | Required per site | None (IDMZ host is customer's existing jump host) |
| Management software licenses | Per-site server + per-device | Per-device subscription |
| Patching and securing the management tool | Customer responsibility | Vendor responsibility (SaaS) |
| Database/backup of management tool | Customer | Vendor |
| Multi-site console consolidation | Additional tier or manual | Native (one tenant) |
| Staff time for tool operations | Hours/week per site **[A]** | Minutes/week per tenant **[A]** |
| Proxy/egress host | Often also required | Required (IDMZ) |

**Narrative for the deck:** the BMW requirement (85K devices) would have implied a management footprint at every plant and partition. NinjaOne's model is one tenant plus one egress host per site. Finance should quantify the delta using NinjaOne's internal pricing and the IDC Business Value study (Doc #US54520326, June 2026) **[E]**.

---

## 10. Go-to-market motions enabled by the lab

| Motion | Audience | Asset from the lab |
|---|---|---|
| **Architecture workshop** (90 min) | Prospect's IT + OT + Security | Zone/conduit diagram; live demo; objection matrix |
| **MSP/integrator enablement** | Partners already deploying on SCADA hosts | Reproducible lab build; per-site runbook; sanitized reference architecture |
| **Deal support template** | AEs facing S-01-style questions | Pre-written architecture response + diagram (closes the gap Brian Melville's answer left) |
| **Product pilot pipeline** | Customers volunteering for Proxy (S-02) | Lab as pre-flight for proxy/egress validation |
| **Content** | Marketing | Public reference architecture page (currently absent from ninjaone.com); lab walkthrough video; JSW story cross-link |

---

## 11. Risks and dependencies

| Risk | Impact | Mitigation |
|---|---|---|
| Airgap status ambiguity (Slack vs Confluence) | Overpromising to customers | Internal-only positioning until James Hoscheit / Product confirm; external deck mentions "roadmap" generically |
| Proxy remains alpha | Enterprise no-internet deals stay blocked | Reference architecture supports customer-supplied proxy today; Proxy is an upgrade path |
| Backup via proxy unsupported | Objection O-5 | Documented workaround; raise as product feedback |
| OT teams reject any IT tool near Level 2 | Deal veto | Variant B (agentless L2) always offered; OT persona addressed first in workshop |
| Lab perceived as toy (Docker PLCs) | Credibility | Position as IEC 62443 reference implementation; offer CODESYS runtime variant; emphasize real Modbus and real segmentation |

---

## 12. Success criteria for the business case

By the end of Phase 4 the lab must have produced:

1. Measured values for every metric in Section 5.
2. A reference architecture (Phase 2) that an AE can attach to an S-01-style request without SE involvement.
3. A recorded 8–10 minute demo.
4. A product feedback document with at least five lab-validated requirements traceable to Phase 0 signals.
5. Sign-off from one Product Manager (Proxy or Airgap) that the lab is a valid pre-flight environment.

---

## 13. Next phase

**Phase 2 — Reference Architecture "NinjaOne for Industrial Environments (IEC 62443-aligned)":** zone and conduit model, flow matrix (allowed/denied), three deployment variants (full-cloud with IDMZ; restricted segment via proxy; agentless/unmanaged), identity and access model, logging and audit, and the explicit "what we do not do" section. Diagrams in Mermaid for the Markdown deliverable and exportable for slides.

*End of Phase 1.*
