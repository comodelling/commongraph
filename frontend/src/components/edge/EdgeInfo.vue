<template>
  <div class="element-info">
    <div class="pane-header">
      <div class="title-group">
        <h4>Edge Info</h4>
      </div>
      <div class="tabs">
        <button
          :class="{ active: currentTab === 'view' }"
          @click="switchTab('view')"
          :disabled="isBrandNewEdge"
          :title="
            isBrandNewEdge
              ? 'View not available for new edges'
              : 'View edge (V)'
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
                ? 'Edit this edge (E)'
                : 'You need edit permissions to modify edges'
          "
        >
          Edit
        </button>
        <button
          :class="{ active: currentTab === 'history' }"
          @click="readOnly ? null : switchTab('history')"
          :disabled="isBrandNewEdge || readOnly"
          :title="
            readOnly
              ? 'History not available in demo mode'
              : isBrandNewEdge
                ? 'History not available for new edges'
                : 'View edge history (H)'
          "
        >
          History
        </button>
      </div>
    </div>
    <!-- <hr class="header-separator" /> -->
    <div v-if="edge">
      <template v-if="currentTab === 'edit'">
        <!-- Add a ref so we can inspect unsaved changes in the edit component -->
        <component
          ref="edgeEdit"
          :is="currentTabComponent"
          :edge="edge"
          :sourceId="edge.source"
          :targetId="edge.target"
          :sourceType="edge.sourceNodeType"
          :targetType="edge.targetNodeType"
          @publish-edge="updateEdgeFromEditor"
          @preview-edge-update="previewEdgeUpdate"
          @edge-exists="handleEdgeExists"
        />
      </template>
      <template v-else>
        <component
          :is="currentTabComponent"
          :edge="edge"
          :sourceId="edge.source"
          :targetId="edge.target"
          :title="currentTab === 'history' ? 'Edge' : undefined"
          @publish-edge="updateEdgeFromEditor"
        />
      </template>
    </div>
    <div v-else>
      <p>Edge not found</p>
    </div>
  </div>
</template>

<script>
import EdgeInfoView from "./EdgeInfoView.vue";
import EdgeInfoEdit from "./EdgeInfoEdit.vue";
import HistoryList from "../common/HistoryList.vue";
import { useConfig } from "../../composables/useConfig";
// import api from "../../api/axios";

export default {
  setup() {
    const { canEdit } = useConfig();
    return { canEdit };
  },
  props: {
    edge: {
      type: Object,
      required: false,
      default: undefined,
    },
    readOnly: {
      type: Boolean,
      default: false,
    },
  },
  emits: ["update-edge-from-editor", "edge-exists"],
  data() {
    return {
      currentTab: this.getCurrentTab(),
      localIsBrandNewEdge: this.edge?.new === true, // track new state locally
    };
  },
  watch: {
    "$route.path"(newPath) {
      this.currentTab = this.getCurrentTab();
    },
  },
  computed: {
    currentTabComponent() {
      if (this.currentTab === "view") return EdgeInfoView;
      if (this.currentTab === "edit") return EdgeInfoEdit;
      if (this.currentTab === "history") return HistoryList;
    },
    isBrandNewEdge() {
      return this.localIsBrandNewEdge;
    },
  },

  mounted() {
    // Add keyboard shortcuts
    window.addEventListener("keydown", this.handleKeyboardShortcut);
  },
  beforeUnmount() {
    window.removeEventListener("keydown", this.handleKeyboardShortcut);
  },

  methods: {
    getCurrentTab() {
      if (this.$route.path.endsWith("/edit")) return "edit";
      if (this.$route.path.endsWith("/history")) return "history";
      return "view";
    },
    switchTab(tab) {
      if (this.currentTab === tab) return;
      if (this.isBrandNewEdge && (tab === "view" || tab === "history")) {
        return;
      }
      // If currently in edit mode, check with the edit component if there are unsaved changes.
      if (
        this.currentTab === "edit" &&
        this.$refs.edgeEdit &&
        this.$refs.edgeEdit.hasLocalUnsavedChanges
      ) {
        if (!window.confirm("You have unsaved edits. Leave without saving?")) {
          return; // stay in edit mode
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
    updateEdgeFromEditor(updatedEdge) {
      this.localIsBrandNewEdge = false; // clear local flag
      this.$emit("update-edge-from-editor", updatedEdge);
      this.switchTab("view");
    },
    previewEdgeUpdate(previewEdge) {
      // Forward preview updates to parent without switching tabs
      this.$emit("preview-edge-update", previewEdge);
    },
    handleEdgeExists(edgeInfo) {
      // Emit event to parent to navigate to the existing edge
      this.$emit("edge-exists", edgeInfo);
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
          if (this.canEdit && !this.readOnly && !this.isBrandNewEdge) {
            event.preventDefault();
            this.switchTab("edit");
          }
          break;
        case "v":
          if (!this.isBrandNewEdge) {
            event.preventDefault();
            this.switchTab("view");
          }
          break;
        case "h":
          if (!this.isBrandNewEdge && !this.readOnly) {
            event.preventDefault();
            this.switchTab("history");
          }
          break;
      }
    },
  },
};
</script>

<style scoped>
.pane-header .tabs {
  margin-right: -20px;
}
</style>
