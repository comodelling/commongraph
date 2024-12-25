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
    </div>
    <!-- <h2>Edge Information</h2> -->
    <div v-if="edge">
      <component
        :is="currentTabComponent"
        :edge="edge"
        @publish="publishEdge"
      />
    </div>
    <div v-else>
      <p>Edge not found</p>
    </div>
  </div>
</template>

<script>
import EdgeInfoRead from "./EdgeInfoRead.vue";
import EdgeInfoEdit from "./EdgeInfoEdit.vue";

export default {
  props: {
    edge: {
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
      this.currentTab = newPath.endsWith("/edit") ? "edit" : "read";
    },
  },
  computed: {
    currentTabComponent() {
      return this.currentTab === "read" ? EdgeInfoRead : EdgeInfoEdit;
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
    publishEdge(updatedEdge) {
      this.$emit("update-edge", updatedEdge);
      this.switchTab("read");
    },
  },
};
</script>
