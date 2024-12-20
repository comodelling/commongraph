/**
 * standardise formatting of edge data from backend to frontend format
 * backend data is kept as is in the data field
 **/
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

/**
 * standardise formatting of node data from backend to frontend format
 * backend data is kept as is in the data field
 **/
export function formatFlowNodeProps(data) {
  const { node_id, title, node_type, status } = data;

  const style = {
    opacity: status === "completed" ? 0.4 : 0.95,
    borderColor: status === "completed" ? "green" : "black",
    borderWidth: getBorderWidthByType(node_type),
    borderStyle: status === "draft" ? "dotted" : "solid",
    borderRadius: "8px",
  };

  const nodeProps = {
    id: node_id.toString(),
    type: "special",
    position: { x: 0, y: 0 },
    label: title,
    style: style,
    data: { ...data },
  };

  return nodeProps;
}

function getBorderWidthByType(nodeType) {
  const typeToBorderWidthMap = {
    change: "1px",
    potentiality: "1px",
    action: "2px",
    proposal: "3px",
    objective: "4px",
  };
  return typeToBorderWidthMap[nodeType];
}
