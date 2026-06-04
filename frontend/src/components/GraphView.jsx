/**
 * GraphView — Renders the interactive force-directed knowledge graph.
 *
 * Features:
 *  - Nodes colored by type (red=Malware, orange=Technique, yellow=CVE, blue=Asset)
 *  - Click a node to see its properties in NodeDetail panel
 *  - Highlighted nodes dim unrelated nodes when a selection is active
 */
import { useRef, useCallback, useEffect, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import NodeDetail from "./NodeDetail";

export default function GraphView({ graphData, highlightIds }) {
  const fgRef = useRef();
  const [selectedNode, setSelectedNode] = useState(null);
  const [dimensions, setDimensions]     = useState({ width: 800, height: 600 });
  const containerRef = useRef();

  // Track container size so graph fills the available space
  useEffect(() => {
    const obs = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      setDimensions({ width, height });
    });
    if (containerRef.current) obs.observe(containerRef.current);
    return () => obs.disconnect();
  }, []);

  // When new highlight IDs arrive, zoom to show them
  useEffect(() => {
    if (!highlightIds?.length || !fgRef.current) return;
    setTimeout(() => fgRef.current.zoomToFit(400, 60), 300);
  }, [highlightIds]);

  const nodeColor = useCallback(
    (node) => {
      if (!highlightIds?.length) return node.color;
      return highlightIds.includes(node.id) ? node.color : "#2a2d3e";
    },
    [highlightIds]
  );

  const linkColor = useCallback(
    (link) => {
      if (!highlightIds?.length) return "#334155";
      const s = typeof link.source === "object" ? link.source.id : link.source;
      const t = typeof link.target === "object" ? link.target.id : link.target;
      return highlightIds.includes(s) && highlightIds.includes(t) ? "#64748b" : "#1e2535";
    },
    [highlightIds]
  );

  const drawNode = useCallback((node, ctx, globalScale) => {
    const size  = 6;
    const label = node.name || node.id || "";
    const color = nodeColor(node);

    // Draw circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();

    // Draw label when zoomed in
    if (globalScale >= 1.2) {
      ctx.font         = `${Math.max(3, 10 / globalScale)}px sans-serif`;
      ctx.textAlign    = "center";
      ctx.textBaseline = "top";
      ctx.fillStyle    = "#cbd5e1";
      ctx.fillText(label, node.x, node.y + size + 2);
    }
  }, [nodeColor]);

  if (!graphData) {
    return (
      <div ref={containerRef} style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <p style={{ color: "#8892a4" }}>Loading graph…</p>
      </div>
    );
  }

  return (
    <div ref={containerRef} style={{ width: "100%", height: "100%", position: "relative" }}>
      <ForceGraph2D
        ref={fgRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}
        nodeCanvasObject={drawNode}
        nodeCanvasObjectMode={() => "replace"}
        linkColor={linkColor}
        linkWidth={1}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
        backgroundColor="#0f1117"
        onNodeClick={(node) => setSelectedNode(node)}
        cooldownTicks={120}
        onEngineStop={() => fgRef.current?.zoomToFit(400, 40)}
      />

      <NodeDetail node={selectedNode} onClose={() => setSelectedNode(null)} />

      <div className="legend">
        <h5>Node Types</h5>
        {[
          { color: "#ef4444", label: "Malware" },
          { color: "#f97316", label: "Technique (TTP)" },
          { color: "#eab308", label: "CVE" },
          { color: "#3b82f6", label: "Asset" },
        ].map(({ color, label }) => (
          <div className="legend-row" key={label}>
            <div className="legend-dot" style={{ background: color }} />
            <span>{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
