<template>
  <div class="container">
    <h1>Favourite Nodes</h1>
    <br />
    <div v-if="loading">Loading favourites...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="Object.keys(groupedFavourites).length">
        <div
          v-for="(nodes, scope) in groupedFavourites"
          :key="scope"
          class="scope-group"
        >
          <h4>{{ scope }}</h4>
          <ul>
            <NodeListItem
              v-for="node in nodes"
              :key="node.node_id"
              :node="node"
            />
          </ul>
        </div>
      </div>
      <div v-else>No favourites added yet.</div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from "vue";
import api from "../axios";
import NodeListItem from "../components/NodeListItem.vue";

export default {
  components: { NodeListItem },
  setup() {
    const favourites = ref([]);
    const loading = ref(true);
    const error = ref(null);

    const fetchFavourites = async () => {
      try {
        // Get favourite node IDs from the user's preferences
        const response = await api.get("/user/me");
        const favouriteIds = response.data.preferences?.favourites || [];

        // For each favourite id, fetch node details (title and scope).
        const nodes = await Promise.all(
          favouriteIds.map(async (nodeId) => {
            try {
              const res = await api.get(`/node/${nodeId}`);
              return res.data;
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

    const groupedFavourites = computed(() => {
      return favourites.value.reduce((groups, node) => {
        const scope = node.scope || "Uncategorized";
        if (!groups[scope]) {
          groups[scope] = [];
        }
        groups[scope].push(node);
        return groups;
      }, {});
    });

    return { favourites, loading, error, groupedFavourites };
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
.scope-group {
  margin-bottom: 20px;
}
.node-item {
  cursor: pointer;
  margin-bottom: 7px;
  font-size: 13px;
}
</style>
