<template>
  <div class="element-info">
    <div class="pane-header">
      <div class="title-group">
        <h4>Node Info</h4>
        <button
          v-if="!isBrandNewNode && node && !readOnly"
          class="favourite-btn header-favourite"
          :title="isFavourite ? 'Remove from favourites' : 'Add to favourites'"
          @click="toggleFavourite"
        >
          {{ isFavourite ? "★" : "☆" }}
        </button>
      </div>
      <div class="tabs">
        <button
          :class="{ active: currentTab === 'view', disabled: isBrandNewNode }"
          @click="switchTab('view')"
          :disabled="isBrandNewNode"
          :title="
            isBrandNewNode
              ? 'View not available for new nodes'
              : 'View node (V)'
          "
        >
          View
        </button>
        <button
          :class="{
            active: currentTab === 'edit',
            disabled: !canEdit || readOnly,
          }"
          @click="canEdit && !readOnly ? switchTab('edit') : null"
          :disabled="!canEdit || readOnly"
          :title="
            readOnly
              ? 'Editing disabled in demo mode'
              : canEdit
                ? 'Edit this node (E)'
                : 'You need edit permissions to modify nodes'
          "
        >
          Edit
        </button>
        <button
          :class="{
            active: currentTab === 'history',
            disabled: isBrandNewNode || readOnly,
          }"
          @click="readOnly ? null : switchTab('history')"
          :disabled="isBrandNewNode || readOnly"
          :title="
            readOnly
              ? 'History not available in demo mode'
              : isBrandNewNode
                ? 'History not available for new nodes'
                : 'View node history (H)'
          "
        >
          History
        </button>
      </div>
    </div>
    <!-- <hr class="header-separator" /> -->
    <div class="tab-content">
      <div v-if="node">
        <template v-if="currentTab === 'edit'">
          <component
            ref="nodeEdit"
            :is="currentTabComponent"
            :node="node"
            :nodeId="node.node_id"
            @publish-node="updateNodeFromEditor"
            @preview-node-update="previewNodeUpdate"
          />
        </template>
        <template v-else>
          <component
            :is="currentTabComponent"
            :node="node"
            :nodeId="node.node_id"
            :is-favourite="isFavourite"
            :is-brand-new-node="isBrandNewNode"
            :toggle-favourite="toggleFavourite"
            @publish-node="updateNodeFromEditor"
          />
        </template>
      </div>
      <div v-else>
        <p>Node not found</p>
      </div>
    </div>
  </div>
</template>

<script>
import NodeInfoView from "./NodeInfoView.vue";
import NodeInfoEdit from "./NodeInfoEdit.vue";
import HistoryList from "../common/HistoryList.vue";
import { useAuth } from "../../composables/useAuth";
import { useConfig } from "../../composables/useConfig";
import api from "../../api/axios";

export default {
  setup() {
    const { canEdit } = useConfig();
    return { canEdit };
  },
  props: {
    node: {
      type: Object,
      required: false,
      default: undefined,
    },
    readOnly: {
      type: Boolean,
      default: false,
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
      if (this.currentTab === "history") return HistoryList;
    },
    isBrandNewNode() {
      return this.node && this.node.node_id === "new";
    },
  },
  mounted() {
    if (this.node && this.node.node_id) {
      this.fetchUserFavourites();
    }
    // Add keyboard shortcuts
    window.addEventListener("keydown", this.handleKeyboardShortcut);
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
  beforeUnmount() {
    window.removeEventListener("keydown", this.handleKeyboardShortcut);
  },
  methods: {
    switchTab(tab) {
      // Prevent switching to view/history if node is brand new
      if (this.isBrandNewNode && (tab === "view" || tab === "history")) {
        return;
      }
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
    previewNodeUpdate(previewNode) {
      // Forward preview updates to parent without switching tabs
      this.$emit("preview-node-update", previewNode);
    },
    handleKeyboardShortcut(event) {
      // Only handle shortcuts if not typing in an input/textarea
      const target = event.target;
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.tagName === "SELECT"
      ) {
        return;
      }

      // Check for modifier keys (Ctrl/Cmd + key) - don't interfere with browser shortcuts
      if (event.ctrlKey || event.metaKey || event.altKey) {
        return;
      }

      switch (event.key.toLowerCase()) {
        case "e":
          if (this.canEdit && !this.readOnly && !this.isBrandNewNode) {
            event.preventDefault();
            this.switchTab("edit");
          }
          break;
        case "v":
          if (!this.isBrandNewNode) {
            event.preventDefault();
            this.switchTab("view");
          }
          break;
        case "h":
          if (!this.isBrandNewNode && !this.readOnly) {
            event.preventDefault();
            this.switchTab("history");
          }
          break;
      }
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
.pane-header .tabs {
  margin-right: -20px;
}
</style>
