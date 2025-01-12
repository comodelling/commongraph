/**
 * standardise formatting of edge data from backend to frontend format
 * backend data is kept as is in the data field
 **/
export function formatFlowEdgeProps(data) {
  const { source, target, edge_type, selected, causal_strength_rating } = data;

  const flowSource =
    edge_type === "imply" ? source.toString() : target.toString();
  const flowTarget =
    edge_type === "imply" ? target.toString() : source.toString();

  // const strokeWidth = 1 + (data.cprob ?? 0.5);
  // const markerFactor = 1 / (1 + (data.cprob ?? 0.5) / 2);
  const strokeWidth = 1.5;
  const markerSize = 15;

  const markerEnd =
    edge_type === "imply"
      ? {
          type: "arrow",
          height: markerSize,
          width: markerSize,
          color: "grey",
        }
      : undefined;
  const markerStart =
    edge_type === "require"
      ? {
          type: "arrow",
          height: markerSize,
          width: markerSize,
          color: "grey",
        }
      : undefined;

  let strokeColor = "#ccc";
  switch (causal_strength_rating) {
    case "A":
      strokeColor = "#006d2c";
      break;
    case "B":
      strokeColor = "#74c476";
      break;
    case "C":
      strokeColor = "#777";
      break;
    case "D":
      strokeColor = "#fb6a4a";
      break;
    case "E":
      strokeColor = "#a50f15";
      break;
  }

  return {
    id: `${source}-${target}`,
    type: "special",
    source: flowSource,
    target: flowTarget,
    markerEnd: markerEnd,
    markerStart: markerStart,
    data: { ...data },
    selected: selected ? true : false,
    style: {
      stroke: strokeColor,
      strokeWidth: strokeWidth,
      // strokeColor: "blue",
      // opacity: `${0.5 + (data.cprob ?? 0.5) / 2}`,
    },
  };
}

/**
 * standardise formatting of node data from backend to frontend format
 * backend data is kept as is in the data field
 **/
export function formatFlowNodeProps(data) {
  // console.log("formatFlowNodeProps", data);
  const { node_id, title, node_type, status, position, selected, support } =
    data;

  let borderColor = "#ccc";
  switch (support) {
    case "A":
      borderColor = "#006d2c";
      break;
    case "B":
      borderColor = "#74c476";
      break;
    case "C":
      borderColor = "#777";
      break;
    case "D":
      borderColor = "#fb6a4a";
      break;
    case "E":
      borderColor = "#a50f15";
      break;
  }

  const style = {
    opacity: status === "completed" ? 0.5 : 0.95,
    borderColor: borderColor,
    borderWidth: getBorderWidthByType(node_type),
    borderStyle: status === "draft" ? "dotted" : "solid",
    borderRadius: "8px",
  };

  const nodeProps = {
    id: node_id.toString(),
    type: "special",
    position: position || { x: 0, y: 0 },
    label: title,
    style: style,
    selected: selected ? true : false,
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
