<template>
  <div class="container">
    <h1>Favourite Nodes</h1>
    <br />
    <div v-if="loading">Loading favourites...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <ul v-else>
      <li v-if="favourites.length === 0">No favourites added yet.</li>
      <li v-for="nodeId in favourites" :key="nodeId">
        <router-link :to="`/node/${nodeId}`">Node {{ nodeId }}</router-link>
      </li>
    </ul>
  </div>
</template>

<script>
import { ref, onMounted } from "vue";
import api from "../axios";

export default {
  setup() {
    const favourites = ref([]);
    const loading = ref(true);
    const error = ref(null);

    const fetchFavourites = async () => {
      try {
        // The /user/me endpoint should return the user preferences, including favourites.
        const response = await api.get("/user/me");
        favourites.value = response.data.preferences?.favourites || [];
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
</style>
