import { ref } from "vue";
import api from "../axios";

export function useMetaConfig() {
  const nodeTypes = ref<Record<string, string[]>>({});
  const edgeTypes = ref<Record<string, string[]>>({});
  async function load() {
    try {
      const { data } = await api.get("/config"); // use the correct endpoint
      console.log("Meta config loaded:", data);
      // assume data should be in the format: { node_types: { potentiality: [...], ... }, edge_types: { ... } }
      nodeTypes.value = data.node_types;
      edgeTypes.value = data.edge_types;
    } catch (error) {
      console.error("Failed to load meta config", error);
    }
  }
  return { nodeTypes, edgeTypes, load };
}