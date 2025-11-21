export const COLOR_MODE_TYPE = "type";
export const COLOR_PREFIXES = Object.freeze({
  POLL: "poll:",
  PROPERTY: "property:",
});

export const NODE_COLOR_STORAGE_KEY = "graphNodeColorBy";
export const EDGE_COLOR_STORAGE_KEY = "graphEdgeColorBy";
export const LEGACY_COLOR_STORAGE_KEY = "graphColorBy";

export function toPollColorValue(label) {
  if (!label) {
    return COLOR_MODE_TYPE;
  }
  return `${COLOR_PREFIXES.POLL}${label}`;
}

export function toPropertyColorValue(name) {
  if (!name) {
    return COLOR_MODE_TYPE;
  }
  return `${COLOR_PREFIXES.PROPERTY}${name}`;
}

export function parseColorToken(token) {
  if (!token || token === COLOR_MODE_TYPE) {
    return { mode: COLOR_MODE_TYPE, key: null };
  }

  if (token.startsWith(COLOR_PREFIXES.POLL)) {
    return {
      mode: "poll",
      key: token.slice(COLOR_PREFIXES.POLL.length) || null,
    };
  }

  if (token.startsWith(COLOR_PREFIXES.PROPERTY)) {
    return {
      mode: "property",
      key: token.slice(COLOR_PREFIXES.PROPERTY.length) || null,
    };
  }

  return { mode: COLOR_MODE_TYPE, key: null };
}

export function humanizeLabel(raw) {
  if (!raw || typeof raw !== "string") {
    return raw ?? "";
  }
  const spaced = raw.replace(/[_-]+/g, " ").trim();
  if (!spaced.length) {
    return raw;
  }
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}
