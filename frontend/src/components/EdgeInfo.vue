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
    <div v-if="edge">
      <component
        :is="currentTabComponent"
        :edge="edge"
        :sourceId="edge.source"
        :targetId="edge.target"
        @publish-edge="updateEdgeFromEditor"
      />
    </div>
    <div v-else>
      <p>Edge not found</p>
    </div>
  </div>
</template>

<script>
import EdgeInfoView from "./EdgeInfoView.vue";
import EdgeInfoEdit from "./EdgeInfoEdit.vue";
import EdgeHistory from "./EdgeHistory.vue";

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
      if (this.currentTab === "history") return EdgeHistory;
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
    updateEdgeFromEditor(updatedEdge) {
      this.$emit("update-edge-from-editor", updatedEdge);
      this.switchTab("view");
    },
  },
};
</script>
