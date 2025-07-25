import { ref, computed } from "vue";
import api from "../api/axios";

/* module‐scope singletons */
const nodeTypes     = ref<Record<string, any>>({});
const edgeTypes     = ref<Record<string, any>>({});
const platformName  = ref<string>("");
const tagline       = ref<string>("");
const configLoaded  = ref(false);
const nodePollTypes = ref<Record<string, any>>({});
const edgePollTypes = ref<Record<string, any>>({});
const permissions   = ref<Record<string, boolean>>({});

async function load(forceReload = false) {
  if (configLoaded.value && !forceReload) return;
  try {
    const { data } = await api.get("/config");
    nodeTypes.value    = data.node_types;
    edgeTypes.value    = data.edge_types;
    nodePollTypes.value = Object.keys(data.node_types).reduce((acc, key) => {
      const polls = data.node_types[key].polls || {};
      return { ...acc, ...polls };
    }, {});
    edgePollTypes.value = Object.keys(data.edge_types).reduce((acc, key) => {
      const polls = data.edge_types[key].polls || {};
      return { ...acc, ...polls };
    }, {});
    platformName.value = data.platform_name;
    tagline.value = data.tagline;
    permissions.value = data.permissions || {};
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
  const defaultNodeType = computed(() => Object.keys(nodeTypes.value)[0]||"");
  const defaultEdgeType = computed(() => Object.keys(edgeTypes.value)[0]||"");

  function getNodePolls(type: string) {
    return nodeTypes.value[type]?.polls || {};
  }
  function getEdgePolls(type: string) {
    return edgeTypes.value[type]?.polls || {};
  }

  // Permission helpers
  const canCreate = computed(() => permissions.value.create || false);
  const canEdit = computed(() => permissions.value.edit || false);
  const canDelete = computed(() => permissions.value.delete || false);
  const canRate = computed(() => permissions.value.rate || false);

  return {
    load, clearCache, reloadConfig: () => load(true),
    nodeTypes, edgeTypes, platformName, tagline, configLoaded,
    defaultNodeType, defaultEdgeType,
    nodePollTypes, edgePollTypes,
    getNodePolls, getEdgePolls,
    permissions, canCreate, canEdit, canDelete, canRate,
  };
}