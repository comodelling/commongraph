<template>
  <div class="side-menu">
    <div class="title">Menu</div>
    <router-link to="/">Main page</router-link><br />
    <a 
      v-if="canRead && canCreate"
      href="#" 
      @click="createNewNode" 
      title="Create a new node"
    >
      New node
    </a><br v-if="canRead && canCreate" />
    <a href="#" @click="fetchRandomNode" v-if="canRead">Random node</a><br v-if="canRead" />
    <!-- <router-link to="/schema">Graph schema</router-link><br /> -->
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
    const { canRead, canCreate } = useConfig();

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
      // if page is favourites or settings, redirect to login
      if (router.currentRoute.value.path === "/favourites" || router.currentRoute.value.path === "/settings" 
          || router.currentRoute.value.path === "/admin/users" || router.currentRoute.value.path.startsWith("/node/new")
          || router.currentRoute.value.path.startsWith("/edge/new")) {
        router.push("/login");
      }
      if (router.currentRoute.value.path.endsWith("/edit")  || router.currentRoute.value.path.endsWith("/edit#")) {
        // remove edit suffix to go back to view
        const newPath = router.currentRoute.value.path.replace(/\/edit#?$/, "");
        router.push(newPath);
      }
    };

    return {
      fetchRandomNode,
      createNewNode,
      logout,
      isLoggedIn,
      isAdmin,
      canRead,
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
  font-size: 13px;
  margin: 0 4px 2px 0;
  line-height: 1.6;
}

.side-menu a,
.side-menu router-link {
  display: inline-block;
  margin-top: 1px;
  margin-bottom: 1px;
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
