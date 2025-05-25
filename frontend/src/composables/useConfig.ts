import { ref, computed } from "vue";
import api from "../axios";

/* module‐scope singletons */
const nodeTypes     = ref<Record<string, any>>({});
const edgeTypes     = ref<Record<string, any>>({});
const platformName  = ref<string>("");
const configLoaded  = ref(false);

async function load() {
  if (configLoaded.value) return;
  try {
    const { data } = await api.get("/config");
    nodeTypes.value    = data.node_types;
    edgeTypes.value    = data.edge_types;
    platformName.value = data.platform_name;
    configLoaded.value = true;
    console.log("Config loaded:", data);
  } catch (error) {
    console.error("Failed to load meta config", error);
  }
}

const defaultNodeType = computed(() => Object.keys(nodeTypes.value)[0] || "");
const defaultEdgeType = computed(() => Object.keys(edgeTypes.value)[0] || "");


export function useConfig() {
  return {
    nodeTypes,
    edgeTypes,
    platformName,
    configLoaded,
    load,
    defaultNodeType,
    defaultEdgeType,
  };
}