<template>
  <div class="side-menu">
    <div class="title">Menu</div>
    <router-link to="/">Main page</router-link><br />
    <a href="#" @click="createNewNode">New node</a><br />
    <a href="#" @click="fetchRandomNode">Random node</a><br />
    <router-link to="/about">About ObjectiveNet</router-link>
    <br /><br />
    <div class="title">User</div>
    <div v-if="!isLoggedIn">
      <router-link to="/login">Log in</router-link><br />
      <router-link to="/signup">Sign up</router-link><br />
    </div>
    <div v-else>
      <router-link to="/settings">Settings</router-link><br />
      <a href="#" @click="logout">Log out</a>
    </div>
  </div>
</template>

<script>
import api from "../axios";
import { useRouter } from "vue-router";
import { useAuth } from "../composables/useAuth";

export default {
  setup() {
    const router = useRouter();
    const { isLoggedIn, clearTokens } = useAuth();
    console.log("isLoggedIn", isLoggedIn);

    const fetchRandomNode = async () => {
      try {
        const response = await api.get(
          `${import.meta.env.VITE_BACKEND_URL}/node/random`,
        );
        const node = response.data;
        const path = router.currentRoute.value.path;
        if (path.startsWith("/node") || path.startsWith("/edge")) {
          window.location.href = `/node/${node.node_id}`;
        } else {
          router.push({ name: "NodeView", params: { id: node.node_id } });
        }
      } catch (error) {
        console.error("Error fetching random node:", error);
      }
    };

    const createNewNode = async () => {
      const path = router.currentRoute.value.path;
      if (path.startsWith("/node") || path.startsWith("/edge")) {
        window.location.href = `/node/new`;
      } else {
        router.push({ name: "NodeEdit", params: { id: "new" } });
      }
    };

    const logout = () => {
      clearTokens();
      router.push("/login");
    };

    return {
      fetchRandomNode,
      createNewNode,
      logout,
      isLoggedIn,
    };
  },
};
</script>

<style scoped>
.side-menu {
  width: 150px;
  min-width: 150px;
  height: calc(100vh - 4px);
  box-sizing: border-box;
  /* box-sizing: border-box; */
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: 5px;
  padding: 10px;
  font-size: 12px;
  margin: 2px;
  padding-top: 50px;
}
.side-menu .title {
  font-size: 20px;
  font-weight: bold;
}
</style>
