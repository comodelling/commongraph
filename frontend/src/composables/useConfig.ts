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

    const pollsConfig = (data.polls || {}) as Record<string, any>;
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

export function useConfig() {
  const defaultNodeType = computed(() => Object.keys(nodeTypes.value)[0] || "");
  const defaultEdgeType = computed(() => Object.keys(edgeTypes.value)[0] || "");

  function getNodePolls(type: string) {
    return nodePollsByType.value[type] || {};
  }
  function getEdgePolls(type: string) {
    return edgePollsByType.value[type] || {};
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
    permissions,
    canRead,
    canCreate,
    canEdit,
    canDelete,
    canRate,
    allowSignup,
  };
}
