/**
 * NodeDetail — floating panel shown when user clicks a graph node.
 * Displays all properties of the clicked node.
 */

const LABEL_COLORS = {
  Malware:   { bg: "#450a0a", color: "#ef4444" },
  Technique: { bg: "#431407", color: "#f97316" },
  CVE:       { bg: "#422006", color: "#eab308" },
  Asset:     { bg: "#172554", color: "#3b82f6" },
};

const SKIP_KEYS = ["id", "name", "label", "color", "x", "y", "vx", "vy", "fx", "fy", "__indexColor", "index"];

export default function NodeDetail({ node, onClose }) {
  if (!node) return null;

  const lc = LABEL_COLORS[node.label] || { bg: "#1e1e2e", color: "#888" };
  const extras = Object.entries(node).filter(([k]) => !SKIP_KEYS.includes(k));

  return (
    <div className="node-detail">
      <button className="close-btn" onClick={onClose}>×</button>
      <h4>{node.name || node.id}</h4>
      <span className="label" style={{ background: lc.bg, color: lc.color }}>
        {node.label}
      </span>

      {node.id && (
        <div className="nd-row">
          <span className="nd-key">ID</span>
          <span className="nd-val">{node.id}</span>
        </div>
      )}

      {extras.map(([k, v]) => (
        <div className="nd-row" key={k}>
          <span className="nd-key">{k}</span>
          <span className="nd-val">
            {typeof v === "object" ? JSON.stringify(v) : String(v ?? "—")}
          </span>
        </div>
      ))}
    </div>
  );
}
