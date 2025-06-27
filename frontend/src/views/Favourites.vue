<template>
  <div class="container">
    <div class="form-wrapper">
      <h2>Favourite Nodes</h2>
      <br />
      <div v-if="loading">Loading favourites...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else>
        <div v-if="favourites.length">
          <ul>
            <NodeListItem
              v-for="node in favourites"
              :key="node.node_id"
              :node="node"
            />
          </ul>
        </div>
        <div v-else>No favourites added yet.</div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from "vue";
import api from "../api/axios";
import NodeListItem from "../components/node/NodeListItem.vue";

export default {
  components: { NodeListItem },
  setup() {
    const favourites = ref([]);
    const loading = ref(true);
    const error = ref(null);

    const fetchFavourites = async () => {
      try {
        // Get favourite node IDs from the user's preferences
        const response = await api.get("/users/me");
        const favouriteIds = response.data.preferences?.favourites || [];

        // For each favourite id, fetch node details (title and scope).
        const nodes = await Promise.all(
          favouriteIds.map(async (nodeId) => {
            try {
              const res = await api.get(`/nodes/${nodeId}/history`);
              console.log("Fetched node details for id", nodeId, res.data[0]);
              let node = res.data[0].payload;
              node.last_modified = res.data[0].timestamp;
              console.log("Node payload:", node);
              return node;
            } catch (err) {
              console.error("Error fetching node details for id", nodeId);
              return { node_id: nodeId, title: `Node ${nodeId}`, scope: "" };
            }
          }),
        );
        favourites.value = nodes;
      } catch (err) {
        error.value = "Failed to load favourites.";
      } finally {
        loading.value = false;
      }
    };

    onMounted(() => {
      fetchFavourites();
    });

    return { favourites, loading, error };
  },
};
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.error {
  color: red;
}
.node-item {
  cursor: pointer;
  margin-bottom: 7px;
  font-size: 13px;
}
</style>