<template>
  <div class="main-page">
    <!-- Background graph -->
    <div class="graph-background">
      <CosmosGraphVis
        :height="'100%'"
        :show-controls="false"
        opacity-mode="uniform"
        @node-click="handleNodeClick"
        @edge-click="handleEdgeClick"
        @graph-loaded="handleGraphLoaded"
      />
    </div>

    <!-- Foreground content panel -->
    <div class="content-panel">
      <div class="content">
        <router-link :to="{ name: 'About' }" class="platform-link">
          <h1>{{ platformName }}</h1>
        </router-link>
        <p class="tagline">
          {{ platformTagline }}
        </p>

        <p class="instruction">Use the top search bar to get started.</p>
      </div>
    </div>
  </div>
</template>

<script>
import { onMounted } from "vue";
import SearchBar from "../components/common/SearchBar.vue";
import CosmosGraphVis from "../components/graph/GraphVis.vue";
import { buildSearchParams } from "../utils/searchParser.js";
import { useConfig } from "../composables/useConfig";

export default {
  components: { SearchBar, CosmosGraphVis },
  data() {
    return {
      quote: null,
    };
  },
  setup() {
    const { platformName, load, platformTagline } = useConfig();
    onMounted(load);
    return { platformName, platformTagline };
  },
  methods: {
    goToSearch(parsedQuery) {
      const params = buildSearchParams(parsedQuery);
      this.$router.push({ name: "SearchPage", query: params });
    },
    normalizeEdgeEventPayload(payload) {
      if (!payload) return null;
      if (typeof payload === "object" && payload !== null) {
        return {
          id: payload.id ?? null,
          sourceId: payload.sourceId ?? null,
          targetId: payload.targetId ?? null,
          data: payload.data ?? null,
        };
      }

      const stringId = String(payload);
      const match = stringId.match(/^edge_([^_]+)_([^_]+)_/);
      if (!match) {
        return { id: stringId, sourceId: null, targetId: null, data: null };
      }

      return {
        id: stringId,
        sourceId: match[1] ?? null,
        targetId: match[2] ?? null,
        data: null,
      };
    },
    handleNodeClick(nodeId) {
      console.log("Node clicked:", nodeId);
      // Navigate to node focus view
      this.$router.push({ name: "NodeView", params: { id: nodeId } });
    },
    handleEdgeClick(edgeInfo) {
      const payload = this.normalizeEdgeEventPayload(edgeInfo);
      console.log("Edge clicked:", payload);
      if (!payload?.sourceId || !payload?.targetId) {
        console.warn("Unable to navigate without edge endpoints", payload);
        return;
      }

      this.$router.push({
        name: "EdgeView",
        params: {
          source_id: payload.sourceId,
          target_id: payload.targetId,
        },
      });
    },
    handleGraphLoaded(data) {
      console.log(
        "Graph loaded with",
        data.nodes?.length,
        "nodes and",
        data.edges?.length,
        "edges",
      );
    },
  },
};
</script>

<style scoped>
.main-page {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

/* Background graph layer */
.graph-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  opacity: 0.8;
}

/* Foreground content panel */
.content-panel {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 20px;
  pointer-events: none; /* Allow clicks to pass through to graph */
}

.content {
  text-align: center;
  margin: 0 auto;
  max-width: 600px;
  padding: 40px;
  font-size: 1.1rem;
  background-color: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(2px);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.18);
  pointer-events: auto; /* Re-enable clicks on the content box itself */
}

/* Dark mode support */
:global(body.dark) .content {
  background-color: rgba(30, 30, 30, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.tagline {
  font-size: 1.2rem;
  color: var(--text-color);
  font-style: italic;
  opacity: 1;
}

.instruction {
  margin-top: 20px;
  font-size: 1rem;
  color: var(--text-color);
  opacity: 1;
}

.platform-link {
  text-decoration: none;
  color: inherit;
  cursor: pointer;
  transition: color 0.3s ease;
}

.platform-link:hover {
  color: #646cff;
}

.platform-link h1 {
  margin: 0;
  transition: transform 0.3s ease;
  opacity: 1;
}

.platform-link:hover h1 {
  transform: scale(1.05);
}
</style>
