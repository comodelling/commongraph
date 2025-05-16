import { ref, computed } from "vue";
import api from "../axios";

export function useConfig() {
  const nodeTypes = ref<Record<string, string[]>>({});
  const edgeTypes = ref<Record<string, string[]>>({});
  const platformName = ref<string>("");

  async function load() {
    try {
      const { data } = await api.get("/config");
      console.log("Graph config loaded:", data);
      // assume data format: { node_types: { potentiality: [...], ... }, edge_types: { ... } }
      nodeTypes.value = data.node_types;
      edgeTypes.value = data.edge_types;
      platformName.value = data.platform_name;
    } catch (error) {
      console.error("Failed to load meta config", error);
    }
  }
  const defaultNodeType = computed(() => {
    const keys = Object.keys(nodeTypes.value);
    return keys.length ? keys[0] : "";
  });
  const defaultEdgeType = computed(() => {
    const keys = Object.keys(edgeTypes.value);
    const out = keys.length ? keys[0] : "";
    return out;
  });
  return { nodeTypes, edgeTypes, defaultNodeType, defaultEdgeType, platformName, load };
}