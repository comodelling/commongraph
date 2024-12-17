export function formatFlowEdgeProps(data) {
  const { source, target, edge_type } = data;

  const flowSource =
    edge_type === "imply" ? source.toString() : target.toString();
  const flowTarget =
    edge_type === "imply" ? target.toString() : source.toString();
  const markerEnd =
    edge_type === "imply"
      ? { type: "arrowclosed", height: 25, width: 25 }
      : undefined;
  const markerStart =
    edge_type === "require"
      ? { type: "arrow", height: 25, width: 25 }
      : undefined;

  return {
    id: `${source}-${target}`,
    type: "special",
    source: flowSource,
    target: flowTarget,
    markerEnd: markerEnd,
    markerStart: markerStart,
    data: { ...data },
  };
}
