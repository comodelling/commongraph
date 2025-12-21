<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md

SPDX-License-Identifier: AGPL-3.0-or-later
-->
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
            <div class="viz-left">
              <div class="viz-tabs">
                <button
                  :class="['tab-button', { active: activeTab === 'flow' }]"
                  @click="selectTab('flow')"
                  title="Flow View"
                >
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 20 20"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <!-- Left node -->
                    <rect
                      x="1"
                      y="5.5"
                      width="6"
                      height="9"
                      rx="1.2"
                      stroke="currentColor"
                      stroke-width="1.4"
                      fill="none"
                    />
                    <!-- Right node -->
                    <rect
                      x="13"
                      y="5.5"
                      width="6"
                      height="9"
                      rx="1.2"
                      stroke="currentColor"
                      stroke-width="1.4"
                      fill="none"
                    />
                    <!-- Edge arrow -->
                    <path
                      d="M7.5 10 L12.5 10"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                    />
                    <!-- Arrowhead (filled triangle) -->
                    <path d="M11.5 8 L14 10 L11.5 12 Z" fill="currentColor" />
                  </svg>
                </button>
                <button
                  :class="['tab-button', { active: activeTab === 'graph' }]"
                  @click="selectTab('graph')"
                  title="Graph View"
                >
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 20 20"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <!-- Center node (larger) -->
                    <circle cx="10" cy="10" r="1.5" fill="currentColor" />

                    <!-- Outer nodes positioned in pentagon -->
                    <circle cx="10" cy="3" r="1.8" fill="currentColor" />
                    <circle cx="16.5" cy="7.5" r="1.8" fill="currentColor" />
                    <circle cx="13.5" cy="15" r="1.8" fill="currentColor" />
                    <circle cx="6.5" cy="15" r="1.8" fill="currentColor" />
                    <circle cx="3.5" cy="7.5" r="1.8" fill="currentColor" />

                    <!-- Edges from center to outer nodes -->
                    <line
                      x1="10"
                      y1="10"
                      x2="10"
                      y2="4.8"
                      stroke="currentColor"
                      stroke-width="1.2"
                      opacity="0.7"
                    />
                    <line
                      x1="10"
                      y1="10"
                      x2="14.8"
                      y2="7.8"
                      stroke="currentColor"
                      stroke-width="1.2"
                      opacity="0.7"
                    />
                    <line
                      x1="10"
                      y1="10"
                      x2="12.8"
                      y2="13.5"
                      stroke="currentColor"
                      stroke-width="1.2"
                      opacity="0.7"
                    />
                    <line
                      x1="10"
                      y1="10"
                      x2="7.2"
                      y2="13.5"
                      stroke="currentColor"
                      stroke-width="1.2"
                      opacity="0.7"
                    />
                    <line
                      x1="10"
                      y1="10"
                      x2="5.2"
                      y2="7.8"
                      stroke="currentColor"
                      stroke-width="1.2"
                      opacity="0.7"
                    />

                    <!-- Outer ring connections -->
                    <path
                      d="M10 3 L16.5 7.5 L13.5 15 L6.5 15 L3.5 7.5 Z"
                      stroke="currentColor"
                      stroke-width="1"
                      fill="none"
                      opacity="0.4"
                    />
                  </svg>
                </button>
                <button
                  class="tab-button disabled"
                  disabled
                  title="Map View (Coming Soon)"
                >
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 20 20"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <!-- Map background -->
                    <path
                      d="M2 14 L6.5 12 L13.5 14.5 L18 12.5 V4.5 L13.5 6.5 L6.5 4 L2 6 Z"
                      fill="currentColor"
                      opacity="0.25"
                    />
                    <!-- Fold lines -->
                    <path
                      d="M6.5 4 V12 M13.5 6.5 V14.5"
                      stroke="currentColor"
                      stroke-width="1.8"
                      stroke-linecap="round"
                    />
                    <!-- Top edge -->
                    <path
                      d="M2 6 L6.5 4 L13.5 6.5 L18 4.5"
                      stroke="currentColor"
                      stroke-width="1.6"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      fill="none"
                    />
                  </svg>
                </button>
              </div>
            </div>
            <div class="viz-controls">
              <GraphControls
                :depth="depthLevel"
                :node-color-by="nodeColorBy"
                :edge-color-by="edgeColorBy"
                :show-info-button="true"
                :info-mode="infoMode"
                @update:depth="updateDepth"
                @update:nodeColorBy="updateNodeColorBy"
                @update:edgeColorBy="updateEdgeColorBy"
                @update:infoMode="toggleInfoMode"
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
            :info-control-visible="false"
            :node-color-by="nodeColorBy"
            :edge-color-by="edgeColorBy"
            :read-only="!(canCreate || canEdit || canDelete)"
            :highlighted-node-id="hoveredNodeId"
            :fit-trigger="flowFitTick"
            @nodeClick="handleNodeClick"
            @edgeClick="handleEdgeClick"
            @newNodeCreated="handleNewNodeCreated"
            @newEdgeCreated="handleNewEdgeCreated"
            @editExistingEdge="handleEditExistingEdge"
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
import Icon from "../components/common/Icon.vue";
import { useLogging } from "../composables/useLogging";
import {
  COLOR_MODE_TYPE,
  EDGE_COLOR_STORAGE_KEY,
  LEGACY_COLOR_STORAGE_KEY,
  NODE_COLOR_STORAGE_KEY,
} from "../utils/graphColoring";

const FOCUS_GRAPH_CACHE_KEY = "focusFlowGraphSnapshot";

export default {
  components: {
    RatingHistogram,
    NodeListItem,
    AggRatingMultipane,
    CosmosGraphVis,
    FlowEditor,
    GraphControls,
    Icon,
  },
  data() {
    // Logging system
    const { debugLog, infoLog, warnLog, errorLog, DEBUG } =
      useLogging("SearchPage");

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
      nodeColorBy:
        localStorage.getItem(NODE_COLOR_STORAGE_KEY) ||
        localStorage.getItem(LEGACY_COLOR_STORAGE_KEY) ||
        COLOR_MODE_TYPE,
      edgeColorBy:
        localStorage.getItem(EDGE_COLOR_STORAGE_KEY) ||
        localStorage.getItem(LEGACY_COLOR_STORAGE_KEY) ||
        COLOR_MODE_TYPE,
      ratings: {}, // Store node ratings fetched from API
      pendingFocusGraph: null,
      pendingFocusEdge: null,
      DEBUG,
      infoMode: localStorage.getItem("commongraph:flow:infoMode") === "true",
      debugLog,
      infoLog,
      warnLog,
      errorLog,
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

      this.debugLog("subgraphData:", {
        nodes: result.nodes.length,
        edges: result.edges.length,
      });
      this.debugLog("Search results and subgraph nodes:", {
        searchResults: this.nodes.length,
        subgraphNodes: this.subgraphNodes.length,
      });
      if (result.nodes.length > 0) {
        this.debugLog("Sample node:", JSON.stringify(result.nodes[0]));
        this.debugLog(
          "All node IDs:",
          result.nodes.map((n) => n.node_id),
        );
      }
      if (result.edges.length > 0) {
        this.debugLog("Sample edge:", JSON.stringify(result.edges[0]));
        this.debugLog(
          "All edge sources:",
          result.edges.map((e) => e.source),
        );
        this.debugLog(
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

      this.debugLog("flowSubgraphData computed - colors:", {
        node: this.nodeColorBy,
        edge: this.edgeColorBy,
      });

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

          const formatted = formatFlowNodeProps(enrichedNode, this.nodeColorBy);
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
            this.edgeColorBy,
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

      this.debugLog("flowSubgraphData - formatted nodes with colors", {
        formattedNodes: formattedNodes.length,
        nodeColorBy: this.nodeColorBy,
        edgeColorBy: this.edgeColorBy,
      });
      if (formattedNodes.length > 0) {
        this.debugLog("Sample node style:", formattedNodes[0].style);
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
        this.debugLog("New query:", newQuery);
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
    nodeStatusAllowed(node) {
      if (!node || !this.nodeAllowsProperty) {
        return false;
      }
      return this.nodeAllowsProperty(node.node_type, "status");
    },
    sanitizeNode(node) {
      if (!node) {
        return node;
      }
      if (
        !this.nodeStatusAllowed(node) &&
        Object.prototype.hasOwnProperty.call(node, "status")
      ) {
        delete node.status;
      }
      return node;
    },
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
        this.debugLog("Fetching node ratings for IDs:", nodeIds);
        const { data } = await api.get("/nodes/ratings/median", {
          params: { node_ids: nodeIds },
        });
        this.debugLog("Raw node ratings:", data);
        this.ratings = data;
      } catch (err) {
        this.errorLog("Error fetching node ratings:", err);
      }
    },
    async fetchEdgeRatings(edges) {
      if (!edges.length) return edges;

      const pollConfig = this.edgePollTypes || {};
      const pollLabels = Object.keys(pollConfig || {});
      const edgeKeys = Array.from(
        new Set(
          edges
            .map((edge) => {
              const source = edge.source ?? edge.source_id;
              const target = edge.target ?? edge.target_id;
              if (source == null || target == null) {
                return null;
              }
              return `${source}-${target}`;
            })
            .filter(Boolean),
        ),
      );

      if (!edgeKeys.length) {
        return edges;
      }

      if (!pollLabels.length) {
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
            const keysForPoll = edgesForPoll.map(
              (e) => `${e.source}-${e.target}`,
            );
            const { data: edgeRatings } = await api.get(
              "/edges/ratings/median",
              {
                params: { edge_ids: keysForPoll, poll_label: pollLabel },
              },
            );

            edgesForPoll.forEach((edge) => {
              const key = `${edge.source}-${edge.target}`;
              const ratingEntry = edgeRatings[key] ?? null;
              const ratingValue = this.resolveRatingValue(
                ratingEntry,
                "median_rating",
              );
              edge.pollRatings = {
                ...(edge.pollRatings || {}),
                ...(ratingValue != null ? { [pollLabel]: ratingValue } : {}),
              };
              edge.causal_strength = ratingValue;
            });
          }
        } catch (err) {
          this.errorLog("Error fetching edge ratings:", err);
        }

        return edges;
      }

      const pollResults = {};
      try {
        for (const pollLabel of pollLabels) {
          const { data } = await api.get("/edges/ratings/median", {
            params: { edge_ids: edgeKeys, poll_label: pollLabel },
          });
          pollResults[pollLabel] = data;
        }
      } catch (err) {
        this.errorLog("Error fetching edge ratings:", err);
        return edges;
      }

      edges.forEach((edge) => {
        const key = `${edge.source}-${edge.target}`;
        const ratingMap = {};
        pollLabels.forEach((pollLabel) => {
          const ratingEntry = pollResults[pollLabel]?.[key] ?? null;
          const ratingValue = this.resolveRatingValue(
            ratingEntry,
            "median_rating",
          );
          if (ratingValue != null) {
            ratingMap[pollLabel] = ratingValue;
          }
        });

        edge.pollRatings = ratingMap;
        const defaultLabel =
          edge.ratingLabel ||
          edge.poll_label ||
          edge.default_poll_label ||
          this.resolveEdgePollLabel(edge);
        edge.ratingLabel = defaultLabel || null;
        edge.causal_strength =
          defaultLabel && ratingMap[defaultLabel] != null
            ? ratingMap[defaultLabel]
            : null;
      });

      return edges;
    },
    updateNodesWithRatings(rawNodes) {
      this.debugLog(
        "updateNodesWithRatings called with",
        rawNodes.length,
        "nodes",
      );
      this.debugLog("Current ratings object:", this.ratings);
      return rawNodes.map((node) => {
        const nodeSpecificLabel =
          node.ratingLabel ||
          node.poll_label ||
          node.default_poll_label ||
          null;
        const pollLabel = nodeSpecificLabel || this.resolveNodePollLabel(node);
        const ratingEntry = this.ratings[node.node_id];
        const ratingValue = this.resolveRatingValue(ratingEntry, pollLabel);
        const normalizedRatings =
          ratingEntry && typeof ratingEntry === "object"
            ? { ...ratingEntry }
            : pollLabel && ratingEntry != null
              ? { [pollLabel]: Number(ratingEntry) }
              : {};

        this.debugLog(
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
        node.pollRatings = normalizedRatings;

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
      this.debugLog("Updating depth to:", newDepth);
      this.depthLevel = newDepth;
      localStorage.setItem("graphDepthLevel", newDepth);
      // Re-fetch subgraph data with new depth
      this.performSearch();
    },
    updateNodeColorBy(newNodeColorBy) {
      this.debugLog("Updating node color by to:", newNodeColorBy);
      this.nodeColorBy = newNodeColorBy;
      localStorage.setItem(NODE_COLOR_STORAGE_KEY, newNodeColorBy);
    },
    updateEdgeColorBy(newEdgeColorBy) {
      this.debugLog("Updating edge color by to:", newEdgeColorBy);
      this.edgeColorBy = newEdgeColorBy;
      localStorage.setItem(EDGE_COLOR_STORAGE_KEY, newEdgeColorBy);
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
    ensurePendingFocusGraph() {
      if (!this.pendingFocusGraph) {
        const baseNodesSource = this.subgraphNodes.length
          ? this.subgraphNodes
          : this.nodes;
        const rawNodes = baseNodesSource.map((node) =>
          JSON.parse(JSON.stringify(node)),
        );
        const rawEdges = (this.relationships || []).map((edge) => {
          const source =
            edge.source ?? edge.source_id ?? edge.data?.source ?? null;
          const target =
            edge.target ?? edge.target_id ?? edge.data?.target ?? null;
          return JSON.parse(
            JSON.stringify({
              ...edge,
              source,
              target,
            }),
          );
        });
        this.pendingFocusGraph = { nodes: rawNodes, edges: rawEdges };
      }
      return this.pendingFocusGraph;
    },
    toRawNode(flowNode) {
      if (!flowNode) return null;
      const raw = flowNode.data
        ? JSON.parse(JSON.stringify(flowNode.data))
        : JSON.parse(JSON.stringify(flowNode));
      if (flowNode.position && !raw.position) {
        raw.position = JSON.parse(JSON.stringify(flowNode.position));
      }
      const nodeId =
        flowNode.id ?? raw.node_id ?? raw.id ?? flowNode.data?.node_id;
      if (nodeId != null) {
        const numeric = Number(nodeId);
        raw.node_id = Number.isNaN(numeric) ? nodeId : numeric;
      }
      return raw;
    },
    toRawEdge(flowEdge) {
      if (!flowEdge) return null;
      const raw = flowEdge.data
        ? JSON.parse(JSON.stringify(flowEdge.data))
        : JSON.parse(JSON.stringify(flowEdge));
      const source =
        flowEdge.data?.source ?? flowEdge.source ?? raw.source ?? raw.source_id;
      const target =
        flowEdge.data?.target ?? flowEdge.target ?? raw.target ?? raw.target_id;
      if (source != null) {
        const numericSource = Number(source);
        raw.source = Number.isNaN(numericSource) ? source : numericSource;
      }
      if (target != null) {
        const numericTarget = Number(target);
        raw.target = Number.isNaN(numericTarget) ? target : numericTarget;
      }
      return raw;
    },
    upsertNodeInGraph(graph, flowNode) {
      if (!graph || !flowNode) return;
      const rawNode = this.toRawNode(flowNode);
      if (!rawNode || rawNode.node_id == null) return;
      const existingIndex = graph.nodes.findIndex(
        (existing) => existing?.node_id === rawNode.node_id,
      );
      if (existingIndex >= 0) {
        graph.nodes.splice(existingIndex, 1, rawNode);
      } else {
        graph.nodes.push(rawNode);
      }
    },
    upsertEdgeInGraph(graph, flowEdge) {
      if (!graph || !flowEdge) return;
      const rawEdge = this.toRawEdge(flowEdge);
      if (!rawEdge || rawEdge.source == null || rawEdge.target == null) return;
      const edgeId = `${rawEdge.source}-${rawEdge.target}`;
      const existingIndex = graph.edges.findIndex((existing) => {
        if (!existing) return false;
        const existingId = `${existing.source}-${existing.target}`;
        return existingId === edgeId;
      });
      if (existingIndex >= 0) {
        graph.edges.splice(existingIndex, 1, rawEdge);
      } else {
        graph.edges.push(rawEdge);
      }
    },
    storeFocusGraphSnapshot(graph, focusNodeData, focusEdgeData = null) {
      try {
        const payload = {
          nodes: graph.nodes.map((node) => JSON.parse(JSON.stringify(node))),
          edges: graph.edges.map((edge) => JSON.parse(JSON.stringify(edge))),
          focusNode: focusNodeData
            ? JSON.parse(JSON.stringify(focusNodeData))
            : null,
          focusEdge: focusEdgeData
            ? JSON.parse(JSON.stringify(focusEdgeData))
            : null,
        };
        sessionStorage.setItem(FOCUS_GRAPH_CACHE_KEY, JSON.stringify(payload));
      } catch (error) {
        this.warnLog("Failed to cache focus graph snapshot", error);
      }
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
      this.debugLog("Node clicked in search:", nodeId);
      // Navigate to node focus view
      this.$router.push({ name: "NodeView", params: { id: nodeId } });
    },
    handleEdgeClick(edgeInfo) {
      const payload = this.normalizeEdgeEventPayload(edgeInfo);
      this.debugLog("Edge clicked in search:", payload);
      if (!payload?.sourceId || !payload?.targetId) {
        this.warnLog("Unable to navigate without edge endpoints", payload);
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
      this.debugLog(
        "Search graph loaded with",
        data.nodes?.length,
        "nodes and",
        data.edges?.length,
        "edges",
      );
    },
    getCurrentInfoMode() {
      return this.infoMode;
    },
    toggleInfoMode() {
      const current = this.infoMode;
      const next = !current;
      try {
        localStorage.setItem(
          "commongraph:flow:infoMode",
          next ? "true" : "false",
        );
      } catch (err) {
        // ignore localStorage errors
      }
      window.dispatchEvent(
        new CustomEvent("commongraph-infoMode-set", { detail: next }),
      );
      this.infoMode = next;
    },
    handleNewNodeCreated(newNodeData) {
      // newNodeData is the formatted node object created in FlowEditor
      this.debugLog("New node created in flow view:", newNodeData);
      const graph = this.ensurePendingFocusGraph();
      this.upsertNodeInGraph(graph, newNodeData);

      const focusNodePayload = newNodeData?.data
        ? JSON.parse(JSON.stringify(newNodeData.data))
        : null;

      this.storeFocusGraphSnapshot(
        graph,
        focusNodePayload,
        this.pendingFocusEdge,
      );

      // reset cached graph so future operations start fresh
      this.pendingFocusGraph = null;
      this.pendingFocusEdge = null;

      // Navigate to node edit view for the newly created node
      const targetId = newNodeData?.id ?? newNodeData?.data?.node_id ?? "new";
      this.$router.push({ name: "NodeEdit", params: { id: targetId } });
    },
    handleNewEdgeCreated(newEdgeData) {
      this.debugLog("New edge created in flow view:", newEdgeData);
      const graph = this.ensurePendingFocusGraph();
      this.upsertEdgeInGraph(graph, newEdgeData);
      const rawEdge = this.toRawEdge(newEdgeData);
      this.pendingFocusEdge = rawEdge;

      const src = rawEdge?.source;
      const tgt = rawEdge?.target;
      const involvesNewNode = src === "new" || tgt === "new";

      if (!involvesNewNode && src != null && tgt != null) {
        this.storeFocusGraphSnapshot(graph, null, rawEdge);
        this.pendingFocusGraph = null;
        this.pendingFocusEdge = null;
        this.$router.push({
          name: "EdgeEdit",
          params: { source_id: src, target_id: tgt },
        });
        return;
      }

      if (src == null || tgt == null) {
        this.warnLog("New edge missing endpoints, cannot open edge editor");
      }
    },
    handleEditExistingEdge(edgeInfo) {
      this.debugLog("Editing existing edge:", edgeInfo);
      const { edge, source, target } = edgeInfo;
      const rawEdge = {
        source,
        target,
        ...edge,
      };
      this.pendingFocusEdge = rawEdge;
      this.storeFocusGraphSnapshot(
        this.ensurePendingFocusGraph(),
        null,
        rawEdge,
      );
      this.pendingFocusGraph = null;
      this.pendingFocusEdge = null;
      this.$router.push({
        name: "EdgeEdit",
        params: { source_id: source, target_id: target },
      });
    },
    async fetchNodeRatings(nodeIds) {
      if (!nodeIds.length) return;
      try {
        this.debugLog("Fetching node ratings for IDs:", nodeIds);
        const { data } = await api.get("/nodes/ratings/median", {
          params: { node_ids: nodeIds },
        });
        this.debugLog("Raw node ratings:", data);
        this.ratings = data;
      } catch (err) {
        this.errorLog("Error fetching node ratings:", err);
      }
    },
    async fetchEdgeRatings(edges) {
      if (!edges.length) return edges;

      const pollConfig = this.edgePollTypes || {};
      const pollLabels = Object.keys(pollConfig || {});
      const edgeKeys = Array.from(
        new Set(
          edges
            .map((edge) => {
              const source = edge.source ?? edge.source_id;
              const target = edge.target ?? edge.target_id;
              if (source == null || target == null) {
                return null;
              }
              return `${source}-${target}`;
            })
            .filter(Boolean),
        ),
      );

      if (!edgeKeys.length) {
        return edges;
      }

      if (!pollLabels.length) {
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
            const keysForPoll = edgesForPoll.map(
              (e) => `${e.source}-${e.target}`,
            );
            const { data: edgeRatings } = await api.get(
              "/edges/ratings/median",
              {
                params: { edge_ids: keysForPoll, poll_label: pollLabel },
              },
            );

            edgesForPoll.forEach((edge) => {
              const key = `${edge.source}-${edge.target}`;
              const ratingEntry = edgeRatings[key] ?? null;
              const ratingValue = this.resolveRatingValue(
                ratingEntry,
                "median_rating",
              );
              edge.pollRatings = {
                ...(edge.pollRatings || {}),
                ...(ratingValue != null ? { [pollLabel]: ratingValue } : {}),
              };
              edge.causal_strength = ratingValue;
            });
          }
        } catch (err) {
          this.errorLog("Error fetching edge ratings:", err);
        }

        return edges;
      }

      const pollResults = {};
      try {
        for (const pollLabel of pollLabels) {
          const { data } = await api.get("/edges/ratings/median", {
            params: { edge_ids: edgeKeys, poll_label: pollLabel },
          });
          pollResults[pollLabel] = data;
        }
      } catch (err) {
        this.errorLog("Error fetching edge ratings:", err);
        return edges;
      }

      edges.forEach((edge) => {
        const key = `${edge.source}-${edge.target}`;
        const ratingMap = {};
        pollLabels.forEach((pollLabel) => {
          const ratingEntry = pollResults[pollLabel]?.[key] ?? null;
          const ratingValue = this.resolveRatingValue(
            ratingEntry,
            "median_rating",
          );
          if (ratingValue != null) {
            ratingMap[pollLabel] = ratingValue;
          }
        });

        edge.pollRatings = ratingMap;
        const defaultLabel =
          edge.ratingLabel ||
          edge.poll_label ||
          edge.default_poll_label ||
          this.resolveEdgePollLabel(edge);
        edge.ratingLabel = defaultLabel || null;
        edge.causal_strength =
          defaultLabel && ratingMap[defaultLabel] != null
            ? ratingMap[defaultLabel]
            : null;
      });

      return edges;
    },
    updateNodesWithRatings(rawNodes) {
      this.debugLog(
        "updateNodesWithRatings called with",
        rawNodes.length,
        "nodes",
      );
      this.debugLog("Current ratings object:", this.ratings);
      return rawNodes.map((node) => {
        const nodeSpecificLabel =
          node.ratingLabel ||
          node.poll_label ||
          node.default_poll_label ||
          null;
        const pollLabel = nodeSpecificLabel || this.resolveNodePollLabel(node);
        const ratingEntry = this.ratings[node.node_id];
        const ratingValue = this.resolveRatingValue(ratingEntry, pollLabel);

        this.debugLog(
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
          this.nodes = this.updateNodesWithRatings(this.nodes).map((node) =>
            this.sanitizeNode(node),
          );
          subgraphNodes = this.updateNodesWithRatings(subgraphNodes).map(
            (node) => this.sanitizeNode(node),
          );
        } else {
          this.ratings = {};
        }

        this.nodes = this.nodes.map((node) => this.sanitizeNode(node));
        subgraphNodes = subgraphNodes.map((node) => this.sanitizeNode(node));

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
      canEdit,
      canDelete,
      defaultNodeType,
      getNodePolls,
      getEdgePolls,
      nodeAllowsProperty,
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
      canEdit,
      canDelete,
      defaultNodeType,
      getNodePolls,
      getEdgePolls,
      nodeAllowsProperty,
    };
  },
  mounted() {
    // Keep the info icon state in sync with localStorage, and subscribe to external toggle events
    this._infoModeHandler = (e) => {
      if (typeof e?.detail === "boolean") {
        this.infoMode = e.detail;
      }
    };
    window.addEventListener("commongraph-infoMode-set", this._infoModeHandler);
  },
  beforeUnmount() {
    window.removeEventListener(
      "commongraph-infoMode-set",
      this._infoModeHandler,
    );
  },
};
</script>

<style scoped>
.search-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

.search-content {
  display: flex;
  flex: 1;
  overflow: hidden;
  gap: 4px; /* Space between columns, matching ElementFocus left-panel gap */
  padding: 0;
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
  min-height: 0; /* Allow flex items inside to shrink */
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
  padding-right: 9px;
  box-sizing: border-box;
  overflow: hidden;
  min-width: 0; /* Allow flex item to shrink below content size */
  min-height: 0; /* Allow flex item to shrink below content size */
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
  min-width: 0; /* Allow flex item to shrink below content size */
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
  justify-content: center; /* Center the controls */
  align-items: flex-start;
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

.viz-left {
  position: absolute;
  left: 0;
  top: 0;
  display: flex;
  flex-direction: column;
  pointer-events: auto; /* ensure buttons inside are clickable even though parent header may have pointer-events: none */
}

.viz-controls {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 4px 8px;
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
  width: 20px;
  height: 20px;
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
