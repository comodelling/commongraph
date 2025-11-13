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
              <NodeListItem
                :node="node"
                @hover="handleNodeItemHover"
                @leave="handleNodeItemLeave"
              />
            </div>
          </ul>
        </div>
      </div>
      <div class="visualization-column">
        <div class="graph-container">
          <div
            class="viz-header"
            :class="{ 'has-compass': activeTab === 'flow' }"
          >
            <div class="viz-tabs">
              <button
                :class="['tab-button', { active: activeTab === 'flow' }]"
                @click="selectTab('flow')"
                title="Flow View"
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <rect
                    x="1"
                    y="5"
                    width="4"
                    height="6"
                    rx="0.5"
                    stroke="currentColor"
                    stroke-width="1.5"
                    fill="none"
                  />
                  <rect
                    x="11"
                    y="5"
                    width="4"
                    height="6"
                    rx="0.5"
                    stroke="currentColor"
                    stroke-width="1.5"
                    fill="none"
                  />
                  <line
                    x1="5"
                    y1="8"
                    x2="11"
                    y2="8"
                    stroke="currentColor"
                    stroke-width="1.8"
                  />
                  <path
                    d="M 9 6 L 11 8 L 9 10"
                    stroke="currentColor"
                    stroke-width="1.8"
                    fill="none"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </button>
              <button
                :class="['tab-button', { active: activeTab === 'graph' }]"
                @click="selectTab('graph')"
                title="Graph View"
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <circle cx="4" cy="4" r="2" fill="currentColor" />
                  <circle cx="12" cy="4" r="2" fill="currentColor" />
                  <circle cx="8" cy="12" r="2" fill="currentColor" />
                  <line
                    x1="6"
                    y1="4"
                    x2="10"
                    y2="4"
                    stroke="currentColor"
                    stroke-width="1.5"
                  />
                  <line
                    x1="5.4"
                    y1="5.4"
                    x2="6.6"
                    y2="10.6"
                    stroke="currentColor"
                    stroke-width="1.5"
                  />
                  <line
                    x1="10.6"
                    y1="5.4"
                    x2="9.4"
                    y2="10.6"
                    stroke="currentColor"
                    stroke-width="1.5"
                  />
                </svg>
              </button>
              <button
                class="tab-button disabled"
                disabled
                title="Map View (Coming Soon)"
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M2 12 L6 10 L10 12 L14 10 V4 L10 6 L6 4 L2 6 Z"
                    fill="currentColor"
                    opacity="0.3"
                  />
                  <path
                    d="M6 4 V10 M10 6 V12"
                    stroke="currentColor"
                    stroke-width="1.5"
                  />
                  <path
                    d="M2 6 L6 4 L10 6 L14 4"
                    stroke="currentColor"
                    stroke-width="1.5"
                    fill="none"
                  />
                </svg>
              </button>
            </div>
            <div class="viz-controls">
              <GraphControls
                :depth="depthLevel"
                :color-by="colorBy"
                @update:depth="updateDepth"
                @update:colorBy="updateColorBy"
              />
            </div>
          </div>
          <CosmosGraphVis
            v-if="activeTab === 'graph'"
            :graph-data="subgraphData"
            :show-controls="false"
            @node-click="handleNodeClick"
            @edge-click="handleEdgeClick"
            @graph-loaded="handleGraphLoaded"
          />
          <FlowEditor
            v-else-if="activeTab === 'flow'"
            :data="flowSubgraphData"
            :read-only="true"
            :highlighted-node-id="hoveredNodeId"
            :fit-trigger="flowFitTick"
            @nodeClick="handleNodeClick"
            @edgeClick="handleEdgeClick"
          />
        </div>

        <!-- <AggRatingMultipane
          :nodes="nodes"
          :poll-configs="nodePolls"
          @filter-by-rating="applyRatingFilter"
        /> -->
      </div>
    </div>
  </div>
</template>

<script>
import api from "../api/axios";
import qs from "qs";
import { useRouter, useRoute } from "vue-router";
import { useConfig } from "../composables/useConfig";
import {
  formatFlowNodeProps,
  formatFlowEdgeProps,
} from "../composables/formatFlowComponents";
import RatingHistogram from "../components/poll/RatingHistogram.vue";
import NodeListItem from "../components/node/NodeListItem.vue";
import AggRatingMultipane from "../components/poll/AggRatingMultipane.vue";
import CosmosGraphVis from "../components/graph/GraphVis.vue";
import FlowEditor from "../components/graph/FlowEditor.vue";
import GraphControls from "../components/graph/GraphControls.vue";

export default {
  components: {
    RatingHistogram,
    NodeListItem,
    AggRatingMultipane,
    CosmosGraphVis,
    FlowEditor,
    GraphControls,
  },
  data() {
    return {
      title: "",
      nodes: [],
      relationships: [], // Edges from the subgraph
      subgraphNodes: [], // All nodes from subgraph (search results + connected nodes)
      activeTab: "graph", // Current visualization tab
      hoveredNodeId: null,
      userSelectedTab: false,
      flowFitTick: 0,
      depthLevel: parseInt(localStorage.getItem("graphDepthLevel")) || 1, // Depth level for subgraph traversal
      colorBy: localStorage.getItem("graphColorBy") || "type", // Color nodes/edges by 'type' or 'rating'
      ratings: {}, // Store node ratings fetched from API
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

      // If we have subgraph nodes from the API, use those (they include search results + connected nodes)
      // Otherwise, just use the search results
      let nodesToUse = this.nodes;
      if (this.subgraphNodes.length > 0) {
        nodesToUse = this.subgraphNodes;
      }

      // Create a Set of search result node IDs for marking
      const searchResultIds = new Set(this.nodes.map((n) => n.node_id));

      // Transform all nodes into graph format
      const graphNodes = nodesToUse.map((node) => ({
        node_id: node.node_id,
        id: node.node_id,
        title: node.title || `Node ${node.node_id}`,
        label: node.title || `Node ${node.node_id}`,
        node_type: node.node_type || "unknown",
        scope: node.scope || "",
        support: node.support, // Include rating for color-by-rating mode
        ratingLabel: node.ratingLabel || null,
        isSearchResult: searchResultIds.has(node.node_id),
      }));

      // Use actual relationships/edges from the API
      const graphEdges = this.relationships.map((rel) => ({
        source: rel.source,
        target: rel.target,
        source_id: rel.source,
        target_id: rel.target,
        edge_type:
          rel.edge_type || rel.relationship_type || rel.type || "unknown",
        type: rel.edge_type || rel.relationship_type || rel.type || "unknown",
        causal_strength: rel.causal_strength, // Include rating for color-by-rating mode
        ratingLabel: rel.ratingLabel || null,
      }));

      const result = {
        nodes: graphNodes,
        edges: graphEdges,
      };

      console.log(
        "subgraphData:",
        result.nodes.length,
        "nodes,",
        result.edges.length,
        "edges",
      );
      console.log(
        "Search results:",
        this.nodes.length,
        "Subgraph nodes:",
        this.subgraphNodes.length,
      );
      if (result.nodes.length > 0) {
        console.log("Sample node:", JSON.stringify(result.nodes[0]));
        console.log(
          "All node IDs:",
          result.nodes.map((n) => n.node_id),
        );
      }
      if (result.edges.length > 0) {
        console.log("Sample edge:", JSON.stringify(result.edges[0]));
        console.log(
          "All edge sources:",
          result.edges.map((e) => e.source),
        );
        console.log(
          "All edge targets:",
          result.edges.map((e) => e.target),
        );
      }

      return result;
    },
    searchResultIdSet() {
      return new Set(
        this.nodes
          .map((node) => Number(node.node_id ?? node.id))
          .filter((id) => Number.isFinite(id)),
      );
    },
    flowSubgraphData() {
      const nodesSource = this.subgraphNodes.length
        ? this.subgraphNodes
        : this.nodes;

      if (!nodesSource.length) {
        return { nodes: [], edges: [] };
      }

      console.log("flowSubgraphData computed - colorBy:", this.colorBy);

      const formattedNodes = nodesSource
        .map((node) => {
          const nodeId = Number(node.node_id ?? node.id);
          if (!Number.isFinite(nodeId)) {
            return null;
          }

          const enrichedNode = {
            ...node,
            node_id: nodeId,
            title: node.title || `Node ${nodeId}`,
          };

          const formatted = formatFlowNodeProps(enrichedNode, this.colorBy);
          const isSearchResult = this.searchResultIdSet.has(nodeId);

          formatted.data = {
            ...formatted.data,
            isSearchResult,
          };
          if (!formatted.label) {
            formatted.label = enrichedNode.title;
          }

          if (!isSearchResult) {
            const baseOpacityRaw = formatted.style?.opacity;
            const baseOpacity =
              typeof baseOpacityRaw === "number"
                ? baseOpacityRaw
                : parseFloat(baseOpacityRaw) || 0.95;
            formatted.style = {
              ...formatted.style,
              opacity: Math.min(baseOpacity, 0.35),
            };
          }

          const classTokens = [formatted.class];
          classTokens.push(
            isSearchResult ? "flow-node-search-result" : "flow-node-connector",
          );
          formatted.class = classTokens.filter(Boolean).join(" ");

          return formatted;
        })
        .filter(Boolean);

      const formattedEdges = this.relationships
        .map((rel) => {
          const sourceId = Number(rel.source ?? rel.source_id);
          const targetId = Number(rel.target ?? rel.target_id);
          if (!Number.isFinite(sourceId) || !Number.isFinite(targetId)) {
            return null;
          }

          const edgeType =
            rel.edge_type || rel.relationship_type || rel.type || "unknown";

          const formatted = formatFlowEdgeProps(
            {
              ...rel,
              source: sourceId,
              target: targetId,
              edge_type: edgeType,
            },
            this.colorBy,
          );

          const sourceIsSearch = this.searchResultIdSet.has(sourceId);
          const targetIsSearch = this.searchResultIdSet.has(targetId);

          const edgeClassTokens = [formatted.class];
          if (!sourceIsSearch || !targetIsSearch) {
            const baseOpacityRaw = formatted.style?.opacity;
            const baseOpacity =
              typeof baseOpacityRaw === "number"
                ? baseOpacityRaw
                : parseFloat(baseOpacityRaw) || 1;
            formatted.style = {
              ...formatted.style,
              opacity: Math.min(baseOpacity, 0.35),
            };
            edgeClassTokens.push("flow-edge-connector");
          } else {
            edgeClassTokens.push("flow-edge-search-result");
          }
          formatted.class = edgeClassTokens.filter(Boolean).join(" ");

          return formatted;
        })
        .filter(Boolean);

      console.log(
        "flowSubgraphData - formatted",
        formattedNodes.length,
        "nodes with colorBy:",
        this.colorBy,
      );
      if (formattedNodes.length > 0) {
        console.log("Sample node style:", formattedNodes[0].style);
      }

      return { nodes: formattedNodes, edges: formattedEdges };
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
    activeTab(newVal, oldVal) {
      if (newVal === "flow" && oldVal !== "flow") {
        this.requestFlowFit();
      }
    },
  },
  methods: {
    normalizeTypeName(type) {
      if (!type && type !== 0) {
        return null;
      }
      return String(type).trim().toLowerCase();
    },
    resolveNodePollLabel(node) {
      if (!node) {
        return null;
      }
      const directLabel =
        node.ratingLabel || node.poll_label || node.default_poll_label || null;
      if (directLabel) {
        return directLabel;
      }

      const availableLabels = Array.isArray(node.available_poll_labels)
        ? node.available_poll_labels
        : Array.isArray(node.poll_labels)
          ? node.poll_labels
          : null;
      if (availableLabels && availableLabels.length) {
        return availableLabels[0];
      }

      const nodeType = node.node_type;
      if (!nodeType) {
        return null;
      }

      const candidateFromGetter = this.getNodePolls
        ? Object.keys(this.getNodePolls(nodeType) || {})
        : [];
      if (candidateFromGetter.length) {
        return candidateFromGetter[0];
      }

      const normalizedType = this.normalizeTypeName(nodeType);
      if (!normalizedType) {
        return null;
      }

      const pollsByType = this.nodePollsByType || {};
      const matchedByType = Object.entries(pollsByType).find(
        ([type]) => this.normalizeTypeName(type) === normalizedType,
      );
      if (matchedByType) {
        const [_, pollConfig] = matchedByType;
        const labels = Object.keys(pollConfig || {});
        if (labels.length) {
          return labels[0];
        }
      }

      const allNodePollTypes = this.nodePollTypes || {};
      const fromGlobal = Object.entries(allNodePollTypes).find(
        ([, poll]) =>
          Array.isArray(poll?.node_types) &&
          poll.node_types.some(
            (type) => this.normalizeTypeName(type) === normalizedType,
          ),
      );
      if (fromGlobal) {
        return fromGlobal[0];
      }

      return null;
    },
    resolveEdgePollLabel(edge) {
      if (!edge) {
        return null;
      }
      const directLabel =
        edge.ratingLabel || edge.poll_label || edge.default_poll_label || null;
      if (directLabel) {
        return directLabel;
      }

      const availableLabels = Array.isArray(edge.available_poll_labels)
        ? edge.available_poll_labels
        : Array.isArray(edge.poll_labels)
          ? edge.poll_labels
          : null;
      if (availableLabels && availableLabels.length) {
        return availableLabels[0];
      }

      const edgeType = edge.edge_type || edge.type;
      if (!edgeType) {
        return null;
      }

      const candidateFromGetter = this.getEdgePolls
        ? Object.keys(this.getEdgePolls(edgeType) || {})
        : [];
      if (candidateFromGetter.length) {
        return candidateFromGetter[0];
      }

      const normalizedType = this.normalizeTypeName(edgeType);
      if (!normalizedType) {
        return null;
      }

      const pollsByType = this.edgePollsByType || {};
      const matchedByType = Object.entries(pollsByType).find(
        ([type]) => this.normalizeTypeName(type) === normalizedType,
      );
      if (matchedByType) {
        const [_, pollConfig] = matchedByType;
        const labels = Object.keys(pollConfig || {});
        if (labels.length) {
          return labels[0];
        }
      }

      const allEdgePollTypes = this.edgePollTypes || {};
      const fromGlobal = Object.entries(allEdgePollTypes).find(
        ([, poll]) =>
          Array.isArray(poll?.edge_types) &&
          poll.edge_types.some(
            (type) => this.normalizeTypeName(type) === normalizedType,
          ),
      );
      if (fromGlobal) {
        return fromGlobal[0];
      }

      return null;
    },
    selectTab(tab) {
      if (tab === this.activeTab) return;
      this.userSelectedTab = true;
      this.activeTab = tab;
    },
    requestFlowFit() {
      this.flowFitTick += 1;
    },
    async fetchNodeRatings(nodeIds) {
      if (!nodeIds.length) return;
      try {
        console.log("Fetching node ratings for IDs:", nodeIds);
        const { data } = await api.get("/nodes/ratings/median", {
          params: { node_ids: nodeIds },
        });
        console.log("Raw node ratings:", data);
        this.ratings = data;
      } catch (err) {
        console.error("Error fetching node ratings:", err);
      }
    },
    async fetchEdgeRatings(edges) {
      if (!edges.length) return edges;
      const groupedByPoll = new Map();

      edges.forEach((edge) => {
        const pollLabel = this.resolveEdgePollLabel(edge);
        edge.ratingLabel = pollLabel;
        edge.causal_strength = null;

        if (!pollLabel) {
          return;
        }

        if (!groupedByPoll.has(pollLabel)) {
          groupedByPoll.set(pollLabel, []);
        }
        groupedByPoll.get(pollLabel).push(edge);
      });

      try {
        for (const [pollLabel, edgesForPoll] of groupedByPoll.entries()) {
          const edgeKeys = edgesForPoll.map((e) => `${e.source}-${e.target}`);
          const { data: edgeRatings } = await api.get("/edges/ratings/median", {
            params: { edge_ids: edgeKeys, poll_label: pollLabel },
          });

          edgesForPoll.forEach((edge) => {
            const key = `${edge.source}-${edge.target}`;
            const ratingEntry = edgeRatings[key] ?? null;
            const ratingValue = this.resolveRatingValue(
              ratingEntry,
              "median_rating",
            );
            edge.causal_strength = ratingValue;
          });
        }
      } catch (err) {
        console.error("Error fetching edge ratings:", err);
      }

      return edges;
    },
    updateNodesWithRatings(rawNodes) {
      console.log(
        "updateNodesWithRatings called with",
        rawNodes.length,
        "nodes",
      );
      console.log("Current ratings object:", this.ratings);
      return rawNodes.map((node) => {
        const nodeSpecificLabel =
          node.ratingLabel ||
          node.poll_label ||
          node.default_poll_label ||
          null;
        const pollLabel = nodeSpecificLabel || this.resolveNodePollLabel(node);
        const ratingEntry = this.ratings[node.node_id];
        const ratingValue = this.resolveRatingValue(ratingEntry, pollLabel);

        console.log(
          `Node ${node.node_id}: pollLabel=`,
          pollLabel,
          "ratingEntry=",
          ratingEntry,
          "resolved rating=",
          ratingValue,
        );

        let ratingLabel = pollLabel || nodeSpecificLabel || null;
        if (!ratingLabel && ratingEntry && typeof ratingEntry === "object") {
          const candidateKey = Object.keys(ratingEntry).find(
            (key) => key !== "median_rating" && ratingEntry[key] != null,
          );
          if (candidateKey) {
            ratingLabel = candidateKey;
          }
        }
        if (!ratingLabel && ratingValue != null) {
          ratingLabel = "rating";
        }

        if (ratingValue != null) {
          node.support = ratingValue;
        } else {
          delete node.support;
        }

        node.ratingLabel = ratingLabel || null;

        return node;
      });
    },
    resolveRatingValue(entry, keyPreference) {
      if (entry == null) {
        return null;
      }

      if (typeof entry === "number") {
        return Number(entry);
      }

      if (
        keyPreference &&
        typeof entry === "object" &&
        entry[keyPreference] != null
      ) {
        return Number(entry[keyPreference]);
      }

      if (typeof entry === "object") {
        if (entry.median_rating != null) {
          return Number(entry.median_rating);
        }

        if (keyPreference && entry[keyPreference] != null) {
          return Number(entry[keyPreference]);
        }

        const firstValue = Object.values(entry).find((value) => value != null);
        return firstValue != null ? Number(firstValue) : null;
      }

      return null;
    },
    getDefaultNodePollLabel(nodeType) {
      if (!nodeType) {
        return null;
      }
      return this.resolveNodePollLabel({ node_type: nodeType });
    },
    getDefaultEdgePollLabel(edgeType) {
      if (!edgeType) {
        return null;
      }
      return this.resolveEdgePollLabel({ edge_type: edgeType });
    },
    updateDepth(newDepth) {
      console.log("Updating depth to:", newDepth);
      this.depthLevel = newDepth;
      localStorage.setItem("graphDepthLevel", newDepth);
      // Re-fetch subgraph data with new depth
      this.performSearch();
    },
    updateColorBy(newColorBy) {
      console.log("Updating color by to:", newColorBy);
      this.colorBy = newColorBy;
      localStorage.setItem("graphColorBy", newColorBy);
      // No need to re-fetch - the computed properties (flowSubgraphData) will automatically update
      // This makes color changes instant and dynamic!
    },
    handleNodeItemHover(nodeId) {
      const numericId = Number(nodeId);
      this.hoveredNodeId = Number.isFinite(numericId) ? numericId : null;
    },
    handleNodeItemLeave(nodeId) {
      const numericId = Number(nodeId);
      if (this.hoveredNodeId === numericId) {
        this.hoveredNodeId = null;
      }
    },
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
      console.log("Node clicked in search:", nodeId);
      // Navigate to node focus view
      this.$router.push({ name: "NodeView", params: { id: nodeId } });
    },
    handleEdgeClick(edgeInfo) {
      const payload = this.normalizeEdgeEventPayload(edgeInfo);
      console.log("Edge clicked in search:", payload);
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
        "Search graph loaded with",
        data.nodes?.length,
        "nodes and",
        data.edges?.length,
        "edges",
      );
    },
    async fetchNodeRatings(nodeIds) {
      if (!nodeIds.length) return;
      try {
        console.log("Fetching node ratings for IDs:", nodeIds);
        const { data } = await api.get("/nodes/ratings/median", {
          params: { node_ids: nodeIds },
        });
        console.log("Raw node ratings:", data);
        this.ratings = data;
      } catch (err) {
        console.error("Error fetching node ratings:", err);
      }
    },
    async fetchEdgeRatings(edges) {
      if (!edges.length) return edges;
      const groupedByPoll = new Map();

      edges.forEach((edge) => {
        const pollLabel = this.resolveEdgePollLabel(edge);
        edge.ratingLabel = pollLabel;
        edge.causal_strength = null;

        if (!pollLabel) {
          return;
        }

        if (!groupedByPoll.has(pollLabel)) {
          groupedByPoll.set(pollLabel, []);
        }
        groupedByPoll.get(pollLabel).push(edge);
      });

      try {
        for (const [pollLabel, edgesForPoll] of groupedByPoll.entries()) {
          const edgeKeys = edgesForPoll.map((e) => `${e.source}-${e.target}`);
          const { data: edgeRatings } = await api.get("/edges/ratings/median", {
            params: { edge_ids: edgeKeys, poll_label: pollLabel },
          });

          edgesForPoll.forEach((edge) => {
            const key = `${edge.source}-${edge.target}`;
            const ratingEntry = edgeRatings[key] ?? null;
            const ratingValue = this.resolveRatingValue(
              ratingEntry,
              "median_rating",
            );
            edge.causal_strength = ratingValue;
          });
        }
      } catch (err) {
        console.error("Error fetching edge ratings:", err);
      }

      return edges;
    },
    updateNodesWithRatings(rawNodes) {
      console.log(
        "updateNodesWithRatings called with",
        rawNodes.length,
        "nodes",
      );
      console.log("Current ratings object:", this.ratings);
      return rawNodes.map((node) => {
        const nodeSpecificLabel =
          node.ratingLabel ||
          node.poll_label ||
          node.default_poll_label ||
          null;
        const pollLabel = nodeSpecificLabel || this.resolveNodePollLabel(node);
        const ratingEntry = this.ratings[node.node_id];
        const ratingValue = this.resolveRatingValue(ratingEntry, pollLabel);

        console.log(
          `Node ${node.node_id}: pollLabel=`,
          pollLabel,
          "ratingEntry=",
          ratingEntry,
          "resolved rating=",
          ratingValue,
        );

        let ratingLabel = pollLabel || nodeSpecificLabel || null;
        if (!ratingLabel && ratingEntry && typeof ratingEntry === "object") {
          const candidateKey = Object.keys(ratingEntry).find(
            (key) => key !== "median_rating" && ratingEntry[key] != null,
          );
          if (candidateKey) {
            ratingLabel = candidateKey;
          }
        }
        if (!ratingLabel && ratingValue != null) {
          ratingLabel = "rating";
        }

        if (ratingValue != null) {
          node.support = ratingValue;
        } else {
          delete node.support;
        }

        node.ratingLabel = ratingLabel || null;

        return node;
      });
    },
    resolveRatingValue(entry, keyPreference) {
      if (entry == null) {
        return null;
      }

      if (typeof entry === "number") {
        return Number(entry);
      }

      if (
        keyPreference &&
        typeof entry === "object" &&
        entry[keyPreference] != null
      ) {
        return Number(entry[keyPreference]);
      }

      if (typeof entry === "object") {
        if (entry.median_rating != null) {
          return Number(entry.median_rating);
        }

        if (keyPreference && entry[keyPreference] != null) {
          return Number(entry[keyPreference]);
        }

        const firstValue = Object.values(entry).find((value) => value != null);
        return firstValue != null ? Number(firstValue) : null;
      }

      return null;
    },
    getDefaultNodePollLabel(nodeType) {
      if (!nodeType) {
        return null;
      }
      return this.resolveNodePollLabel({ node_type: nodeType });
    },
    getDefaultEdgePollLabel(edgeType) {
      if (!edgeType) {
        return null;
      }
      return this.resolveEdgePollLabel({ edge_type: edgeType });
    },
    async performSearch() {
      const startTime = performance.now();
      const query = this.$route.query || {};
      const rawTitle = query.q ?? query.title ?? this.title;
      const title = Array.isArray(rawTitle)
        ? rawTitle.join(" ")
        : typeof rawTitle === "string"
          ? rawTitle
          : this.title;
      const node_type = query.node_type ?? undefined;
      const status = query.status ?? undefined;
      const scope = query.scope ?? undefined;
      const tagsParam = query.tags;
      const tagsArray = Array.isArray(tagsParam)
        ? tagsParam
        : typeof tagsParam === "string" && tagsParam.length
          ? tagsParam
              .split(",")
              .map((tag) => tag.trim())
              .filter(Boolean)
          : [];

      try {
        this.ratings = {};
        const baseParams = {
          title,
          node_type,
          status,
          scope,
          tags: tagsArray.length ? tagsArray : undefined,
        };

        const paramsSerializer = (params) =>
          qs.stringify(params, { arrayFormat: "repeat" });

        const [searchResponse, subgraphResponse] = await Promise.all([
          api.get(`/nodes`, {
            params: baseParams,
            paramsSerializer,
          }),
          api.get(`/nodes/subgraph`, {
            params: { ...baseParams, levels: this.depthLevel },
            paramsSerializer,
          }),
        ]);

        this.nodes = Array.isArray(searchResponse.data)
          ? searchResponse.data
          : [];

        let subgraphNodes = Array.isArray(subgraphResponse.data?.nodes)
          ? subgraphResponse.data.nodes
          : [];
        let relationships = Array.isArray(subgraphResponse.data?.edges)
          ? subgraphResponse.data.edges
          : [];

        const allNodeIds = [...this.nodes, ...subgraphNodes]
          .map((n) => n?.node_id)
          .filter((id) => id != null);

        if (allNodeIds.length) {
          await this.fetchNodeRatings(Array.from(new Set(allNodeIds)));
          this.nodes = this.updateNodesWithRatings(this.nodes);
          subgraphNodes = this.updateNodesWithRatings(subgraphNodes);
        } else {
          this.ratings = {};
        }

        relationships = await this.fetchEdgeRatings(relationships);

        this.subgraphNodes = subgraphNodes;
        this.relationships = relationships;

        const combinedNodes = [...this.nodes, ...this.subgraphNodes];
        const totalNodeCount = new Set(
          combinedNodes
            .map((node) => node?.node_id ?? node?.id)
            .filter((id) => id !== undefined && id !== null),
        ).size;
        const preferredTab = totalNodeCount < 50 ? "flow" : "graph";
        if (!this.userSelectedTab) {
          this.activeTab = preferredTab;
        }

        const endTime = performance.now();
        console.log(`Search completed in ${endTime - startTime} milliseconds`);
        console.log(
          `Found ${this.nodes.length} search results, ${this.subgraphNodes.length} total nodes in subgraph, ${this.relationships.length} edges`,
        );
      } catch (error) {
        console.error("Error fetching nodes:", error);
        this.nodes = [];
        this.relationships = [];
        this.subgraphNodes = [];
      }
    },
  },
  setup() {
    const router = useRouter();
    const route = useRoute();
    const {
      nodePollTypes,
      edgePollTypes,
      nodePollsByType,
      edgePollsByType,
      canCreate,
      defaultNodeType,
      getNodePolls,
      getEdgePolls,
    } = useConfig();
    const nodePolls = nodePollTypes.value;
    return {
      router,
      route,
      nodePolls,
      nodePollTypes,
      edgePollTypes,
      nodePollsByType,
      edgePollsByType,
      canCreate,
      defaultNodeType,
      getNodePolls,
      getEdgePolls,
    };
  },
};
</script>

<style scoped>
.search-page {
  display: flex;
  flex-direction: column;
  height: 92vh;
  width: 99.3vw;
}

.search-content {
  display: flex;
  flex: 1;
  overflow: hidden;
  gap: 4px; /* Space between columns, matching ElementFocus left-panel gap */
  padding: 0 1px 0 0; /* Small padding on right and bottom to show borders */
  box-sizing: border-box;
}

.results-column {
  width: 400px; /* Match ElementFocus left-panel width */
  padding: 10px 0 5px 0px;
  padding-right: 2px; /* Match ElementFocus left-panel padding-right */
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  overflow: hidden; /* Prevent overflow */
  flex-shrink: 0; /* Don't shrink the results column */
}

.results-column h2 {
  text-align: center;
  margin: 0px 50px;
  padding-bottom: 10px;
  padding-right: 50px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0; /* Prevent header from shrinking */
}

.results-list {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.visualization-column {
  flex: 1;
  padding: 0;
  box-sizing: border-box;
  overflow: hidden;
  min-width: 0; /* Allow flex item to shrink below content size */
  display: flex;
  flex-direction: column;
}

.graph-container {
  flex: 1;
  border-radius: 4px;
  padding-right: 2px; /* To match ElementFocus right-panel padding-right */
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0; /* Allow flex item to shrink */
  position: relative;
  box-sizing: border-box;
  /* No border here - it's on cosmos-container inside GraphVis */
}

.viz-header {
  position: absolute;
  top: 10px;
  left: 10px;
  right: 10px;
  display: flex;
  justify-content: flex-start; /* Align to left, not space-between */
  align-items: center;
  z-index: 10;
  gap: 16px;
  pointer-events: none; /* Allow clicks to pass through empty space */
}

.viz-header.has-compass {
  right: 80px; /* Add space for compass/layout controls on the right when in flow mode */
}

.viz-tabs,
.viz-controls {
  pointer-events: auto; /* Re-enable clicks on the actual controls */
}

.viz-tabs {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.viz-controls {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 5px 7px;
  background-color: var(--background-color);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.tab-button {
  padding: 6px 8px;
  background-color: var(--background-color);
  color: var(--text-color);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  min-width: 32px;
  min-height: 32px;
}

.tab-button svg {
  width: 16px;
  height: 16px;
  display: block;
}

.tab-button:hover:not(.disabled) {
  background-color: var(--border-color);
  border-color: var(--text-color);
  transform: translateY(-1px);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.15);
}

.tab-button:active:not(.disabled) {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.tab-button.active {
  font-weight: 600;
  border-color: var(--text-color);
  background-color: var(--border-color);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.tab-button.disabled {
  opacity: 0.3;
  cursor: not-allowed;
  color: var(--muted-text-color);
}

.tab-button.disabled:hover {
  transform: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

:global(body.dark) .tab-button {
  background-color: #333;
  color: #fff;
  border-color: #555;
}

:global(body.dark) .tab-button:hover:not(.disabled) {
  background-color: #444;
  border-color: #777;
}

:global(body.dark) .tab-button.active {
  background-color: #444;
  border-color: #888;
}

:global(body.dark) .viz-controls {
  background-color: #333;
  border-color: #555;
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
