<template>
  <div class="side-menu">
    <div class="title">Menu</div>
    <router-link to="/">Main page</router-link><br />
    <a 
      href="#" 
      @click="canCreate ? createNewNode() : null" 
      :class="{ disabled: !canCreate }"
      :title="canCreate ? 'Create a new node' : 'You need create permissions to add new nodes'"
    >
      New node
    </a><br />
    <a href="#" @click="fetchRandomNode">Random node</a><br />
    <router-link to="/schema">Graph schema</router-link><br />
    <router-link to="/about">About</router-link>
    <br /><br />
    <div class="title">User</div>
    <div v-if="!isLoggedIn">
      <router-link to="/login">Log in</router-link><br />
      <router-link to="/signup">Sign up</router-link><br />
    </div>
    <div v-else>
      <router-link to="/favourites">Favourites</router-link><br />
      <router-link to="/settings">Settings</router-link><br />
      <router-link v-if="isAdmin" to="/admin/users">Manage Users<br /></router-link>
      <a href="#" @click="logout">Log out</a>
    </div>
  </div>
</template>

<script>
import { useRouter } from "vue-router";
import { useAuth } from "../../composables/useAuth";
import { useConfig } from "../../composables/useConfig";
import api from "../../api/axios";


export default {
  setup() {
    const router = useRouter();
    const { isLoggedIn, isAdmin, clearTokens } = useAuth();
    const { canCreate } = useConfig();

    const fetchRandomNode = async () => {
      try {
        const response = await api.get(
          `/nodes/random`,
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
      router.push('/login');
    };

    return {
      fetchRandomNode,
      createNewNode,
      logout,
      isLoggedIn,
      isAdmin,
      canCreate,
    };
  },
};
</script>

<style scoped>
.side-menu {
  width: 120px;
  min-width: 100px;
  height: 100%;
  box-sizing: border-box;
  overflow-x: hidden;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  background-color: var(--background-color);
  border-radius: 5px;
  padding: 10px;
  font-size: 12px;
  margin: 0 4px 2px 0;
}
.side-menu .title {
  font-size: 20px;
  font-weight: bold;
}

.side-menu .disabled {
  color: #999;
  cursor: not-allowed;
  text-decoration: none;
}

.side-menu .disabled:hover {
  color: #999;
  text-decoration: none;
}
</style>
