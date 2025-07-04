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
            :disabled="isBrandNewEdge"
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
// import api from "../../api/axios";

export default {
  props: {
    edge: {
      type: Object,
      required: false,
      default: undefined,
    },
  },
  emits: ["update-edge-from-editor"],
  data() {
    return {
      currentTab: this.getCurrentTab(),
      localIsBrandNewEdge: this.edge?.new === true,  // track new state locally
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
      this.localIsBrandNewEdge = false;  // clear local flag
      this.$emit("update-edge-from-editor", updatedEdge);
      this.switchTab("view");
    },
  },
};
</script>

<style scoped>

.pane-header .tabs {
  margin-right: -20px;
}

</style>