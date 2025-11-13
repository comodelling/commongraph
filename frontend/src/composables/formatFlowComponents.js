import { useConfig } from "./useConfig";
const { nodeTypes, edgeTypes } = useConfig();

const defaultThemeBorderColor = "var(--border-color)";
const defaultThemeEdgeColor = "var(--border-color)";

const defaultStrengthColors = {
  A: "#006d2c",
  B: "#74c476",
  C: "#e3c100",
  D: "#fb6a4a",
  E: "#a50f15",
};

// Convert numeric rating (1-5) to letter grade (A-E)
// Assuming 5 is best (A) and 1 is worst (E)
function numericRatingToGrade(rating) {
  if (!rating || typeof rating !== "number") return null;
  if (rating >= 4.5) return "A";
  if (rating >= 3.5) return "B";
  if (rating >= 2.5) return "C";
  if (rating >= 1.5) return "D";
  return "E";
}

// Get color for a numeric or letter rating
function getRatingColor(rating) {
  if (!rating) return null;
  // If it's already a letter grade, use it directly
  if (typeof rating === "string" && defaultStrengthColors[rating]) {
    return defaultStrengthColors[rating];
  }
  // If it's a number, convert to letter grade first
  if (typeof rating === "number") {
    const grade = numericRatingToGrade(rating);
    return defaultStrengthColors[grade];
  }
  return null;
}

const defaultNodeBorderWidth = "4px";
const defaultNodeBorderRadius = "5px";

export function formatFlowEdgeProps(data, colorBy = "type") {
  const { source, target, edge_type, selected, causal_strength, ratingLabel } =
    data;
  const conf = edgeTypes.value[edge_type]?.style || {};
  console.log(
    "formatFlowEdgeProps - colorBy:",
    colorBy,
    "causal_strength:",
    causal_strength,
  );

  let strokeColor;
  if (colorBy === "rating") {
    // Use rating-based color (supports both numeric and letter grades)
    if (causal_strength != null) {
      const ratingColor = getRatingColor(causal_strength);
      strokeColor = ratingColor || defaultThemeEdgeColor;
      console.log(
        "Using rating color for edge:",
        causal_strength,
        "->",
        strokeColor,
      );
    } else {
      strokeColor = defaultThemeEdgeColor;
      console.log(
        "No rating for edge, using theme default color:",
        strokeColor,
      );
    }
  } else {
    // Use type-based color from config
    strokeColor = conf.stroke || defaultThemeEdgeColor;
    console.log("Using type color from config for edge:", strokeColor);
  }

  const strokeWidth = conf.strokeWidth ?? 1.5;
  const markerEndConf = conf.markerEnd || {
    type: "arrow",
    height: 15,
    width: 15,
    color: strokeColor,
  };

  return {
    id: `${source}-${target}`,
    type: "special",
    source: source.toString(),
    target: target.toString(),
    markerEnd: markerEndConf,
    markerStart: undefined,
    data: { ...data, ratingLabel },
    selected: !!selected,
    style: { stroke: strokeColor, strokeWidth },
  };
}

export function formatFlowNodeProps(data, colorBy = "type") {
  const {
    node_id,
    title,
    node_type,
    status,
    position,
    selected,
    support,
    ratingLabel,
  } = data;
  const conf = nodeTypes.value[node_type]?.style || {};
  console.log(
    "formatFlowNodeProps - colorBy:",
    colorBy,
    "support:",
    support,
    "node_type:",
    node_type,
  );

  let borderColor;
  if (colorBy === "rating") {
    if (support != null) {
      // Use rating-based color (supports both numeric and letter grades)
      const ratingColor = getRatingColor(support);
      borderColor = ratingColor || defaultThemeBorderColor;
      console.log("Using rating color:", support, "->", borderColor);
    } else {
      borderColor = defaultThemeBorderColor;
      console.log(
        "No rating for node, using theme default color:",
        borderColor,
      );
    }
  } else {
    // Use type-based color from config
    borderColor = conf.borderColor || defaultThemeBorderColor;
    console.log("Using type color from config:", borderColor);
  }

  const borderWidth = conf.borderWidth || defaultNodeBorderWidth;
  const borderRadius = conf.borderRadius || defaultNodeBorderRadius;
  const borderStyle =
    conf.borderStyle || (status === "draft" ? "dotted" : "solid");
  const opacity =
    conf.opacity ?? (["realised", "unrealised"].includes(status) ? 0.5 : 0.95);

  return {
    id: node_id.toString(),
    type: "special",
    position: position || { x: 0, y: 0 },
    label: title,
    selected: !!selected,
    data: { ...data, ratingLabel },
    style: { opacity, borderColor, borderWidth, borderStyle, borderRadius },
  };
}
