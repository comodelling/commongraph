<template>
  <div class="element-info">
    <div class="tabs">
      <button
        :class="{ active: currentTab === 'read' }"
        @click="switchTab('read')"
      >
        Read
      </button>
      <button
        :class="{ active: currentTab === 'edit' }"
        @click="switchTab('edit')"
      >
        Edit
      </button>
    </div>
    <!-- <h2>Node Information</h2> -->
    <div v-if="node">
      <component
        :is="currentTabComponent"
        :node="node"
        @publish="publishNode"
      />
    </div>
    <div v-else>
      <p>Node not found</p>
    </div>
  </div>
</template>

<script>
import NodeInfoRead from "./NodeInfoRead.vue";
import NodeInfoEdit from "./NodeInfoEdit.vue";

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
      currentTab: this.$route.path.endsWith("/edit") ? "edit" : "read",
    };
  },
  watch: {
    "$route.path"(newPath) {
      // Ensure it only watches for node routes updates
      if (newPath.includes("/node")) {
        this.currentTab = newPath.endsWith("/edit") ? "edit" : "read";
      }
    },
  },
  computed: {
    currentTabComponent() {
      return this.currentTab === "read" ? NodeInfoRead : NodeInfoEdit;
    },
  },
  methods: {
    switchTab(tab) {
      if (this.currentTab === tab) return;
      this.currentTab = tab;
      if (tab === "edit") {
        this.$router.push(`${this.$route.path}/edit`);
      } else {
        const path = this.$route.path.split("/edit")[0];
        this.$router.push(path);
      }
    },
    publishNode(updatedNode) {
      this.$emit("update-node", updatedNode);
      this.switchTab("read");
    },
  },
};
</script>
