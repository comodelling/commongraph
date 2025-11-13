<template>
  <div class="focus">
    <div class="left-panel">
      <!-- Top card: show node info or edge info -->
      <div class="card">
        <template v-if="isNode">
          <NodeInfo
            v-if="node"
            :node="node"
            @update-node-from-editor="updateNodeFromEditor"
          />
          <div v-else class="error-message">Node not found</div>
        </template>
        <template v-else-if="isEdge">
          <EdgeInfo
            v-if="edge"
            :edge="edge"
            @update-edge-from-editor="updateEdgeFromEditor"
          />
          <div v-else class="error-message">Edge not found</div>
        </template>
      </div>

      <!-- Second card: show rating for node or edge -->

      <template v-if="isNode && nodePollsCount && !node.new">
        <div
          class="card"
          v-for="(pollConfig, pollLabel) in nodePolls"
          :key="`node-${pollLabel}-${node.node_id}`"
        >
          <ElementPollPane
            :element="{ node_id: node.node_id }"
            :poll-label="pollLabel"
            :poll-config="pollConfig"
          />
        </div>
      </template>

      <template v-else-if="isEdge && edgePollsCount && !edge.new">
        <div
          class="card"
          v-for="(pollConfig, pollLabel) in edgePolls"
          :key="`edge-${pollLabel}-${edge.source}-${edge.target}`"
        >
          <ElementPollPane
            :element="{ edge: { source: edge.source, target: edge.target } }"
            :poll-label="pollLabel"
            :poll-config="pollConfig"
          />
        </div>
      </template>
    </div>

    <div class="right-panel">
      <div class="right-panel-header">
        <GraphControls
          :depth="depthLevel"
          :color-by="colorBy"
          @update:depth="updateDepth"
          @update:colorBy="updateColorBy"
        />
      </div>
      <SubgraphRenderer
        :data="subgraphData"
        @nodeClick="updateNodeFromBackend"
        @edgeClick="updateEdgeFromBackend"
        @newNodeCreated="openNewlyCreatedNode"
        @newEdgeCreated="openNewlyCreatedEdge"
        :updatedNode="updatedNode"
        :updatedEdge="updatedEdge"
      />
    </div>
  </div>
</template>

<script>
import { useConfig } from "../composables/useConfig";
import NodeInfo from "../components/node/NodeInfo.vue";
import EdgeInfo from "../components/edge/EdgeInfo.vue";
import ElementPollPane from "../components/poll/ElementPollPane.vue";
import SubgraphRenderer from "../components/graph/FlowEditor.vue";
import GraphControls from "../components/graph/GraphControls.vue";
import {
  formatFlowEdgeProps,
  formatFlowNodeProps,
} from "../composables/formatFlowComponents";
import api from "../api/axios";
import { hydrate } from "vue";

const FOCUS_GRAPH_CACHE_KEY = "focusFlowGraphSnapshot";

export default {
  components: {
    NodeInfo,
    EdgeInfo,
    ElementPollPane,
    SubgraphRenderer,
    GraphControls,
  },
  setup() {
    const {
      nodeTypes,
      edgeTypes,
      nodePollTypes,
      edgePollTypes,
      nodePollsByType,
      edgePollsByType,
      defaultNodeType,
      canCreate,
      canEdit,
      getNodePolls,
      getEdgePolls,
    } = useConfig();

    // nodeTypes & edgeTypes will be unwrapped when used in `this.*`
    return {
      nodeTypes,
      edgeTypes,
      nodePollTypes,
      edgePollTypes,
      nodePollsByType,
      edgePollsByType,
      defaultNodeType,
      canCreate,
      canEdit,
      getNodePolls,
      getEdgePolls,
    };
  },

  data() {
    return {
      node: undefined,
      edge: undefined,
      updatedNode: undefined,
      updatedEdge: undefined,
      subgraphData: {},
      ratings: {},
      causalDirection: "LeftToRight",
      depthLevel: parseInt(localStorage.getItem("graphDepthLevel")) || 2, // Default depth for ElementFocus
      colorBy: localStorage.getItem("graphColorBy") || "type", // Color nodes/edges by 'type' or 'rating'
    };
  },
  watch: {
    "$route.params.id"() {
      if (this.id) {
        this.hydrateNodeFromCache();
      }
    },
    "$route.params.source_id"() {
      console.log("Source ID changed to:", this.sourceId);
      if (this.sourceId) {
        this.hydrateEdgeFromCache();
      }
    },
    "$route.params.target_id"() {
      if (this.targetId) {
        this.hydrateEdgeFromCache();
      }
    },
  },
  computed: {
    nodeId() {
      return this.$route.params.id === "new"
        ? "new"
        : Number(this.$route.params.id);
    },
    sourceId() {
      return this.$route.params.source_id;
    },
    targetId() {
      return this.$route.params.target_id;
    },
    isEditMode() {
      return this.$route.path.endsWith("/edit");
    },
    isBrandNewNode() {
      return this.nodeId === "new";
    },
    isNode() {
      return Boolean(this.nodeId);
    },
    isEdge() {
      return Boolean(this.sourceId && this.targetId);
    },
    allowedNodeFields() {
      if (!this.node?.node_type) return [];
      console.log("node Types allowed", this.nodeTypes);
      return this.nodeTypes[this.node.node_type].properties || [];
    },
    allowedEdgeFields() {
      if (!this.edge?.edge_type) return [];
      return this.edgeTypes[this.edge.edge_type].properties || [];
    },
    nodePolls() {
      if (!this.node?.node_type) return {};
      return this.nodeTypes[this.node.node_type].polls || {};
    },
    nodePollsCount() {
      return Object.keys(this.nodePolls).length;
    },
    edgePolls() {
      if (!this.edge?.edge_type) return {};
      return this.edgeTypes[this.edge.edge_type].polls || {};
    },
    edgePollsCount() {
      return Object.keys(this.edgePolls).length;
    },
  },
  // when opening a brand-new node, use defaultNodeType and only include allowed props
  async created() {
    let cachedSnapshot = null;
    if (this.isBrandNewNode || this.isEdge) {
      cachedSnapshot = this.consumeFocusGraphSnapshot();
    } else {
      this.clearFocusGraphSnapshot();
    }

    if (this.isBrandNewNode) {
      // Check permissions first
      if (!this.canCreate) {
        alert(
          "You don't have permission to create nodes. Please log in with an account that has create permissions.",
        );
        this.$router.push({ name: "Home" });
        return;
      }

      console.log("Opening brand new node in focus");
      let type = cachedSnapshot?.focusNode?.node_type || this.defaultNodeType;
      if (!this.nodeTypes[type]) {
        console.warn(
          "Unknown node type from snapshot, falling back to default",
          type,
        );
        type = this.defaultNodeType;
      }
      console.log("Default node type:", type);
      // const allowed = this.allowedNodeFields.value || [];
      const allowed = this.nodeTypes[type]?.properties || [];
      console.log("Allowed node props:", allowed);

      // Check if there's a pre-populated title from search
      const prePopulatedTitle = sessionStorage.getItem("newNodeTitle");
      if (prePopulatedTitle) {
        sessionStorage.removeItem("newNodeTitle"); // Clear after reading
      }

      // build minimal node object (prefer snapshot data when available)
      const nodeFromSnapshot = cachedSnapshot?.focusNode
        ? { ...cachedSnapshot.focusNode }
        : null;

      const node = nodeFromSnapshot || { node_id: "new", node_type: type };
      node.node_id = node.node_id ?? "new";
      node.node_type = node.node_type || type;
      node.new = true;

      if (allowed.includes("title")) {
        if (node.title == null || node.title === "") {
          node.title = prePopulatedTitle || "";
        }
      } else {
        delete node.title;
      }
      if (allowed.includes("scope")) {
        if (node.scope == null) node.scope = "";
      } else {
        delete node.scope;
      }
      if (allowed.includes("status")) {
        node.status = node.status || "draft";
      } else {
        delete node.status;
      }
      if (allowed.includes("tags")) {
        if (!Array.isArray(node.tags)) node.tags = [];
      } else {
        delete node.tags;
      }
      if (allowed.includes("references")) {
        if (!Array.isArray(node.references)) node.references = [];
      } else {
        delete node.references;
      }
      if (allowed.includes("description")) {
        if (node.description == null) node.description = "";
      } else {
        delete node.description;
      }

      this.node = node;
      this.$router.push({ name: "NodeEdit", params: { id: "new" } });
      const snapshotHasGraph = Boolean(
        cachedSnapshot?.nodes?.length || cachedSnapshot?.edges?.length,
      );

      if (snapshotHasGraph) {
        const flowGraph = this.buildFlowGraphFromRaw(
          cachedSnapshot.nodes,
          cachedSnapshot.edges,
        );
        const targetId = this.node?.node_id?.toString();
        if (targetId) {
          flowGraph.nodes = flowGraph.nodes.map((n) => {
            if (n.id === targetId) {
              return {
                ...n,
                selected: true,
                data: { ...n.data, selected: true },
                label: n.label || this.node.title || "New Node",
              };
            }
            return n;
          });
        }
        this.subgraphData = flowGraph;
      } else {
        let formattedNode = formatFlowNodeProps(this.node, this.colorBy);
        formattedNode.label = formattedNode.label || "New Node";
        // small delay so VueFlow has time to mount
        setTimeout(() => {
          this.subgraphData = { nodes: [formattedNode], edges: [] };
        }, 45);
      }
    } else if (this.isEdge && cachedSnapshot?.focusEdge) {
      this.hydrateNewEdgeFromSnapshot(cachedSnapshot);
    } else {
      this.fetchElementAndSubgraphData();
    }
  },
  methods: {
    consumeFocusGraphSnapshot() {
      const raw = sessionStorage.getItem(FOCUS_GRAPH_CACHE_KEY);
      if (!raw) return null;
      sessionStorage.removeItem(FOCUS_GRAPH_CACHE_KEY);
      try {
        return JSON.parse(raw);
      } catch (error) {
        console.warn("Failed to parse focus graph snapshot", error);
        return null;
      }
    },
    clearFocusGraphSnapshot() {
      sessionStorage.removeItem(FOCUS_GRAPH_CACHE_KEY);
    },
    buildFlowGraphFromRaw(rawNodes = [], rawEdges = []) {
      const formattedNodes = (rawNodes || []).map((node) => {
        const normalized = { ...node };
        if (
          typeof normalized.node_id === "string" &&
          normalized.node_id !== "new"
        ) {
          const numericId = Number(normalized.node_id);
          if (!Number.isNaN(numericId)) {
            normalized.node_id = numericId;
          }
        }
        return formatFlowNodeProps(normalized, this.colorBy);
      });
      const formattedEdges = (rawEdges || []).map((edge) => {
        const normalized = { ...edge };
        const resolvedSource =
          normalized.source ?? normalized.source_id ?? normalized.data?.source;
        const resolvedTarget =
          normalized.target ?? normalized.target_id ?? normalized.data?.target;
        if (resolvedSource != null) {
          const numericSource = Number(resolvedSource);
          normalized.source = Number.isNaN(numericSource)
            ? resolvedSource
            : numericSource;
        }
        if (resolvedTarget != null) {
          const numericTarget = Number(resolvedTarget);
          normalized.target = Number.isNaN(numericTarget)
            ? resolvedTarget
            : numericTarget;
        }
        return formatFlowEdgeProps(normalized, this.colorBy);
      });
      return { nodes: formattedNodes, edges: formattedEdges };
    },
    hydrateNewEdgeFromSnapshot(snapshot) {
      const rawEdge = snapshot?.focusEdge ? { ...snapshot.focusEdge } : null;
      if (!rawEdge) {
        this.fetchElementAndSubgraphData();
        return;
      }

      const sourceRaw = rawEdge.source ?? rawEdge.source_id;
      const targetRaw = rawEdge.target ?? rawEdge.target_id;
      const sourceIdNumber = Number(sourceRaw);
      const targetIdNumber = Number(targetRaw);
      const edge = {
        ...rawEdge,
        source:
          Number.isNaN(sourceIdNumber) || sourceRaw === "new"
            ? sourceRaw
            : sourceIdNumber,
        target:
          Number.isNaN(targetIdNumber) || targetRaw === "new"
            ? targetRaw
            : targetIdNumber,
        new: true,
      };

      const edgeTypeConfig = this.edgeTypes[edge.edge_type] || {};
      const allowed = edgeTypeConfig.properties || [];
      if (allowed.includes("description") && edge.description == null) {
        edge.description = "";
      }
      if (allowed.includes("references") && !Array.isArray(edge.references)) {
        edge.references = [];
      }

      const rawNodes = snapshot?.nodes || [];
      const resolveNodeType = (nodeId) => {
        if (nodeId == null || nodeId === "new") return null;
        const numeric = Number(nodeId);
        return rawNodes.find((node) => {
          const candidate = Number(node.node_id ?? node.id);
          return candidate === numeric;
        })?.node_type;
      };

      edge.sourceNodeType = edge.sourceNodeType || resolveNodeType(edge.source);
      edge.targetNodeType = edge.targetNodeType || resolveNodeType(edge.target);

      this.edge = edge;
      if (snapshot?.nodes?.length || snapshot?.edges?.length) {
        this.subgraphData = this.buildFlowGraphFromRaw(
          snapshot.nodes,
          snapshot.edges,
        );
      }
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
    async fetchElementAndSubgraphData() {
      console.log("fetchElementAndSubgraphData");
      try {
        this.ratings = {};
        const seed = this.nodeId || this.sourceId || this.targetId;
        const response = await api.get(`/graph/${seed}`, {
          params: { levels: this.depthLevel },
        });
        let fetched_nodes = response.data.nodes || [];
        const fetched_edges = response.data.edges || [];

        // Fetch and update node ratings as before
        await this.fetchNodeRatings(fetched_nodes.map((node) => node.node_id));
        fetched_nodes = this.updateNodesWithRatings(fetched_nodes);

        // Now fetch and update edge ratings
        const updatedEdges = await this.fetchEdgeRatings(fetched_edges);

        console.log("Fetched nodes:", fetched_nodes);
        this.node =
          fetched_nodes.find((node) => node.node_id === parseInt(seed)) || null;

        // Debug: Log the node to see if it has support
        if (this.node) {
          console.log(
            "Current node support:",
            this.node.support,
            "ratings:",
            this.ratings[this.node.node_id],
          );
        }

        if (this.sourceId && this.targetId) {
          this.edge =
            updatedEdges.find(
              (edge) =>
                edge.source === parseInt(this.sourceId) &&
                edge.target === parseInt(this.targetId),
            ) || null;
          const sourceNode = fetched_nodes.find(
            (n) => n.node_id === parseInt(this.sourceId),
          );
          const targetNode = fetched_nodes.find(
            (n) => n.node_id === parseInt(this.targetId),
          );
          this.edge = {
            ...this.edge,
            sourceNodeType: sourceNode?.node_type,
            targetNodeType: targetNode?.node_type,
          };
          console.log("Edge found !!!!!!!!!! :", this.edge);
        } else {
          this.edge = null;
        }
        // Build subgraphData using formatted nodes/edges.
        // Debug: Log nodes before formatting to check support property
        console.log(
          "Nodes before formatting:",
          fetched_nodes.map((n) => ({
            node_id: n.node_id,
            support: n.support,
            title: n.title,
          })),
        );

        this.subgraphData = {
          nodes: fetched_nodes.map((node) =>
            formatFlowNodeProps(node, this.colorBy),
          ),
          edges: updatedEdges.map((edge) =>
            formatFlowEdgeProps(edge, this.colorBy),
          ),
        };

        // Debug: Check what's actually in the formatted subgraphData
        console.log(
          "After formatting, first node.data:",
          this.subgraphData.nodes[0]?.data,
        );
      } catch (error) {
        console.error("Error fetching induced subgraph:", error);
        this.node = null;
        this.edge = null;
        this.subgraphData = { nodes: [], edges: [] };
      }
    },
    hydrateEdgeFromCache() {
      if (this.edge?.new) {
        return;
      }
      const s = Number(this.sourceId);
      const t = Number(this.targetId);
      const nodes = this.subgraphData.nodes;
      const edges = this.subgraphData.edges;

      const sourceNode = nodes.find((n) => n.node_id === s);
      const targetNode = nodes.find((n) => n.node_id === t);
      const edgeRaw = edges.find((e) => e.source === s && e.target === t);

      if (sourceNode && targetNode && edgeRaw) {
        // no network needed
        this.edge = {
          ...edgeRaw,
          sourceNodeType: sourceNode.node_type,
          targetNodeType: targetNode.node_type,
        };
      } else {
        // fallback to two cheap calls
        Promise.all([
          api.get(`/edges/${s}/${t}`),
          api.get(`/nodes/${s}`),
          api.get(`/nodes/${t}`),
        ]).then(([eRes, sRes, tRes]) => {
          this.edge = {
            ...eRes.data,
            sourceNodeType: sRes.data.node_type,
            targetNodeType: tRes.data.node_type,
          };
        });
      }
    },
    hydrateNodeFromCache() {
      const nodeId = this.nodeId;
      const nodes = this.subgraphData.nodes;
      const nodeRaw = nodes.find((n) => n.node_id === Number(nodeId));

      if (nodeRaw) {
        this.node = nodeRaw;
      } else {
        // fallback to a single call
        api.get(`/nodes/${nodeId}`).then((res) => {
          this.node = res.data;
        });
      }
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
      this.fetchElementAndSubgraphData();
    },
    updateColorBy(newColorBy) {
      console.log("Updating color by to:", newColorBy);
      this.colorBy = newColorBy;
      localStorage.setItem("graphColorBy", newColorBy);
      // Re-format the existing subgraph data with new colors (no API call needed!)
      this.reformatSubgraphData();
    },
    reformatSubgraphData() {
      // This method reformats the existing subgraph data without re-fetching from API
      // It's much faster for color changes
      if (!this.subgraphData.nodes || !this.subgraphData.edges) {
        return;
      }

      // Extract the raw data from the formatted nodes/edges
      const rawNodes = this.subgraphData.nodes.map((n) => n.data || n);
      const rawEdges = this.subgraphData.edges.map((e) => e.data || e);

      // Debug: Check if support is in the raw data
      console.log(
        "Reformatting - raw nodes:",
        rawNodes.map((n) => ({
          node_id: n.node_id,
          support: n.support,
          title: n.title,
        })),
      );
      console.log("Reformatting with colorBy:", this.colorBy);

      // Re-format with current colorBy setting
      this.subgraphData = {
        nodes: rawNodes.map((node) => formatFlowNodeProps(node, this.colorBy)),
        edges: rawEdges.map((edge) => formatFlowEdgeProps(edge, this.colorBy)),
      };
    },
    async updateNodeFromBackend(node_id) {
      try {
        const response = await api.get(`/nodes/${node_id}`);
        this.node = response.data || undefined;
      } catch (error) {
        console.error("Error fetching node:", error);
        this.node = undefined;
      }
    },
    async updateEdgeFromBackend(source_id, target_id) {
      try {
        const response = await api.get(`/edges/${source_id}/${target_id}`);
        this.edge = response.data || undefined;
      } catch (error) {
        console.error("Error fetching edge:", error);
        this.edge = undefined;
      }
    },
    updateNodeFromEditor(updatedNode) {
      console.log("Updating node from editor", updatedNode);
      try {
        this.node = { ...this.node, ...updatedNode, new: false };
        this.updatedNode = { ...updatedNode };
      } catch (error) {
        console.error("Failed to update node:", error);
      }
    },
    updateEdgeFromEditor(updatedEdge) {
      console.log("Updating edge from editor", updatedEdge);
      try {
        this.edge = { ...updatedEdge, new: true };
        this.updatedEdge = { ...updatedEdge };
      } catch (error) {
        console.error("Failed to update edge:", error);
      }
    },
    openNewlyCreatedNode(newNode) {
      this.node = {
        ...newNode.data,
        new: true,
        fromConnection: newNode.data.fromConnection,
      };
      this.$router.push({ name: "NodeEdit", params: { id: newNode.id } });
    },
    openNewlyCreatedEdge(newEdge) {
      // use this.edgeTypes instead of calling useConfig() again
      const allowed = this.edgeTypes[newEdge.data.edge_type].properties || [];
      this.edge = {
        source: parseInt(newEdge.data.source),
        target: parseInt(newEdge.data.target),
        edge_type: newEdge.data.edge_type,
        new: true,
      };
      if (allowed.includes("description")) this.edge.description = "";
      if (allowed.includes("references")) this.edge.references = [];
      this.$router.push({
        name: "EdgeEdit",
        params: {
          source_id: this.edge.source,
          target_id: this.edge.target,
        },
      });
    },
  },
};
</script>

<style scoped>
.focus {
  display: flex;
  height: 100%;
  overflow: hidden;
}

/* Left panel holds the info and rating cards */
.left-panel {
  width: 400px; /* Adjust width as needed */
  padding: 0 2px 0 0;
  box-sizing: border-box;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  gap: 4px; /* Space between cards */
  flex-shrink: 0; /* Don't shrink the left panel */
}

/* Card styling for left panel cards */
.card {
  border: 1px solid var(--border-color);
  border-radius: 5px;
  padding: 10px;
  margin: 0px;
}

/* Right panel for subgraph renderer; ensures full available space */
.right-panel {
  flex: 1;
  /* padding-left: 2px;
  padding-right: 10px;
  padding-bottom: 3px; */
  padding: 0px 11px 2px 3px;
  /* box-sizing: border-box; */
  overflow: hidden;
  min-width: 0;
  position: relative; /* For positioning controls */
}

.right-panel-header {
  position: absolute;
  top: 10px;
  right: 90px; /* Position from the right, leaving space for compass */
  left: auto; /* Override any left positioning */
  z-index: 10;
  display: flex;
  align-items: center;
  padding: 6px 10px;
  background-color: var(--background-color);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  pointer-events: auto;
  width: auto; /* Auto width based on content */
}

:global(body.dark) .right-panel-header {
  background-color: #333;
  border-color: #555;
}

.error-message {
  font-weight: bold;
  margin: 30px;
  text-align: center;
}
</style>
