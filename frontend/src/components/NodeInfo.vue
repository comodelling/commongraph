<template>
  <div class="element-info">
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
      <component
        :is="currentTabComponent"
        :node="node"
        :nodeId="node.node_id"
        @publish-node="updateNodeFromEditor"
      />
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
    };
  },
  computed: {
    currentTabComponent() {
      if (this.currentTab === "view") return NodeInfoView;
      if (this.currentTab === "edit") return NodeInfoEdit;
      if (this.currentTab === "history") return NodeHistoryView;
    },
  },
  watch: {
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
    getCurrentTab() {
      if (this.$route.path.endsWith("/edit")) return "edit";
      if (this.$route.path.endsWith("/history")) return "history";
      return "view";
    },
    switchTab(tab) {
      if (this.currentTab === tab) return;
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
  },
};
</script>
