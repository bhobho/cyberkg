/**
 * SearchPanel — Three-tab sidebar for querying the knowledge graph:
 *   1. Attack Paths  — "Which malware can reach this asset?"
 *   2. CVE Lookup    — "What attacks exploit this CVE?"
 *   3. Malware       — "What does this malware family do?"
 *
 * On successful query, calls onHighlight(ids) so the graph dims unrelated nodes.
 */
import { useState, useEffect } from "react";
import {
  fetchAttackPaths, fetchAllAssets,
  fetchVulnerability, fetchCVEList,
  fetchMalwareDetail, fetchMalwareList,
} from "../api/client";

export default function SearchPanel({ onHighlight }) {
  const [tab, setTab] = useState("paths");

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div className="tabs">
        <button className={`tab ${tab === "paths"   ? "active" : ""}`} onClick={() => setTab("paths")}>Attack Paths</button>
        <button className={`tab ${tab === "cve"     ? "active" : ""}`} onClick={() => setTab("cve")}>CVE Lookup</button>
        <button className={`tab ${tab === "malware" ? "active" : ""}`} onClick={() => setTab("malware")}>Malware</button>
      </div>

      {tab === "paths"   && <AttackPathsTab onHighlight={onHighlight} />}
      {tab === "cve"     && <CVETab         onHighlight={onHighlight} />}
      {tab === "malware" && <MalwareTab     onHighlight={onHighlight} />}
    </div>
  );
}

/* ─── Tab 1: Attack Paths ─────────────────────────────────────────────── */
function AttackPathsTab({ onHighlight }) {
  const [assets,  setAssets]  = useState([]);
  const [selected, setSelected] = useState("");
  const [result,  setResult]  = useState(null);
  const [error,   setError]   = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchAllAssets().then(r => {
      setAssets(r.data);
      if (r.data.length) setSelected(r.data[0].name);
    }).catch(() => {});
  }, []);

  async function search() {
    if (!selected) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const r = await fetchAttackPaths(selected);
      setResult(r.data);
      // Highlight all node IDs involved in attack chains
      const ids = new Set([r.data.asset]);
      r.data.attack_chains.forEach(c => {
        if (c.malware_id)   ids.add(c.malware_id);
        if (c.technique_id) ids.add(c.technique_id);
        if (c.cve)          ids.add(c.cve);
      });
      onHighlight([...ids]);
    } catch (e) {
      setError(e.response?.data?.detail || "Query failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="panel">
      <p style={{ color: "#8892a4", fontSize: 12 }}>
        Select an asset to see every attack chain that can reach it.
      </p>

      <div className="field">
        <label>Target Asset</label>
        <select value={selected} onChange={e => setSelected(e.target.value)}>
          {assets.map(a => <option key={a.id} value={a.name}>{a.name}</option>)}
        </select>
      </div>

      <button className="btn btn-primary" onClick={search} disabled={loading || !selected}>
        {loading ? "Searching…" : "Find Attack Paths"}
      </button>

      {error && <p className="error-msg">{error}</p>}

      {result && (
        <div className="result-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3>{result.asset}</h3>
            <span className={`risk-badge risk-${result.risk_score}`}>{result.risk_score} Risk</span>
          </div>
          <p style={{ color: "#8892a4", fontSize: 11 }}>{result.asset_type}</p>

          {result.attack_chains.length === 0 ? (
            <p className="empty-msg">No chained attack paths found.</p>
          ) : (
            <>
              <p style={{ fontSize: 11, color: "#8892a4" }}>{result.attack_chains.length} attack chain(s) found:</p>
              {result.attack_chains.map((c, i) => (
                <div className="chain-row" key={i}>
                  <div className="chain-flow">
                    <span className="node-pill pill-mal">{c.malware}</span>
                    <span className="arrow">→</span>
                    <span className="node-pill pill-tech">{c.technique}</span>
                    <span className="arrow">→</span>
                    <span className="node-pill pill-cve">{c.cve}</span>
                  </div>
                  <div className="cvss-score">
                    Tactic: {c.tactic} · CVSS: <span>{c.cvss ?? "N/A"}</span>
                  </div>
                </div>
              ))}
            </>
          )}

          {result.direct_targets?.length > 0 && (
            <div>
              <p style={{ fontSize: 11, color: "#8892a4", marginBottom: 4 }}>Direct malware targets:</p>
              <div className="tag-list">
                {result.direct_targets.map(m => <span className="tag" key={m}>{m}</span>)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ─── Tab 2: CVE Lookup ───────────────────────────────────────────────── */
function CVETab({ onHighlight }) {
  const [cves,    setCves]    = useState([]);
  const [selected, setSelected] = useState("");
  const [result,  setResult]  = useState(null);
  const [error,   setError]   = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCVEList().then(r => {
      setCves(r.data);
      if (r.data.length) setSelected(r.data[0].id);
    }).catch(() => {});
  }, []);

  async function search() {
    if (!selected) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const r = await fetchVulnerability(selected);
      setResult(r.data);
      onHighlight([r.data.cve_id]);
    } catch (e) {
      setError(e.response?.data?.detail || "Query failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="panel">
      <p style={{ color: "#8892a4", fontSize: 12 }}>
        Look up a CVE to see which malware exploits it and which assets are at risk.
      </p>

      <div className="field">
        <label>CVE ID</label>
        <select value={selected} onChange={e => setSelected(e.target.value)}>
          {cves.map(c => (
            <option key={c.id} value={c.id}>
              {c.id} (CVSS {c.cvss ?? "?"})
            </option>
          ))}
        </select>
      </div>

      <button className="btn btn-primary" onClick={search} disabled={loading || !selected}>
        {loading ? "Looking up…" : "Lookup CVE"}
      </button>

      {error && <p className="error-msg">{error}</p>}

      {result && (
        <div className="result-card">
          <h3>{result.cve_id}</h3>
          <p style={{ fontSize: 11, color: "#8892a4" }}>{result.description}</p>
          <div className="nd-row">
            <span className="nd-key">CVSS</span>
            <span style={{ color: result.cvss >= 9 ? "#ef4444" : result.cvss >= 7 ? "#f97316" : "#eab308", fontWeight: 700 }}>
              {result.cvss ?? "N/A"}
            </span>
          </div>

          {result.malware_families?.length > 0 && (
            <div>
              <p style={{ fontSize: 11, color: "#8892a4", marginBottom: 4 }}>Exploited by:</p>
              <div className="tag-list">
                {result.malware_families.map(m => <span className="tag" key={m} style={{ background: "#450a0a", color: "#ef4444" }}>{m}</span>)}
              </div>
            </div>
          )}

          {result.techniques?.length > 0 && (
            <div>
              <p style={{ fontSize: 11, color: "#8892a4", marginBottom: 4 }}>Via techniques:</p>
              <div className="tag-list">
                {result.techniques.map(t => <span className="tag" key={t}>{t}</span>)}
              </div>
            </div>
          )}

          {result.affected_assets?.length > 0 && (
            <div>
              <p style={{ fontSize: 11, color: "#8892a4", marginBottom: 4 }}>Affected assets:</p>
              <div className="tag-list">
                {result.affected_assets.filter(a => a.name).map(a => (
                  <span className="tag" key={a.name} style={{ background: "#172554", color: "#3b82f6" }}>{a.name}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ─── Tab 3: Malware ──────────────────────────────────────────────────── */
function MalwareTab({ onHighlight }) {
  const [malwares,  setMalwares]  = useState([]);
  const [selected,  setSelected]  = useState("");
  const [result,    setResult]    = useState(null);
  const [error,     setError]     = useState("");
  const [loading,   setLoading]   = useState(false);

  useEffect(() => {
    fetchMalwareList().then(r => {
      setMalwares(r.data);
      if (r.data.length) setSelected(r.data[0].name);
    }).catch(() => {});
  }, []);

  async function search() {
    if (!selected) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const r = await fetchMalwareDetail(selected);
      setResult(r.data);
      const ids = [
        ...r.data.techniques.map(t => t.id),
        ...r.data.cves,
      ];
      onHighlight(ids);
    } catch (e) {
      setError(e.response?.data?.detail || "Query failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="panel">
      <p style={{ color: "#8892a4", fontSize: 12 }}>
        Select a malware family to see its techniques, CVEs, and targets.
      </p>

      <div className="field">
        <label>Malware Family</label>
        <select value={selected} onChange={e => setSelected(e.target.value)}>
          {malwares.map(m => <option key={m.id} value={m.name}>{m.name} ({m.type})</option>)}
        </select>
      </div>

      <button className="btn btn-primary" onClick={search} disabled={loading || !selected}>
        {loading ? "Loading…" : "Analyze Malware"}
      </button>

      {error && <p className="error-msg">{error}</p>}

      {result && (
        <div className="result-card">
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <h3>{result.malware}</h3>
            <span className="tag" style={{ background: "#450a0a", color: "#ef4444" }}>{result.malware_type}</span>
          </div>
          <p style={{ fontSize: 11, color: "#8892a4" }}>{result.description}</p>

          {result.techniques?.length > 0 && (
            <div>
              <p style={{ fontSize: 11, color: "#8892a4", marginBottom: 4 }}>ATT&CK Techniques:</p>
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {result.techniques.filter(t => t.id).map(t => (
                  <div key={t.id} className="chain-row">
                    <span style={{ color: "#f97316", fontWeight: 700 }}>{t.id}</span>
                    <span style={{ color: "#cbd5e1", marginLeft: 6 }}>{t.name}</span>
                    <div style={{ color: "#8892a4", fontSize: 11, marginTop: 2 }}>{t.tactic}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.cves?.length > 0 && (
            <div>
              <p style={{ fontSize: 11, color: "#8892a4", marginBottom: 4 }}>CVEs exploited:</p>
              <div className="tag-list">
                {result.cves.map(c => <span className="tag" key={c} style={{ background: "#422006", color: "#eab308" }}>{c}</span>)}
              </div>
            </div>
          )}

          {result.targets?.length > 0 && (
            <div>
              <p style={{ fontSize: 11, color: "#8892a4", marginBottom: 4 }}>Known targets:</p>
              <div className="tag-list">
                {result.targets.map(t => <span className="tag" key={t} style={{ background: "#172554", color: "#3b82f6" }}>{t}</span>)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
