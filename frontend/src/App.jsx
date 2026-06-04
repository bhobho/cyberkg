/**
 * App.jsx — Root component.
 *
 * Layout:
 *   Header  (title + live stats)
 *   Body
 *     Sidebar  (SearchPanel with 3 query tabs)
 *     GraphArea (ForceGraph2D visualization)
 */
import { useState, useEffect } from "react";
import { fetchGraph, fetchStats } from "./api/client";
import GraphView   from "./components/GraphView";
import SearchPanel from "./components/SearchPanel";

export default function App() {
  const [graphData,    setGraphData]    = useState(null);
  const [stats,        setStats]        = useState(null);
  const [highlightIds, setHighlightIds] = useState([]);
  const [loadError,    setLoadError]    = useState("");

  useEffect(() => {
    fetchGraph()
      .then(r => setGraphData(r.data))
      .catch(() => setLoadError("Could not load graph. Is the backend running on port 8000?"));

    fetchStats()
      .then(r => setStats(r.data))
      .catch(() => {});
  }, []);

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Cybersecurity Attack Knowledge Graph</h1>
          <p className="subtitle">Explore malware → techniques → CVEs → assets</p>
        </div>

        {stats && (
          <>
            <span className="stat-chip">Malware: <span>{stats.nodes?.Malware ?? 0}</span></span>
            <span className="stat-chip">Techniques: <span>{stats.nodes?.Technique ?? 0}</span></span>
            <span className="stat-chip">CVEs: <span>{stats.nodes?.CVE ?? 0}</span></span>
            <span className="stat-chip">Assets: <span>{stats.nodes?.Asset ?? 0}</span></span>
            <span className="stat-chip">Relationships: <span>{stats.edges ?? 0}</span></span>
          </>
        )}

        {highlightIds.length > 0 && (
          <button
            onClick={() => setHighlightIds([])}
            style={{ marginLeft: "auto", padding: "5px 12px", borderRadius: 6, border: "1px solid #2a2d3e", background: "transparent", color: "#8892a4", cursor: "pointer", fontSize: 12 }}
          >
            Clear highlight
          </button>
        )}
      </header>

      <div className="body">
        <aside className="sidebar">
          <SearchPanel onHighlight={setHighlightIds} />
        </aside>

        <main className="graph-area">
          {loadError ? (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", flexDirection: "column", gap: 12 }}>
              <p style={{ color: "#ef4444", fontSize: 14 }}>{loadError}</p>
              <p style={{ color: "#8892a4", fontSize: 12 }}>Run: <code style={{ background: "#1a1d2e", padding: "2px 6px", borderRadius: 4 }}>uvicorn main:app --reload</code> in the backend folder</p>
            </div>
          ) : (
            <GraphView graphData={graphData} highlightIds={highlightIds} />
          )}
        </main>
      </div>
    </div>
  );
}
