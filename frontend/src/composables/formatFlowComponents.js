import { useConfig } from "./useConfig";
const { nodeTypes, edgeTypes } = useConfig();

const defaultStrengthColors = {
  A: "#006d2c", B: "#74c476", C: "#e3c100", D: "#fb6a4a", E: "#a50f15",
};
const defaultNodeBorderWidth = "5px";

const defaultNodeBorderRadius = "5px";

export function formatFlowEdgeProps(data) {
  const { source, target, edge_type, selected, causal_strength } = data;
  const conf = edgeTypes.value[edge_type]?.style || {};
  console.log("config", conf);

  const strokeColor   = conf.stroke      || defaultStrengthColors[causal_strength] || "#ccc";
  const strokeWidth   = conf.strokeWidth ?? 1.5;
  const markerEndConf = conf.markerEnd   || { type: "arrow", height: 15, width: 15, color: strokeColor };

  return {
    id: `${source}-${target}`,
    type: "special",
    source: source.toString(),
    target: target.toString(),
    markerEnd: markerEndConf,
    markerStart: undefined,
    data: { ...data },
    selected: !!selected,
    style: { stroke: strokeColor, strokeWidth },
  };
}

export function formatFlowNodeProps(data) {
  const { node_id, title, node_type, status, position, selected, support } = data;
  const conf = nodeTypes.value[node_type]?.style || {};
  console.log("config", conf);
  console.log("nodeTypes", nodeTypes.value);

  const borderColor = conf.borderColor || defaultStrengthColors[support] || "#ccc";
  const borderWidth = conf.borderWidth || defaultNodeBorderWidth;
  const borderRadius= conf.borderRadius|| defaultNodeBorderRadius;
  const borderStyle = conf.borderStyle || (status === "draft" ? "dotted" : "solid");
  const opacity     = conf.opacity     ?? (status === "completed" ? 0.5 : 0.95);

  return {
    id: node_id.toString(),
    type: "special",
    position: position || { x: 0, y: 0 },
    label: title,
    selected: !!selected,
    data: { ...data },
    style: { opacity, borderColor, borderWidth, borderStyle, borderRadius },
  };
}