<template>
  <div class="element-info">
    <div class="favourite-toggle">
      <button class="favourite-btn" @click="toggleFavourite">
        {{ isFavourite ? "★" : "☆" }}
      </button>
    </div>
    <div class="tabs">
      <button
        :class="{ active: currentTab === 'view' }"
        @click="switchTab('view')"
      >
        View
      </button>
      <button
        :class="{ active: currentTab === 'edit' }"
        @click="switchTab('edit')"
      >
        Edit
      </button>
      <button
        :class="{ active: currentTab === 'history' }"
        @click="switchTab('history')"
      >
        History
      </button>
    </div>
    <div v-if="node">
      <template v-if="currentTab === 'edit'">
        <component
          ref="nodeEdit"
          :is="currentTabComponent"
          :node="node"
          :nodeId="node.node_id"
          @publish-node="updateNodeFromEditor"
        />
      </template>
      <template v-else>
        <component
          :is="currentTabComponent"
          :node="node"
          :nodeId="node.node_id"
          @publish-node="updateNodeFromEditor"
        />
      </template>
    </div>
    <div v-else>
      <p>Node not found</p>
    </div>
  </div>
</template>

<script>
import NodeInfoView from "./NodeInfoView.vue";
import NodeInfoEdit from "./NodeInfoEdit.vue";
import NodeHistoryView from "./NodeHistory.vue";
import { useAuth } from "../composables/useAuth";
import api from "../axios";

export default {
  props: {
    node: {
      type: Object,
      required: false,
      default: undefined,
    },
  },
  data() {
    return {
      currentTab: this.$route.path.endsWith("/edit")
        ? "edit"
        : this.$route.path.endsWith("/history")
          ? "history"
          : "view",
      isFavourite: false,
      userFavourites: [],
    };
  },
  computed: {
    currentTabComponent() {
      if (this.currentTab === "view") return NodeInfoView;
      if (this.currentTab === "edit") return NodeInfoEdit;
      if (this.currentTab === "history") return NodeHistoryView;
    },
  },
  mounted() {
    if (this.node && this.node.node_id) {
      this.fetchUserFavourites();
    }
  },
  watch: {
    node(newVal) {
      if (newVal && newVal.node_id) {
        this.fetchUserFavourites();
      }
    },
    "$route.path"(newPath) {
      if (newPath.includes("/node")) {
        if (newPath.endsWith("/edit")) {
          this.currentTab = "edit";
        } else if (newPath.endsWith("/history")) {
          this.currentTab = "history";
        } else {
          this.currentTab = "view";
        }
      }
    },
  },
  methods: {
    switchTab(tab) {
      if (this.currentTab === "edit" && this.$refs.nodeEdit) {
        if (this.$refs.nodeEdit.hasLocalUnsavedChanges) {
          if (
            !window.confirm("You have unsaved edits. Leave without saving?")
          ) {
            return;
          }
        }
      }
      this.currentTab = tab;
      const basePath = this.$route.path.split("/edit")[0].split("/history")[0];
      if (tab === "edit") {
        this.$router.push(`${basePath}/edit`);
      } else if (tab === "history") {
        this.$router.push(`${basePath}/history`);
      } else {
        this.$router.push(basePath);
      }
    },
    updateNodeFromEditor(updatedNode) {
      this.$emit("update-node-from-editor", updatedNode);
      this.switchTab("view");
    },
    fetchUserFavourites() {
      const { getAccessToken } = useAuth();
      const token = getAccessToken();
      if (!token) return;
      api
        .get(`/users/me`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        .then((response) => {
          this.userFavourites = response.data.preferences?.favourites || [];
          this.isFavourite = this.userFavourites.includes(this.node.node_id);
        })
        .catch((err) => {
          console.error("Failed to fetch favourites:", err);
        });
    },
    toggleFavourite() {
      const { getAccessToken } = useAuth();
      const token = getAccessToken();
      if (!token) {
        window.alert("You must be logged in to update favourites.");
        return;
      }
      let updatedFavourites;
      if (this.isFavourite) {
        updatedFavourites = this.userFavourites.filter(
          (id) => id !== this.node.node_id,
        );
      } else {
        updatedFavourites = [...this.userFavourites, this.node.node_id];
      }
      api
        .patch(
          `/users/preferences`,
          { favourites: updatedFavourites },
          { headers: { Authorization: `Bearer ${token}` } },
        )
        .then((response) => {
          this.userFavourites = response.data.preferences.favourites;
          this.isFavourite = this.userFavourites.includes(this.node.node_id);
        })
        .catch((err) => {
          console.error("Failed to update favourites:", err);
          window.alert("Failed to update favourites.");
        });
    },
  },
};
</script>

<style scoped>
.element-info {
  position: relative;
  padding-top: 2rem;
}

/* Favourite toggle style */
.favourite-toggle {
  position: absolute;
  top: -17px; /* Adjust as needed */
  right: -23px; /* Adjust as needed */
}
.favourite-btn {
  background: none;
  border: none;
  font-size: 1.2rem; /* Smaller star */
  cursor: pointer;
  color: gold;
}
.favourite-btn:hover {
  opacity: 0.8;
}

/* Tabs styles (unchanged) */
.tabs {
  position: absolute;
  top: -10px;
  left: -10px;
}
.tabs button {
  flex: 1;
  padding: 3px 10px;
  cursor: pointer;
  background: none;
  border-radius: 3px;
  border-bottom: 1px solid var(--border-color);
  font-size: 11px;
}
.tabs button.active {
  border-bottom: 2px solid #007bff;
  font-weight: bold;
}
</style>
