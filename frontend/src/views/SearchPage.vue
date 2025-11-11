<template>
  <div class="search-page">
    <div class="search-content">
      <div class="results-column">
        <h2>Search Results</h2>
        <div class="results-list">
          <div v-if="!nodes.length && title" class="no-results">
            <p>
              No results found for:
              <span class="no-results-query">{{ formattedQuery }}</span>
            </p>
            <button
              v-if="canCreate"
              @click="createNodeFromSearch"
              class="create-node-btn"
            >
              Create "{{ formattedQuery }}"
            </button>
            <p v-else class="no-permission-message">
              Log in with create permissions to add new nodes.
            </p>
          </div>
          <ul v-else>
            <div v-for="node in nodes" :key="node.node_id">
              <NodeListItem :node="node" />
            </div>
          </ul>
        </div>
      </div>
      <div class="visualization-column">
        <div class="graph-container">
          <CosmosGraphVis
            :graph-data="subgraphData"
            :height="'300px'"
            :show-controls="true"
            :auto-start-force-atlas="true"
            @node-click="handleNodeClick"
            @edge-click="handleEdgeClick"
            @graph-loaded="handleGraphLoaded"
          />
        </div>

        <AggRatingMultipane
          :nodes="nodes"
          :poll-configs="nodePolls"
          @filter-by-rating="applyRatingFilter"
        />
      </div>
    </div>
  </div>
</template>

<script>
import api from "../api/axios";
import qs from "qs";
import { useRouter, useRoute } from "vue-router";
import { computed } from "vue";
import { useConfig } from "../composables/useConfig";
import RatingHistogram from "../components/poll/RatingHistogram.vue";
import NodeListItem from "../components/node/NodeListItem.vue";
import AggRatingMultipane from "../components/poll/AggRatingMultipane.vue";
import CosmosGraphVis from "../components/graph/GraphVis.vue";

export default {
  components: {
    RatingHistogram,
    NodeListItem,
    AggRatingMultipane,
    CosmosGraphVis,
  },
  data() {
    return {
      title: "",
      nodes: [],
      relationships: [], // Add relationships data
    };
  },
  computed: {
    groupedNodes() {
      return this.nodes.reduce((groups, node) => {
        const scope = node.scope || "Uncategorized";
        if (!groups[scope]) {
          groups[scope] = [];
        }
        groups[scope].push(node);
        return groups;
      }, {});
    },
    subgraphData() {
      if (!this.nodes.length) {
        return { nodes: [], edges: [] };
      }

      // Transform search result nodes into graph format
      const graphNodes = this.nodes.map((node) => ({
        node_id: node.node_id,
        id: node.node_id,
        title: node.title,
        label: node.title,
        node_type: node.node_type,
        scope: node.scope,
      }));

      // Use actual relationships/edges from the API
      const graphEdges = this.relationships.map((rel) => ({
        source_id: rel.source,
        target_id: rel.target,
        edge_type: rel.edge_type || rel.relationship_type || rel.type,
        type: rel.edge_type || rel.relationship_type || rel.type,
      }));

      const result = {
        nodes: graphNodes,
        edges: graphEdges,
      };

      // console.log("subgraphData computed:", result);
      console.log("Raw relationships:", this.relationships);

      return result;
    },
    // Nicely format the incoming title/query which may be an array, JSON string, or comma-separated
    formattedQuery() {
      const q = this.title;
      if (!q && q !== 0) return "";

      // If it's already an array-like string from the router (e.g. ["a","b"]) try to parse JSON
      if (Array.isArray(q)) {
        return q.join(", ");
      }

      if (typeof q === "string") {
        const trimmed = q.trim();
        // Try JSON parse
        try {
          const parsed = JSON.parse(trimmed);
          if (Array.isArray(parsed)) return parsed.join(", ");
          if (typeof parsed === "object" && parsed !== null)
            return JSON.stringify(parsed);
        } catch (e) {
          // not JSON — continue
        }

        // Comma-separated string
        if (trimmed.includes(",")) {
          return trimmed
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean)
            .join(", ");
        }

        return trimmed;
      }

      // Fallback to string conversion
      return String(q);
    },
  },
  watch: {
    "$route.query": {
      immediate: true,
      handler(newQuery) {
        console.log("New query:", newQuery);
        if (!newQuery) return;
        // Handle various query parameter names (q, title, etc.)
        const queryText = newQuery.q || newQuery.title || "";
        this.title = queryText;
        this.performSearch();
      },
    },
  },
  methods: {
    createNodeFromSearch() {
      // Navigate to the node edit page for a new node, passing the search query as title
      const title = this.formattedQuery;

      // Store the title in sessionStorage so ElementFocus can retrieve it
      sessionStorage.setItem("newNodeTitle", title);

      // Navigate to the new node creation route
      this.$router.push({ name: "NodeEdit", params: { id: "new" } });
    },
    applyRatingFilter(rating) {
      // Apply rating filter by updating route query
      const currentQuery = { ...this.$route.query };
      if (rating) {
        currentQuery.rating = rating;
      } else {
        delete currentQuery.rating;
      }
      this.$router.push({ name: "SearchPage", query: currentQuery });
    },
    handleNodeClick(nodeId) {
      console.log("Node clicked in search:", nodeId);
      // Navigate to node focus view
      this.$router.push({ name: "NodeView", params: { id: nodeId } });
    },
    handleEdgeClick(edgeId) {
      console.log("Edge clicked in search:", edgeId);
      // You could show edge details or filter results
    },
    handleGraphLoaded(data) {
      console.log(
        "Search graph loaded with",
        data.nodes?.length,
        "nodes and",
        data.edges?.length,
        "edges",
      );
    },
    async performSearch() {
      try {
        // Handle both 'q' and 'title' query parameters for backwards compatibility
        const query = this.$route.query;
        const title = query.q || query.title;
        const { node_type, edge_type, status, tags, scope, rating } = query;

        const tagsArray = tags
          ? typeof tags === "string"
            ? tags
                .split(",")
                .map((tag) => tag.trim())
                .filter((tag) => tag)
            : tags
          : [];

        if (rating && rating.length) {
          console.warn(
            "rating passed is: ",
            rating,
            " but search currently ignores rating filter",
          );
        }

        console.log("Searching for nodes with:", {
          title,
          node_type,
          edge_type,
          status,
          tags: tagsArray,
          scope,
        });
        const startTime = performance.now();

        // Fetch nodes first (fast response)
        const response = await api.get(`/nodes`, {
          params: {
            title,
            node_type,
            status,
            tags: tagsArray.length ? tagsArray : undefined,
            scope,
          },
          paramsSerializer: (params) =>
            qs.stringify(params, { arrayFormat: "repeat" }),
        });

        this.nodes = response.data;
        this.relationships = []; // Clear previous relationships immediately

        const endTime = performance.now();
        console.log(`Search completed in ${endTime - startTime} milliseconds`);
        console.log(`Found ${this.nodes.length} nodes`);

        // Fetch relationships in the background (non-blocking)
        this.fetchRelationshipsInBackground();
      } catch (error) {
        console.error("Error fetching nodes:", error);
        this.nodes = [];
        this.relationships = [];
      }
    },

    async fetchRelationshipsInBackground() {
      if (this.nodes.length === 0) {
        return;
      }

      const nodeIds = this.nodes.map((node) => node.node_id);
      console.log(
        `Fetching relationships for ${nodeIds.length} nodes in background...`,
      );

      try {
        const relationshipsResponse = await api.get(`/edges`, {
          params: {
            node_ids: nodeIds,
          },
          paramsSerializer: (params) =>
            qs.stringify(params, { arrayFormat: "repeat" }),
        });

        this.relationships = relationshipsResponse.data || [];
        console.log(
          `Loaded ${this.relationships.length} relationships - graph will update automatically`,
        );
      } catch (relError) {
        console.warn("Could not fetch relationships:", relError);
        this.relationships = [];
      }
    },
  },
  setup() {
    const router = useRouter();
    const route = useRoute();
    const { nodePollTypes, canCreate, defaultNodeType } = useConfig();
    const nodePolls = nodePollTypes.value;
    // const nodePolls = computed(() => getNodePolls(defaultNodeType.value));
    return { router, route, nodePolls, canCreate, defaultNodeType };
  },
};
</script>

<style scoped>
.search-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.search-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.results-column {
  flex: 1;
  padding: 10px 0 5px 0px;
  /* padding-left: 100px; */
  /* border-right: 1px solid #ddd; */
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  /* margin:  */
  margin: 2px 2px 4px 2px;
}

.results-column h2 {
  text-align: center;
  margin: 0px 50px;
  padding-bottom: 10px;
  padding-right: 50px;
  border-bottom: 1px solid var(--border-color);
}

.results-list {
  flex: 1;
  overflow-y: auto;
}

.visualization-column {
  flex: 1;
  overflow-y: auto;
  border-radius: 4px;
  margin: 2px 4px 4px 2px;
  display: flex;
  flex-direction: column;
}

.graph-container {
  height: 300px;
  margin-bottom: 10px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  display: flex;
  flex-direction: column;
}

.scope-group {
  margin-bottom: 20px;
}

.node-item {
  cursor: pointer;
  transition: var(--background-color) 0.3s;
  margin-bottom: 5px;
  font-size: 12px;
}

.no-results {
  padding: 12px 16px;
  padding-right: 66px; /* Match the h2's padding-right: 50px + some margin */
  text-align: center;
}

.no-results p {
  margin: 0 0 16px 0;
  color: var(--muted-text-color, #666);
  font-size: 14px;
}

.no-results-query {
  font-weight: 600;
  color: inherit;
}

.create-node-btn {
  padding: 10px 20px;
  background-color: var(--primary-color, #007bff);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition:
    background-color 0.2s,
    transform 0.1s;
}

.create-node-btn:hover {
  background-color: var(--primary-hover-color, #0056b3);
  transform: translateY(-1px);
}

.create-node-btn:active {
  transform: translateY(0);
}

.no-permission-message {
  margin-top: 8px;
  font-size: 13px;
  color: var(--muted-text-color, #999);
  font-style: italic;
}

/* .node-item a {
  text-decoration: none;
} */

/* .node-item a:hover {
  text-decoration: underline;
} */

/* .node-item:hover {
  background-color: #f0f0f0;
} */
</style>
