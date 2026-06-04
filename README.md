# Cybersecurity Attack Knowledge Graph

An interactive graph application that visualises relationships between **malware families**, **attack techniques (MITRE ATT&CK)**, **CVE vulnerabilities**, and **target assets** — so you can explore how a real-world cyberattack moves from malware all the way to a compromised system.

```
Malware → Technique (TTP) → CVE → Asset
```

---

## What You Will See

| Node colour | Meaning |
|-------------|---------|
| 🔴 Red      | Malware family (WannaCry, Emotet, …) |
| 🟠 Orange   | ATT&CK Technique (Phishing, Lateral Movement, …) |
| 🟡 Yellow   | CVE vulnerability (Log4Shell, EternalBlue, …) |
| 🔵 Blue     | Asset (Windows Server, Exchange, …) |

Click any node to inspect its properties. Use the left sidebar to run three types of queries:

1. **Attack Paths** — pick an asset; see every malware chain that can reach it and the risk score.
2. **CVE Lookup** — pick a CVE; see which malware exploits it and which assets are exposed.
3. **Malware** — pick a malware family; see its techniques, CVEs, and known targets.

---

## Prerequisites — Install These First

### 1. Docker Desktop
Used to run the Neo4j graph database with one command.

- Download from https://www.docker.com/products/docker-desktop
- After installing, open Docker Desktop and wait until it says **"Engine running"**.

### 2. Python 3.10+
Used to run the backend API.

Check if you already have it:
```bash
python3 --version
```
If not installed, download from https://www.python.org/downloads/

### 3. Node.js 18+
Used to run the frontend.

Check if you already have it:
```bash
node --version
```
If not installed, download from https://nodejs.org/ (choose the LTS version).

---

## Project Structure

```
cyberkg/
├── backend/
│   ├── main.py              ← FastAPI application (the REST API)
│   ├── database.py          ← Neo4j connection helper
│   ├── routes/
│   │   ├── graph.py         ← /api/graph endpoint
│   │   ├── attack_paths.py  ← /api/attack-paths endpoint
│   │   └── vulnerabilities.py ← /api/vulnerabilities endpoint
│   ├── ingest/
│   │   ├── loader.py        ← Script that populates the database
│   │   └── seed_data.py     ← Static data (works offline)
│   ├── requirements.txt     ← Python dependencies
│   └── .env                 ← Database credentials (safe for local use)
├── frontend/
│   ├── src/
│   │   ├── App.jsx          ← Root React component
│   │   ├── components/
│   │   │   ├── GraphView.jsx   ← Force-directed graph canvas
│   │   │   ├── SearchPanel.jsx ← Sidebar with 3 query tabs
│   │   │   └── NodeDetail.jsx  ← Click-to-inspect popup
│   │   └── api/client.js    ← API call helpers
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml       ← Starts Neo4j
└── README.md
```

---

## Step-by-Step Setup

Open **three separate terminal windows** — you will need them all running at the same time.

---

### Terminal 1 — Start the Database

```bash
# Go to the project folder
cd cyberkg

# Start Neo4j (downloads image on first run, ~2 minutes)
docker compose up -d

# Verify it is running — wait for "Started" in the logs
docker compose logs -f neo4j
# Press Ctrl+C to stop watching logs once you see "Started"
```

Neo4j browser UI is now at http://localhost:7474  
Login: `neo4j` / `password123` (you can explore the graph here too)

---

### Terminal 2 — Set Up and Run the Backend

```bash
# Go to the backend folder
cd cyberkg/backend

# Create a Python virtual environment (keeps dependencies isolated)
python3 -m venv venv

# Activate the virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Load data into Neo4j (takes ~30 seconds; fetches live MITRE data if online)
python -m ingest.loader

# Start the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

API documentation (auto-generated, interactive): http://localhost:8000/docs

---

### Terminal 3 — Set Up and Run the Frontend

```bash
# Go to the frontend folder
cd cyberkg/frontend

# Install JavaScript dependencies
npm install

# Start the development server
npm run dev
```

You should see:
```
  ➜  Local:   http://localhost:5173/
```

Open http://localhost:5173 in your browser. The graph will appear.

---

## Using the Application

### Query 1: Find Attack Paths to an Asset
1. Click the **"Attack Paths"** tab in the left sidebar.
2. Select an asset from the dropdown (e.g., "Active Directory DC").
3. Click **"Find Attack Paths"**.
4. The graph highlights all nodes involved in attack chains reaching that asset.
5. The result card shows each chain: Malware → Technique → CVE, with a risk score.

### Query 2: Look Up a CVE
1. Click **"CVE Lookup"**.
2. Select a CVE ID (e.g., CVE-2021-44228 = Log4Shell).
3. Click **"Lookup CVE"**.
4. See the CVSS score, which malware exploits it, and which assets are at risk.

### Query 3: Analyse a Malware Family
1. Click **"Malware"**.
2. Select a malware family (e.g., WannaCry).
3. Click **"Analyze Malware"**.
4. See its ATT&CK techniques, exploited CVEs, and known target asset types.

### Interacting with the Graph
- **Click any node** to see its full property list in the top-right panel.
- **Scroll** to zoom in/out.
- **Drag** nodes to rearrange the layout.
- **Click "Clear highlight"** in the header to reset node colours.

---

## API Reference

Once the backend is running, all endpoints are documented at http://localhost:8000/docs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/graph` | Full graph (nodes + edges) for the visualisation |
| GET | `/api/graph/stats` | Node and edge counts |
| GET | `/api/attack-paths?asset=<name>` | Attack chains targeting an asset |
| GET | `/api/attack-paths/all-assets` | List all assets |
| GET | `/api/vulnerabilities?cve=<id>` | Malware and assets for a CVE |
| GET | `/api/vulnerabilities/list` | All CVEs ordered by CVSS |
| GET | `/api/vulnerabilities/malware` | All malware families |
| GET | `/api/vulnerabilities/malware/<name>` | Techniques and CVEs for one malware |

---

## Data Sources

| Source | What it provides | How loaded |
|--------|------------------|------------|
| `seed_data.py` | 7 malware, 10 techniques, 7 CVEs, 6 assets — curated real-world data | Always loaded, works offline |
| MITRE ATT&CK | Full technique catalogue from https://github.com/mitre/cti | Fetched on first `python -m ingest.loader` run |
| NVD (NIST) | CVSS scores for each CVE | Fetched on first run (rate-limited without API key) |

### Getting an NVD API Key (optional, free)
Without a key, NVD enrichment works but is rate-limited to 5 requests per 30 seconds.
1. Register at https://nvd.nist.gov/developers/request-an-api-key
2. Add your key to `backend/.env`:
   ```
   NVD_API_KEY=your-key-here
   ```
3. Re-run `python -m ingest.loader`

---

## Stopping the Application

```bash
# Stop the API (Terminal 2): Ctrl+C
# Stop the frontend (Terminal 3): Ctrl+C

# Stop Neo4j (Terminal 1):
docker compose down

# To also delete all graph data (start fresh next time):
docker compose down -v
```

---

## Troubleshooting

**"Could not load graph" in the browser**
→ The backend is not running. Go to Terminal 2 and run `uvicorn main:app --reload --port 8000`.

**`python -m ingest.loader` fails with connection error**
→ Neo4j is not ready yet. Wait 30 seconds after `docker compose up -d` and try again.

**`npm install` fails**
→ Make sure Node.js 18+ is installed: `node --version`.

**Graph loads but is empty**
→ The data was not loaded. Run `python -m ingest.loader` in Terminal 2.

**Port 8000 already in use**
→ Another process is using that port. Run `lsof -i :8000` to find it, or change the port:
```bash
uvicorn main:app --reload --port 8001
# Also update vite.config.js proxy target to http://localhost:8001
```

---

## Concepts Explained (for Beginners)

**Knowledge Graph** — A database where information is stored as nodes (things) and edges (relationships between things). Unlike a table, it lets you ask "how are these things connected?" naturally.

**MITRE ATT&CK** — A publicly maintained catalogue of real cyberattack techniques observed in the wild, organised by what stage of an attack they belong to (tactics).

**CVE (Common Vulnerabilities and Exposures)** — A unique identifier for a known software security flaw. CVE-2021-44228 is Log4Shell; anyone can look it up by that ID.

**CVSS (Common Vulnerability Scoring System)** — A 0–10 number rating how severe a CVE is. 10 = critical (easy to exploit, full system takeover possible).

**Neo4j** — The graph database this project uses. It stores nodes and relationships natively and uses a query language called Cypher (similar to SQL but for graphs).

**FastAPI** — A modern Python framework for building REST APIs quickly.

**React + react-force-graph-2d** — React is a UI library; react-force-graph-2d draws the interactive graph using a physics simulation (nodes repel each other, edges act like springs).
