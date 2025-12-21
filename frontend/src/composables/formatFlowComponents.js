// SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
//
// SPDX-License-Identifier: AGPL-3.0-or-later

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
  let optionKeys = Object.keys(optionMap || {});
  if (!optionKeys.length) {
    return null;
  }

  // Sort keys to make palettes deterministic: numeric keys sorted numerically, otherwise lexicographic
  const allNumeric = optionKeys.every((k) => !Number.isNaN(Number(k)));
  optionKeys = optionKeys.sort((a, b) => {
    if (allNumeric) return Number(a) - Number(b);
    return String(a).localeCompare(String(b));
  });

  const cache =
    scope === "node" ? nodePropertyPaletteCache : edgePropertyPaletteCache;
  // Use per-type cache key so different types with the same property name don't collide
  const cacheKey = `${typeName}:${propertyName}`;

  if (!cache.has(cacheKey)) {
    const palette = new Map();
    const colors = generateBluePurpleScale(optionKeys.length);
    optionKeys.forEach((key, index) => {
      palette.set(String(key), colors[index]);
    });
    cache.set(cacheKey, palette);
    // Debug: show palette mapping for this property/type
    console.debug("Built property palette", { cacheKey, optionKeys, colors });
  }

  return cache.get(cacheKey).get(String(normalizedValue)) || null;
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
    // Try to obtain the property value from multiple sources if missing in the base edge data
    let propValue = getPropertyValue(data, colorMode.key);

    // If not present, check pollRatings map (some systems store aggregated answers here)
    if (
      propValue == null &&
      data?.pollRatings &&
      data.pollRatings[colorMode.key] != null
    ) {
      propValue = data.pollRatings[colorMode.key];
    }

    // If still missing, and the edge has a rating stored as causal_strength with ratingLabel matching the property
    if (
      propValue == null &&
      data?.ratingLabel === colorMode.key &&
      data?.causal_strength != null
    ) {
      propValue = data.causal_strength;
    }

    // As a last resort for commonly named properties like causal_strength, try that field explicitly
    if (
      propValue == null &&
      colorMode.key &&
      typeof colorMode.key === "string" &&
      colorMode.key.endsWith("_strength") &&
      data?.causal_strength != null
    ) {
      propValue = data.causal_strength;
    }

    const propertyColor = getCustomPropertyColor(
      "edge",
      edge_type,
      colorMode.key,
      propValue,
    );

    const typePropertyOptions =
      edgeTypes.value[edge_type]?.property_options || {};
    // Detailed debug information to help understand why colouring fails
    if (!propertyColor) {
      console.debug("Edge property colour resolution", {
        edge_type,
        property: colorMode.key,
        resolvedValue: propValue,
        propertyOptions: typePropertyOptions,
        optionKeys: Object.keys(
          typePropertyOptions[colorMode.key]?.options || {},
        ),
        edgeDataKeys: Object.keys(data || {}),
        dataPreview: data,
      });
    } else {
      console.debug("Edge property colour found", {
        edge_type,
        property: colorMode.key,
        value: propValue,
        color: propertyColor,
      });
    }

    strokeColor = propertyColor || conf.stroke || defaultThemeEdgeColor;
  } else {
    strokeColor = conf.stroke || defaultThemeEdgeColor;
  }

  const strokeWidth = conf.strokeWidth ?? 1.5;

  // Ensure marker color follows stroke color (style can be overridden by config.markerEnd but we still want consistent colouring)
  const markerEndConf = {
    ...(conf.markerEnd || { type: "arrow", height: 15, width: 15 }),
    color: strokeColor,
  };

  // Debugging: log when a property colour was requested but not available
  if (colorMode.mode === "property") {
    const prop = colorMode.key;
    const propertyColor = getCustomPropertyColor(
      "edge",
      edge_type,
      prop,
      getPropertyValue(data, prop),
    );
    if (!propertyColor) {
      console.debug("Edge property colour not found", {
        edge_type,
        property: prop,
        value: getPropertyValue(data, prop),
        available: edgeTypes.value[edge_type]?.property_options || {},
      });
    }
  }

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
