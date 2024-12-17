<template>
  <div class="side-menu">
    <div class="title">Menu</div>
    <router-link to="/">Main page</router-link><br />
    <a href="#" @click="createNewNode">New node</a><br />
    <a href="#" @click="fetchRandomNode">Random node</a><br />
    <router-link to="/about">About ObjectiveNet</router-link>
  </div>
</template>

<script>
import axios from "axios";
import { useRouter } from "vue-router";

export default {
  setup() {
    const router = useRouter();

    const fetchRandomNode = async () => {
      try {
        const response = await axios.get(
          `${import.meta.env.VITE_BACKEND_URL}/nodes/random`,
        );
        const node = response.data;
        window.location.href = `/node/${node.node_id}`;
      } catch (error) {
        console.error("Error fetching random node:", error);
      }
    };

    const createNewNode = async () => {
      const path = router.currentRoute.value.path;
      if (path.startsWith("/node") || path.startsWith("/edge")) {
        window.location.href = `/node/new`;
      } else {
        router.push(`/node/new`);
      }
    };
    return {
      fetchRandomNode: fetchRandomNode,
      createNewNode,
    };
  },
};
</script>

<style scoped>
.side-menu {
  width: 150px;
  min-width: 150px;
  height: 90vh;
  border: 1px solid #ccc;
  padding: 10px;
  font-size: 12px;
  margin-left: 10px;
  margin-top: 20px;
  padding-top: 50px;
}
.side-menu .title {
  font-size: 20px;
  font-weight: bold;
}
</style>
