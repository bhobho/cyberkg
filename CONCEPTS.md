# Cybersecurity Attack Knowledge Graph — Concept Walkthrough

This document explains **what** the application does, **why** each piece exists, and **how** the code implements it — written for someone new to cybersecurity and graph databases.

---

## Table of Contents

1. [The Core Problem](#1-the-core-problem)
2. [What is a Knowledge Graph?](#2-what-is-a-knowledge-graph)
3. [The Four Building Blocks](#3-the-four-building-blocks)
4. [How Attacks Actually Work (the Kill Chain)](#4-how-attacks-actually-work-the-kill-chain)
5. [The Data Model](#5-the-data-model)
6. [Real-World Example: WannaCry](#6-real-world-example-wannacry)
7. [How the Database Works (Neo4j + Cypher)](#7-how-the-database-works-neo4j--cypher)
8. [How the Backend Works (FastAPI)](#8-how-the-backend-works-fastapi)
9. [How the Frontend Works (React + Force Graph)](#9-how-the-frontend-works-react--force-graph)
10. [The Three Queries Explained](#10-the-three-queries-explained)
11. [Data Sources: MITRE ATT&CK and NVD](#11-data-sources-mitre-attck-and-nvd)
12. [How All Layers Connect](#12-how-all-layers-connect)
13. [Extending the Project](#13-extending-the-project)

---

## 1. The Core Problem

Imagine you are a security analyst responsible for 50 servers. A new ransomware strain is reported in the news. You need to answer:

- **Does this ransomware target any of my systems?**
- **Which of my servers are most at risk, and why?**
- **What vulnerabilities does it exploit — and have I patched them?**

Traditional approaches store this information in spreadsheets or siloed databases. To answer the question above, you would manually cross-reference three or four separate sources. This takes time — time attackers do not give you.

A **Knowledge Graph** solves this by storing everything — malware, techniques, CVEs, assets — as a connected network. The answer to "can WannaCry reach my Active Directory server?" becomes a single graph traversal query that completes in milliseconds.

---

## 2. What is a Knowledge Graph?

A knowledge graph is a way of storing information as **nodes** (things) and **edges** (relationships between things).

### Regular database (table)

| malware_name | exploits_cve    |
|-------------|-----------------|
| WannaCry    | CVE-2017-0144   |
| WannaCry    | CVE-2021-34527  |

This tells you what WannaCry exploits — but to find *which servers are at risk* you need to join three more tables.

### Knowledge graph

```
(WannaCry) --[USES_TECHNIQUE]--> (Exploit Public-Facing App)
                                          |
                                  [EXPLOITS]
                                          |
                                  (CVE-2017-0144)
                                          |
                                    [AFFECTS]
                                          |
                               (Windows Server 2019)
```

Now you can ask: *"Starting from WannaCry, follow edges, find all assets reachable within 3 hops."* The graph does the join automatically.

### Why graphs are natural for security

Cyberattacks **are** graphs. An attacker moves from tool → technique → vulnerability → system. Modelling this as a graph means your queries match how attacks actually happen.

---

## 3. The Four Building Blocks

This application has exactly four node types. Understanding them is the foundation for everything else.

---

### Malware

A piece of malicious software. Each malware family has a characteristic set of behaviours.

| Property | Example | Meaning |
|----------|---------|---------|
| `id` | MAL-001 | Internal identifier |
| `name` | WannaCry | Common name |
| `type` | Ransomware | Category (Trojan, Wiper, Botnet, RAT, Loader…) |
| `description` | Ransomware worm… | What it does |

**Examples in this project:** WannaCry, NotPetya, Emotet, Cobalt Strike, Mirai, BlackCat, Lazarus Loader.

---

### Technique (TTP — Tactics, Techniques, and Procedures)

A **technique** is a *method* an attacker uses, independent of any specific tool. The same technique can be used by dozens of different malware families.

| Property | Example | Meaning |
|----------|---------|---------|
| `id` | T1190 | MITRE ATT&CK ID |
| `name` | Exploit Public-Facing Application | What the attacker does |
| `tactic` | Initial Access | Which phase of the attack |
| `description` | Exploit weakness… | How it works |

**Why separate from malware?** Because knowing the *technique* lets you defend against it regardless of which malware uses it. If you block T1190 (exploiting public services), you partially mitigate WannaCry, NotPetya, and dozens of others at once.

**Tactic phases (from MITRE ATT&CK):**

```
Reconnaissance → Initial Access → Execution → Persistence
→ Privilege Escalation → Defense Evasion → Credential Access
→ Discovery → Lateral Movement → Collection → Command & Control
→ Exfiltration → Impact
```

---

### CVE (Common Vulnerabilities and Exposures)

A CVE is a specific, catalogued software flaw. When a technique like "exploit public-facing application" is used against a specific product, there is almost always a CVE number assigned to that flaw.

| Property | Example | Meaning |
|----------|---------|---------|
| `id` | CVE-2017-0144 | Unique ID (year + sequence number) |
| `cvss` | 9.3 | Severity score 0–10 |
| `description` | EternalBlue SMBv1 RCE… | What the flaw is |

**CVSS Score ranges:**

| Score | Severity | Meaning |
|-------|----------|---------|
| 9.0–10.0 | Critical | Remotely exploitable, no authentication needed |
| 7.0–8.9  | High | Significant damage possible |
| 4.0–6.9  | Medium | Requires some conditions |
| 0.1–3.9  | Low | Limited impact |

---

### Asset

An asset is a system, device, or service that an organisation owns and wants to protect.

| Property | Example | Meaning |
|----------|---------|---------|
| `id` | ASSET-001 | Internal identifier |
| `name` | Windows Server 2019 | Human-readable name |
| `type` | Server | Category (Server, Endpoint, IoT, WebServer…) |
| `os` | Windows | Operating system |

Assets are the *target* — the thing an attacker ultimately wants to compromise.

---

## 4. How Attacks Actually Work (the Kill Chain)

A real cyberattack follows a chain of steps. This application models that chain directly.

```
┌─────────────┐    uses     ┌───────────────┐    exploits    ┌──────────────┐    affects    ┌──────────┐
│   Malware   │ ──────────► │   Technique   │ ─────────────► │     CVE      │ ─────────────► │  Asset   │
└─────────────┘             └───────────────┘                └──────────────┘                └──────────┘
  WannaCry            Exploit Public-Facing App          CVE-2017-0144              Windows Server 2019
```

Reading left to right: *WannaCry uses the technique of exploiting public-facing applications, specifically by exploiting CVE-2017-0144 (EternalBlue), which affects Windows Server 2019.*

There is also a direct shortcut edge:

```
┌─────────────┐   targets   ┌──────────┐
│   Malware   │ ──────────► │  Asset   │
└─────────────┘             └──────────┘
```

This captures cases where a malware family is known to target a specific asset type without a specific CVE chain being documented.

### Why four hops matter

When you query "what can reach my Active Directory server?", the graph engine follows edges backwards:

```
Asset ← affects ← CVE ← exploits ← Technique ← uses ← Malware
```

It returns every malware that has a path to that asset — in one query, across the entire dataset.

---

## 5. The Data Model

Here is the complete schema — every node type, property, and relationship in the graph.

```
╔══════════════╗         USES_TECHNIQUE        ╔═══════════════╗
║   Malware    ║ ─────────────────────────────► ║   Technique   ║
║──────────────║                                ║───────────────║
║ id           ║                                ║ id  (T####)   ║
║ name         ║                                ║ name          ║
║ type         ║         TARGETS                ║ tactic        ║
║ description  ║ ──────────────────────────┐    ║ description   ║
╚══════════════╝                           │    ╚═══════════════╝
                                           │            │
                                           │       EXPLOITS
                                           │            │
                                           │            ▼
                                           │    ╔═══════════════╗
                                           │    ║     CVE       ║
                                           │    ║───────────────║
                                           │    ║ id            ║
                                           │    ║ cvss          ║
                                           │    ║ description   ║
                                           │    ╚═══════════════╝
                                           │            │
                                           │        AFFECTS
                                           │            │
                                           │            ▼
                                           │    ╔═══════════════╗
                                           └───►║    Asset      ║
                                                ║───────────────║
                                                ║ id            ║
                                                ║ name          ║
                                                ║ type          ║
                                                ║ os            ║
                                                ╚═══════════════╝
```

### Relationship summary

| Relationship | From → To | Meaning |
|---|---|---|
| `USES_TECHNIQUE` | Malware → Technique | This malware employs this attack method |
| `EXPLOITS` | Technique → CVE | This technique leverages this specific flaw |
| `AFFECTS` | CVE → Asset | This flaw exists in this asset/system |
| `TARGETS` | Malware → Asset | This malware is known to target this asset type |

---

## 6. Real-World Example: WannaCry

WannaCry is a ransomware worm that caused billions of dollars of damage in 2017. Let's trace its path through the graph.

### Step 1 — Initial Access
WannaCry uses technique **T1190 (Exploit Public-Facing Application)**.  
It scans the internet for Windows machines with port 445 (SMB) open.

### Step 2 — The Vulnerability
T1190 in this context exploits **CVE-2017-0144**, nicknamed "EternalBlue".  
EternalBlue is a flaw in Windows SMBv1 (file sharing protocol). CVSS score: **9.3 (Critical)**.  
A remote attacker can send a specially crafted packet and gain full code execution — no password needed.

### Step 3 — Encryption (Impact)
WannaCry also uses **T1486 (Data Encrypted for Impact)** — it encrypts all files on the victim machine and demands a ransom in Bitcoin.

### Step 4 — Lateral Movement
Using **T1021 (Remote Services)**, it spreads to other Windows machines on the same network using the same EternalBlue exploit.

### The graph path

```
WannaCry ──[USES_TECHNIQUE]──► T1190 (Exploit Public-Facing App)
                                    │
                              [EXPLOITS]
                                    │
                                    ▼
                             CVE-2017-0144 (EternalBlue, CVSS 9.3)
                                    │
                               [AFFECTS]
                                    │
                                    ▼
                          Windows Server 2019  ◄──[TARGETS]── WannaCry
                          Corporate Workstation ◄──[AFFECTS]──┘
                          Active Directory DC
```

**Query in plain English:** "Show me all attack chains that can reach my Windows Server 2019."
**Graph answer:** WannaCry → T1190 → CVE-2017-0144 → Windows Server 2019. Risk: Critical.

**What this tells a defender:** Patch CVE-2017-0144 (apply MS17-010), disable SMBv1, and block port 445 at the network boundary. Doing so breaks the entire attack chain for WannaCry and NotPetya simultaneously.

---

## 7. How the Database Works (Neo4j + Cypher)

Neo4j stores data natively as nodes and relationships — no tables, no joins. You query it with **Cypher**, a pattern-matching language.

### Cypher basics

**Create a node:**
```cypher
CREATE (m:Malware {id: "MAL-001", name: "WannaCry", type: "Ransomware"})
```

**Create a relationship:**
```cypher
MATCH (m:Malware {id: "MAL-001"}), (t:Technique {id: "T1190"})
CREATE (m)-[:USES_TECHNIQUE]->(t)
```

**Find attack paths to an asset:**
```cypher
MATCH (m:Malware)-[:USES_TECHNIQUE]->(t:Technique)-[:EXPLOITS]->(c:CVE)-[:AFFECTS]->(a:Asset)
WHERE a.name = "Windows Server 2019"
RETURN m.name, t.name, c.id, c.cvss
```

This single query traverses three relationship hops and returns every malware → technique → CVE chain that reaches the target asset. In SQL this would require three JOINs across four tables.

### MERGE vs CREATE

The loader uses `MERGE` instead of `CREATE`:

```cypher
MERGE (m:Malware {id: $id}) SET m += $props
```

`MERGE` means "create if it doesn't exist, otherwise match the existing one." This makes the loader **idempotent** — you can run it multiple times and it will not create duplicate nodes.

### Why Neo4j for this use case

| Feature | Benefit for security graphs |
|---------|----------------------------|
| Native graph storage | No JOIN overhead — traversals are O(edges), not O(table size) |
| Schema-free nodes | Can add new properties (e.g. `last_seen`, `confidence`) without migrations |
| Cypher path queries | `MATCH path = (a)-[*1..4]->(b)` finds all paths up to 4 hops — natural for attack chains |
| Built-in browser UI | Visualise and query the graph at http://localhost:7474 without writing code |

---

## 8. How the Backend Works (FastAPI)

The backend is a Python REST API that sits between Neo4j and the React frontend.

### Request flow

```
Browser                 FastAPI                    Neo4j
  │                        │                          │
  │  GET /api/attack-paths │                          │
  │  ?asset=Windows Server │                          │
  │ ─────────────────────► │                          │
  │                        │  MATCH (m)-[...]->(a)    │
  │                        │  WHERE a.name = $search  │
  │                        │ ───────────────────────► │
  │                        │                          │
  │                        │  [{malware, technique,   │
  │                        │    cve, cvss, ...}]      │
  │                        │ ◄─────────────────────── │
  │                        │                          │
  │  {asset, chains,       │                          │
  │   risk_score}          │                          │
  │ ◄───────────────────── │                          │
```

### Key files

**`database.py`** — Opens one Neo4j driver at startup and reuses it. Opening a connection per request would be slow.

```python
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def run_query(query, params=None):
    with driver.session() as session:
        result = session.run(query, params or {})
        return [record.data() for record in result]
```

**`routes/attack_paths.py`** — The most important query. It matches the full 3-hop path and also computes a risk score from the maximum CVSS found in all chains:

```python
MATCH path = (m:Malware)-[:USES_TECHNIQUE]->(t:Technique)
             -[:EXPLOITS]->(c:CVE)-[:AFFECTS]->(a:Asset)
WHERE toLower(a.name) CONTAINS toLower($search)
RETURN m.name, t.name, t.tactic, c.id, c.cvss
```

**`routes/graph.py`** — Returns all nodes and edges in a format the frontend can render directly:

```json
{
  "nodes": [{"id": "MAL-001", "name": "WannaCry", "color": "#ef4444", ...}],
  "links": [{"source": "MAL-001", "target": "T1190", "type": "USES_TECHNIQUE"}]
}
```

### Why FastAPI

FastAPI auto-generates interactive API documentation at `/docs`. Every endpoint is explorable in a browser without writing any test code — important for learning and debugging.

---

## 9. How the Frontend Works (React + Force Graph)

The frontend has two main jobs: **render the graph** and **run queries**.

### Force-directed layout

`react-force-graph-2d` uses a physics simulation where:
- Nodes **repel** each other (like magnets with the same pole)
- Edges **attract** connected nodes (like springs)
- The simulation runs until nodes settle into a stable layout

This means connected nodes naturally cluster together. Malware nodes that share techniques end up near each other, visually revealing families of related attacks without you having to arrange anything.

### Node colours

| Colour | Type | Why this colour |
|--------|------|-----------------|
| Red `#ef4444` | Malware | Danger — the threat actor |
| Orange `#f97316` | Technique | Warning — the method |
| Yellow `#eab308` | CVE | Caution — the specific flaw |
| Blue `#3b82f6` | Asset | Neutral — your infrastructure |

Red → orange → yellow → blue follows a heat-map intuition: the redder, the closer to the attacker.

### Highlight mechanic

When you run a query, the sidebar calls `onHighlight(ids)` with the IDs of all nodes involved in the result. The graph then:
- Renders highlighted nodes in their normal colour
- Renders all other nodes as dark grey `#2a2d3e`

This lets you instantly see which part of the graph is relevant to your query, while keeping the full context visible.

### Component hierarchy

```
App
├── Header          (title + live stats chips)
├── Sidebar
│   └── SearchPanel
│       ├── AttackPathsTab   (asset dropdown → attack chains)
│       ├── CVETab           (CVE dropdown → malware + assets)
│       └── MalwareTab       (malware dropdown → techniques + CVEs)
└── GraphArea
    └── GraphView
        ├── ForceGraph2D     (the canvas)
        └── NodeDetail       (floating panel on node click)
```

---

## 10. The Three Queries Explained

### Query 1: Attack Paths (asset → malware chains)

**Question:** "Which malware families can reach this asset, and how?"

**Graph traversal:**
```
Asset ←[AFFECTS]← CVE ←[EXPLOITS]← Technique ←[USES_TECHNIQUE]← Malware
```

**What you get back:**
- Each attack chain: Malware name → Technique name → CVE ID
- The CVSS score of each CVE in the chain
- A risk score (Critical / High / Medium / Low) based on the highest CVSS

**Defensive use:** Sort by CVSS. The Critical chains are your highest-priority patches. Breaking any single edge in a chain (patch the CVE, block the technique, detect the malware) disrupts that attack path.

---

### Query 2: CVE Lookup (CVE → malware families + assets)

**Question:** "Log4Shell just dropped. What in my environment uses it and who exploits it?"

**Graph traversal (two directions):**
```
Malware → Technique → CVE   (who exploits this)
CVE → Asset                 (what is affected)
```

**What you get back:**
- CVSS score and description of the CVE
- All malware families that exploit it (via any technique)
- All assets in the graph that have this CVE

**Defensive use:** After a new CVE is published, run this query immediately. The malware list tells you what threat actors to watch for; the asset list tells you what to patch first.

---

### Query 3: Malware Analysis (malware → full profile)

**Question:** "Cobalt Strike was detected on our network. What does it do?"

**Graph traversal:**
```
Malware → [all USES_TECHNIQUE edges] → Techniques
Techniques → [all EXPLOITS edges] → CVEs
Malware → [all TARGETS edges] → Assets
```

**What you get back:**
- All ATT&CK techniques this malware uses, with tactic phase
- All CVEs it can exploit
- All asset types it is known to target

**Defensive use:** The technique list maps directly to defensive controls. T1059 (scripting interpreters) → disable PowerShell for standard users. T1071 (C2 over HTTP) → deploy TLS inspection. Each technique in MITRE ATT&CK has a documented list of mitigations.

---

## 11. Data Sources: MITRE ATT&CK and NVD

### MITRE ATT&CK

Maintained by The MITRE Corporation (a US non-profit). It is a curated, community-driven catalogue of real attacker behaviours observed in production incidents worldwide.

- **Format:** A single JSON file published on GitHub
- **URL:** https://github.com/mitre/cti
- **Contents:** ~700 techniques, ~130 software entries, grouped into 14 tactics
- **Update frequency:** Several times per year as new techniques are documented

The loader fetches this file and upserts every technique into Neo4j. This means the technique nodes in the graph are real, documented attack methods — not made-up examples.

### NVD (National Vulnerability Database)

Maintained by NIST (US National Institute of Standards and Technology). It is the authoritative source for CVE details and CVSS scores.

- **API:** `https://services.nvd.nist.gov/rest/json/cves/2.0`
- **Rate limit:** 5 requests/30 seconds without an API key; 50 requests/30 seconds with one
- **Contents:** CVSS scores, affected product lists, patch references

The loader queries NVD for each CVE in the seed data to get its authoritative CVSS score.

### Seed data (offline fallback)

`ingest/seed_data.py` contains a hand-curated dataset of 7 malware families, 10 techniques, 7 CVEs, and 6 assets with all their relationships. These are all real — WannaCry, EternalBlue, Log4Shell are documented historical incidents.

The seed data loads first and always works offline. MITRE and NVD enrichment runs on top of it if internet access is available.

---

## 12. How All Layers Connect

Here is the complete data flow from database to browser pixel:

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Browser                                     │
│                                                                     │
│  User selects "Windows Server 2019" → clicks "Find Attack Paths"   │
│                          │                                          │
│              React calls fetchAttackPaths("Windows Server 2019")   │
│                          │                                          │
│              axios.get("/api/attack-paths?asset=Windows Server")   │
└──────────────────────────┼──────────────────────────────────────────┘
                           │ HTTP GET (proxied by Vite dev server)
┌──────────────────────────▼──────────────────────────────────────────┐
│                       FastAPI Backend (port 8000)                    │
│                                                                     │
│  routes/attack_paths.py                                             │
│  def get_attack_paths(asset: str):                                  │
│      rows = run_query(CYPHER_QUERY, {"search": asset})              │
│      return { chains, risk_score }                                  │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ Bolt protocol (port 7687)
┌──────────────────────────▼──────────────────────────────────────────┐
│                    Neo4j (Docker container)                          │
│                                                                     │
│  MATCH (m:Malware)-[:USES_TECHNIQUE]->(t:Technique)                 │
│        -[:EXPLOITS]->(c:CVE)-[:AFFECTS]->(a:Asset)                  │
│  WHERE toLower(a.name) CONTAINS "windows server"                    │
│  RETURN m.name, t.name, t.tactic, c.id, c.cvss                     │
│                                                                     │
│  Result: [{malware:"WannaCry", technique:"Exploit...",              │
│            cve:"CVE-2017-0144", cvss:9.3}, ...]                    │
└─────────────────────────────────────────────────────────────────────┘
                           │
                    JSON response
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                     React Frontend                                   │
│                                                                     │
│  SearchPanel renders result cards                                   │
│  calls onHighlight(["MAL-001","T1190","CVE-2017-0144","ASSET-001"]) │
│                                                                     │
│  GraphView dims all non-highlighted nodes                           │
│  The attack chain glows in the canvas                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 13. Extending the Project

Once you are comfortable with the current application, here are well-defined next steps in increasing complexity.

### Level 1 — Add more data (no code changes needed)

Add entries to `ingest/seed_data.py`. The lists and relationship tuples at the bottom of that file are self-explanatory. Add a new malware family, link it to existing techniques, and re-run `python -m ingest.loader`.

### Level 2 — Add a new node type: Threat Actor

Real threat intelligence attributes malware to groups (APT28, Lazarus Group, FIN7). Add a `ThreatActor` node:

```python
# In seed_data.py
THREAT_ACTORS = [
    {"id": "TA-001", "name": "Lazarus Group", "nation": "DPRK"},
]
ACTOR_USES_MALWARE = [("TA-001", "MAL-007")]
```

Then add a new route `GET /api/actors/{name}` that returns the malware family, techniques, and targets associated with that actor.

### Level 3 — Add detection rules

Add a `Detection` node type linked to techniques:

```
(Detection)-[:DETECTS]->(Technique)
```

Populate it with Sigma rules or YARA signatures. Now the query "how do I detect WannaCry?" traverses:
```
Malware → Technique → Detection
```

### Level 4 — Live threat feed ingestion

Replace the static seed loader with a scheduled job that polls:
- **VirusTotal API** — for new malware samples and their IOCs
- **CISA KEV (Known Exploited Vulnerabilities)** — for CVEs actively exploited in the wild
- **MITRE ATT&CK STIX feed** — for new technique additions

Each new entry gets merged into Neo4j. The graph stays current automatically.

### Level 5 — Risk scoring engine

Add a CVSS-weighted path scoring algorithm: multiply CVSS scores along a path to produce an aggregate "attack path risk score". Assets with the highest cumulative scores across all incoming paths are your highest-priority hardening targets.

---

## Summary

| Concept | What it is | Where in code |
|---------|-----------|---------------|
| Knowledge Graph | Data stored as nodes + relationships | Neo4j database |
| Node types | Malware, Technique, CVE, Asset | `seed_data.py`, Neo4j labels |
| Graph schema | USES_TECHNIQUE, EXPLOITS, AFFECTS, TARGETS | `ingest/loader.py` |
| Graph queries | Cypher pattern matching | `routes/*.py` |
| REST API | FastAPI endpoints consumed by React | `main.py` + `routes/` |
| Visualisation | Force-directed physics simulation | `GraphView.jsx` |
| Highlighting | Dimming non-relevant nodes | `GraphView.jsx` + `SearchPanel.jsx` |
| Real data | MITRE ATT&CK + NVD CVE feeds | `ingest/loader.py` |

The central insight of this project: **model the attack, not just the alert**. By connecting malware → technique → CVE → asset, a single graph query answers questions that would otherwise require manual correlation across multiple databases.
