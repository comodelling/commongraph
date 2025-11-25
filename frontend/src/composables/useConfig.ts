// SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { ref, computed } from "vue";
import api from "../api/axios";

/* module‐scope singletons */
const nodeTypes = ref<Record<string, any>>({});
const edgeTypes = ref<Record<string, any>>({});
const platformName = ref<string>("");
const platformTagline = ref<string>("");
const platformDescription = ref<string>("");
const configLoaded = ref(false);
const nodePollTypes = ref<Record<string, any>>({});
const edgePollTypes = ref<Record<string, any>>({});
const nodePollsByType = ref<Record<string, Record<string, any>>>({});
const edgePollsByType = ref<Record<string, Record<string, any>>>({});
const permissions = ref<Record<string, boolean>>({});
const allowSignup = ref<boolean>(true);
const license = ref<string>("");

function toStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((entry) => (typeof entry === "string" ? entry : String(entry)))
    .filter((entry) => Boolean(entry));
}

function pushUnique(list: string[], value?: string | null) {
  if (!value) {
    return;
  }
  if (!list.includes(value)) {
    list.push(value);
  }
}

function buildAggregatedPolls(data: Record<string, any>): Record<string, any> {
  const aggregated: Record<string, any> = {};
  const basePolls = (data?.polls || {}) as Record<string, any>;

  const ensureEntry = (label: string, pollConfig: Record<string, any> = {}) => {
    if (!aggregated[label]) {
      aggregated[label] = {
        ...pollConfig,
        node_types: toStringArray(pollConfig?.node_types),
        edge_types: toStringArray(pollConfig?.edge_types),
      };
    }
    return aggregated[label];
  };

  Object.entries(basePolls || {}).forEach(([label, pollConfig]) => {
    ensureEntry(label, pollConfig || {});
  });

  const addFromTypes = (
    typeMap: Record<string, any> | undefined,
    targetField: "node_types" | "edge_types",
  ) => {
    Object.entries(typeMap || {}).forEach(([typeName, typeDef]) => {
      Object.entries(typeDef?.polls || {}).forEach(([label, pollConfig]) => {
        const entry = ensureEntry(label, pollConfig || {});
        pushUnique(entry[targetField], typeName);
      });
    });
  };

  addFromTypes(data?.node_types, "node_types");
  addFromTypes(data?.edge_types, "edge_types");

  return aggregated;
}

async function load(forceReload = false) {
  if (configLoaded.value && !forceReload) return;
  try {
    const { data } = await api.get("/config");
    nodeTypes.value = data.node_types;
    edgeTypes.value = data.edge_types;
    const pollsByNodeType: Record<string, Record<string, any>> = {};
    const pollsByEdgeType: Record<string, Record<string, any>> = {};

    nodePollTypes.value = {};
    edgePollTypes.value = {};

    const pollsConfig = buildAggregatedPolls(data);
    Object.entries(pollsConfig).forEach(([label, poll]) => {
      const pollConfig = poll || {};
      const nodeTypesList: string[] = pollConfig.node_types || [];
      const edgeTypesList: string[] = pollConfig.edge_types || [];

      if (nodeTypesList.length) {
        nodePollTypes.value[label] = pollConfig;
      }
      if (edgeTypesList.length) {
        edgePollTypes.value[label] = pollConfig;
      }

      nodeTypesList.forEach((nodeType) => {
        if (!pollsByNodeType[nodeType]) {
          pollsByNodeType[nodeType] = {};
        }
        pollsByNodeType[nodeType][label] = pollConfig;
      });

      edgeTypesList.forEach((edgeType) => {
        if (!pollsByEdgeType[edgeType]) {
          pollsByEdgeType[edgeType] = {};
        }
        pollsByEdgeType[edgeType][label] = pollConfig;
      });
    });

    nodePollsByType.value = pollsByNodeType;
    edgePollsByType.value = pollsByEdgeType;

    platformName.value = data.platform_name;
    platformTagline.value = data.platform_tagline;
    platformDescription.value = data.platform_description;
    permissions.value = data.permissions || {};
    allowSignup.value = data.allow_signup !== false;
    license.value = data.license ?? "";
    configLoaded.value = true;
    console.log("Config loaded", forceReload ? "(forced reload)" : "");
  } catch (error) {
    console.error("Failed to load meta config", error);
  }
}

function clearCache() {
  configLoaded.value = false;
}

// Export for use by other composables
export function reloadConfig() {
  return load(true);
}

/**
 * Helper function to get the Creative Commons license URL
 * @param licenseCode - License code like "CC BY-SA", "CC BY-NC-SA", "CC0", etc.
 * @returns URL to the CC license deed
 */
function getLicenseUrl(licenseCode: string): string {
  // Map of CC license codes to their URLs
  const licenseMap: Record<string, string> = {
    "CC BY": "https://creativecommons.org/licenses/by/4.0/",
    "CC BY-SA": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC BY-NC": "https://creativecommons.org/licenses/by-nc/4.0/",
    "CC BY-NC-SA": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
    "CC BY-ND": "https://creativecommons.org/licenses/by-nd/4.0/",
    "CC BY-NC-ND": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
    CC0: "https://creativecommons.org/publicdomain/zero/1.0/",
    "CC PDM": "https://creativecommons.org/publicdomain/mark/1.0/",
  };

  return licenseMap[licenseCode] || "https://creativecommons.org/licenses/";
}

export function useConfig() {
  const defaultNodeType = computed(() => Object.keys(nodeTypes.value)[0] || "");
  const defaultEdgeType = computed(() => Object.keys(edgeTypes.value)[0] || "");

  function getNodePolls(type: string) {
    return nodePollsByType.value[type] || {};
  }
  function getEdgePolls(type: string) {
    return edgePollsByType.value[type] || {};
  }

  function nodeAllowsProperty(
    type: string | null | undefined,
    prop: string,
  ): boolean {
    if (!type || !prop) {
      return false;
    }
    const typeDef = nodeTypes.value?.[type];
    const properties: string[] = (typeDef?.properties as string[]) || [];
    return properties.includes(prop);
  }

  function edgeAllowsProperty(
    type: string | null | undefined,
    prop: string,
  ): boolean {
    if (!type || !prop) {
      return false;
    }
    const typeDef = edgeTypes.value?.[type];
    const properties: string[] = (typeDef?.properties as string[]) || [];
    return properties.includes(prop);
  }

  // Permission helpers
  const canRead = computed(() => permissions.value.read !== false); // Default to true for backward compatibility
  const canCreate = computed(() => permissions.value.create || false);
  const canEdit = computed(() => permissions.value.edit || false);
  const canDelete = computed(() => permissions.value.delete || false);
  const canRate = computed(() => permissions.value.rate || false);

  return {
    load,
    clearCache,
    reloadConfig: () => load(true),
    nodeTypes,
    edgeTypes,
    platformName,
    platformTagline: platformTagline,
    platformDescription: platformDescription,
    configLoaded,
    defaultNodeType,
    defaultEdgeType,
    nodePollTypes,
    edgePollTypes,
    nodePollsByType,
    edgePollsByType,
    getNodePolls,
    getEdgePolls,
    nodeAllowsProperty,
    edgeAllowsProperty,
    permissions,
    canRead,
    canCreate,
    canEdit,
    canDelete,
    canRate,
    allowSignup,
    license,
    getLicenseUrl,
  };
}
