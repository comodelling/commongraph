<template>
  <div class="main-page">
    <div class="content">
      <router-link :to="{ name: 'About' }" class="platform-link">
        <h1>{{ platformName }}</h1>
      </router-link>
      <p class="tagline">
        {{ tagline }}
      </p>
      <!-- <div class="search-container">
        <SearchBar
          class="wide-search"
          @search="goToSearch"
          style="max-width: 600px; width: 450px"
        />
      </div>
      <div class="graph-container">
        <SigmaGraphVis
          :height="'500px'"
          :show-controls="true"
          :auto-start-force-atlas="true"
          @node-click="handleNodeClick"
          @edge-click="handleEdgeClick"
          @graph-loaded="handleGraphLoaded"
        />
      </div> -->
    </div>
  </div>
</template>

<script>
import { onMounted } from "vue";
import SearchBar from "../components/common/SearchBar.vue";
import SigmaGraphVis from "../components/graph/SigmaGraphVis.vue";
import { buildSearchParams } from "../utils/searchParser.js";
import { useConfig } from "../composables/useConfig";

export default {
  components: { SearchBar },
  data() {
    return {
      quote: null,
    };
  },
  setup() {
    const { platformName, load, tagline } = useConfig();
    onMounted(load);
    return { platformName, tagline };
  },
  methods: {
    goToSearch(parsedQuery) {
      const params = buildSearchParams(parsedQuery);
      this.$router.push({ name: "SearchPage", query: params });
    },
    handleNodeClick(nodeId) {
      console.log("Node clicked:", nodeId);
      // Navigate to node focus view
      this.$router.push({ name: "NodeView", params: { id: nodeId } });
    },
    handleEdgeClick(edgeId) {
      console.log("Edge clicked:", edgeId);
      // Handle edge click - you might need to parse edge ID to get source/target
    },
    handleGraphLoaded(data) {
      console.log("Graph loaded with", data.nodes?.length, "nodes and", data.edges?.length, "edges");
    }
  },
};
</script>

<style scoped>
.main-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.content {
  text-align: center;
  margin: 0 auto;
  max-width: 600px;
  padding: 0 20px;
}

.tagline {
  font-size: 1.25rem;
  margin-bottom: 1.5rem;
}

.search-container {
  display: flex;
  justify-content: center;
  margin-bottom: 30px;
  margin-top: 40px;
}

.graph-container {
  display: flex;
  justify-content: center;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.platform-link {
  text-decoration: none;
  color: inherit;
  cursor: pointer;
}
</style>
