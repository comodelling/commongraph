import { useConfig } from "./useConfig";
import { COLOR_MODE_TYPE, parseColorToken } from "../utils/graphColoring";
const { nodeTypes, edgeTypes, nodeAllowsProperty } = useConfig();

const defaultThemeBorderColor = "var(--border-color)";
const defaultThemeEdgeColor = "var(--border-color)";

const defaultStrengthColors = {
  A: "#006d2c",
  B: "#74c476",
  C: "#e3c100",
  D: "#fb6a4a",
  E: "#a50f15",
};

const nodePropertyPaletteCache = new Map();
const edgePropertyPaletteCache = new Map();

function hexToRgb(hex) {
  const value = hex.replace("#", "");
  const bigint = parseInt(value, 16);
  return {
    r: (bigint >> 16) & 255,
    g: (bigint >> 8) & 255,
    b: bigint & 255,
  };
}

function rgbToHex({ r, g, b }) {
  const clamp = (num) => Math.min(255, Math.max(0, Math.round(num)));
  return `#${[clamp(r), clamp(g), clamp(b)]
    .map((num) => num.toString(16).padStart(2, "0"))
    .join("")}`;
}

function interpolateColor(start, end, factor) {
  return {
    r: start.r + (end.r - start.r) * factor,
    g: start.g + (end.g - start.g) * factor,
    b: start.b + (end.b - start.b) * factor,
  };
}

function generateBluePurpleScale(count) {
  const start = hexToRgb("#3b82f6");
  const end = hexToRgb("#a855f7");
  if (count <= 1) {
    return [rgbToHex(start)];
  }
  const colors = [];
  for (let index = 0; index < count; index += 1) {
    const t = index / (count - 1);
    colors.push(rgbToHex(interpolateColor(start, end, t)));
  }
  return colors;
}

function normalizeOptionKey(value) {
  if (value == null) {
    return null;
  }
  if (Array.isArray(value)) {
    return normalizeOptionKey(value[0]);
  }
  return typeof value === "string" ? value : String(value);
}

function getPropertyValue(entity, propertyName) {
  if (!propertyName || !entity) {
    return null;
  }
  const rawValue = entity[propertyName];
  if (Array.isArray(rawValue)) {
    return rawValue.length ? rawValue[0] : null;
  }
  return rawValue ?? null;
}

function lookupPropertyConfig(scope, typeName, propertyName) {
  if (!propertyName) {
    return null;
  }
  const collection = scope === "node" ? nodeTypes.value : edgeTypes.value;
  if (!collection) {
    return null;
  }
  const typeDef = collection[typeName] || {};
  const propertyOptions = typeDef.property_options || {};
  if (propertyOptions[propertyName]) {
    return propertyOptions[propertyName];
  }

  const fallback = Object.values(collection).find(
    (def) => def?.property_options?.[propertyName],
  );
  return fallback?.property_options?.[propertyName] || null;
}

function getCustomPropertyColor(scope, typeName, propertyName, optionValue) {
  const normalizedValue = normalizeOptionKey(optionValue);
  if (!propertyName || normalizedValue == null) {
    return null;
  }

  const propertyConfig = lookupPropertyConfig(scope, typeName, propertyName);
  const optionMap = propertyConfig?.options || {};
  const optionKeys = Object.keys(optionMap);
  if (!optionKeys.length) {
    return null;
  }

  const cache =
    scope === "node" ? nodePropertyPaletteCache : edgePropertyPaletteCache;
  if (!cache.has(propertyName)) {
    const palette = new Map();
    const colors = generateBluePurpleScale(optionKeys.length);
    optionKeys.forEach((key, index) => {
      palette.set(key, colors[index]);
    });
    cache.set(propertyName, palette);
  }

  return cache.get(propertyName).get(normalizedValue) || null;
}

function getNodePollValue(nodeData, pollLabel) {
  if (!pollLabel) {
    return null;
  }
  if (nodeData?.pollRatings && nodeData.pollRatings[pollLabel] != null) {
    return nodeData.pollRatings[pollLabel];
  }
  if (nodeData?.ratingLabel === pollLabel && nodeData?.support != null) {
    return nodeData.support;
  }
  return null;
}

function getEdgePollValue(edgeData, pollLabel) {
  if (!pollLabel) {
    return null;
  }
  if (edgeData?.pollRatings && edgeData.pollRatings[pollLabel] != null) {
    return edgeData.pollRatings[pollLabel];
  }
  if (
    edgeData?.ratingLabel === pollLabel &&
    edgeData?.causal_strength != null
  ) {
    return edgeData.causal_strength;
  }
  return null;
}

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

export function formatFlowEdgeProps(data, colorBy = COLOR_MODE_TYPE) {
  const { source, target, edge_type, selected } = data;
  const conf = edgeTypes.value[edge_type]?.style || {};
  const colorMode = parseColorToken(colorBy);

  let strokeColor;
  let effectiveStrength = data.causal_strength;
  let effectiveRatingLabel = data.ratingLabel;

  if (colorMode.mode === "poll") {
    const pollValue = getEdgePollValue(data, colorMode.key);
    effectiveStrength = pollValue;
    effectiveRatingLabel = colorMode.key || data.ratingLabel;
    strokeColor =
      pollValue != null
        ? getRatingColor(pollValue) || defaultThemeEdgeColor
        : defaultThemeEdgeColor;
  } else if (colorMode.mode === "property") {
    const propertyColor = getCustomPropertyColor(
      "edge",
      edge_type,
      colorMode.key,
      getPropertyValue(data, colorMode.key),
    );
    strokeColor = propertyColor || conf.stroke || defaultThemeEdgeColor;
  } else {
    strokeColor = conf.stroke || defaultThemeEdgeColor;
  }

  const strokeWidth = conf.strokeWidth ?? 1.5;
  const markerEndConf = conf.markerEnd || {
    type: "arrow",
    height: 15,
    width: 15,
    color: strokeColor,
  };

  return {
    // Ensure source/target ids are safe strings (preview nodes may not have node_id yet)
    id: `${source != null ? source.toString() : `preview-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`}-${
      target != null
        ? target.toString()
        : `preview-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
    }`,
    type: "special",
    source:
      source != null
        ? source.toString()
        : `preview-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    target:
      target != null
        ? target.toString()
        : `preview-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    markerEnd: markerEndConf,
    markerStart: undefined,
    data: {
      ...data,
      ratingLabel: effectiveRatingLabel,
      causal_strength: effectiveStrength,
    },
    selected: !!selected,
    style: { stroke: strokeColor, strokeWidth },
  };
}

export function formatFlowNodeProps(data, colorBy = COLOR_MODE_TYPE) {
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
  const colorMode = parseColorToken(colorBy);
  const statusAllowed =
    typeof nodeAllowsProperty === "function" &&
    nodeAllowsProperty(node_type, "status");
  const normalizedStatus =
    statusAllowed && typeof status === "string" ? status : undefined;

  let borderColor;
  let effectiveSupport = support;
  let effectiveRatingLabel = ratingLabel;

  if (colorMode.mode === "poll") {
    const pollValue = getNodePollValue(data, colorMode.key);
    effectiveSupport = pollValue;
    effectiveRatingLabel = colorMode.key || ratingLabel;
    borderColor =
      pollValue != null
        ? getRatingColor(pollValue) || defaultThemeBorderColor
        : defaultThemeBorderColor;
  } else if (colorMode.mode === "property") {
    const propertyColor = getCustomPropertyColor(
      "node",
      node_type,
      colorMode.key,
      getPropertyValue(data, colorMode.key),
    );
    borderColor = propertyColor || conf.borderColor || defaultThemeBorderColor;
  } else {
    borderColor = conf.borderColor || defaultThemeBorderColor;
  }

  const borderWidth = conf.borderWidth || defaultNodeBorderWidth;
  const borderRadius = conf.borderRadius || defaultNodeBorderRadius;
  const borderStyle =
    conf.borderStyle || (normalizedStatus === "draft" ? "dotted" : "solid");
  const opacity =
    conf.opacity ??
    (["realised", "unrealised"].includes(normalizedStatus) ? 0.5 : 0.95);

  return {
    // Ensure node id is a string; if missing (preview/new node), create a temporary preview id
    id:
      node_id != null
        ? node_id.toString()
        : `preview-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    type: "special",
    position: position || { x: 0, y: 0 },
    label: title,
    selected: !!selected,
    data: {
      ...data,
      ratingLabel: effectiveRatingLabel,
      support: effectiveSupport,
    },
    style: { opacity, borderColor, borderWidth, borderStyle, borderRadius },
  };
}
