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

      <template v-if="isNode && !isBrandNewNode && this.allowedNodeFields.includes('support_rating')">
        <div class="card">
          <ElementRating
            :key="node ? node.node_id : nodeId"
            :element="{ node_id: node ? node.node_id : nodeId }"
            property="support"
          />
        </div>
      </template>
      
      <template v-else-if="isEdge && this.allowedEdgeFields.includes('causal_strength_rating')" >
        <div class="card">
          <ElementRating
            :key="
              edge ? `${edge.source}-${edge.target}` : `${sourceId}-${targetId}`
            "
            :element="{
              edge: edge
                ? { source: edge.source, target: edge.target }
                : { source: sourceId, target: targetId },
            }"
            property="causal_strength"
          />
        </div>
        <!-- <div class="card">
          <ElementRating
            :key="
              edge ? `${edge.source}-${edge.target}` : `${sourceId}-${targetId}`
            "
            :element="{
              edge: edge
                ? { source: edge.source, target: edge.target }
                : { source: sourceId, target: targetId },
            }"
            property="necessity"
          />
        </div>
        <div class="card">
          <ElementRating
            :key="
              edge
                ? `${edge.source}-${edge.target}-sufficiency`
                : `${sourceId}-${targetId}-sufficiency`
            "
            :element="{
              edge: edge
                ? { source: edge.source, target: edge.target }
                : { source: sourceId, target: targetId },
            }"
            property="sufficiency"
          />
        </div> -->
      </template>
    </div>

    <div class="right-panel">
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
import { onBeforeMount, ref } from 'vue'
import { useConfig } from "../composables/useConfig";
import NodeInfo from "../components/NodeInfo.vue";
import EdgeInfo from "../components/EdgeInfo.vue";
import ElementRating from "../components/ElementRating.vue";
import SubgraphRenderer from "../components/SubgraphRenderer.vue";
import {
  formatFlowEdgeProps,
  formatFlowNodeProps,
} from "../composables/formatFlowComponents";
import api from "../axios";

export default {
  components: {
    NodeInfo,
    EdgeInfo,
    ElementRating,
    SubgraphRenderer,
  },
  setup() {
    const { nodeTypes, edgeTypes, defaultNodeType} = useConfig()
 
    // nodeTypes & edgeTypes will be unwrapped when used in `this.*`
    return { nodeTypes, edgeTypes, defaultNodeType}
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
    };
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
       if (!this.node?.node_type) return []
       console.log("node Types allowed", this.nodeTypes);
       return this.nodeTypes[this.node.node_type].properties || []
    },
    allowedEdgeFields() {
      if (!this.edge?.edge_type) return []
      return this.edgeTypes[this.edge.edge_type].properties || []
    },
  },
  // when opening a brand-new node, use defaultNodeType and only include allowed props
  async created() {
    if (this.isBrandNewNode) {

      console.log("Opening brand new node in focus");
      const type = this.defaultNodeType;
      console.log("Default node type:", type);
      // const allowed = this.allowedNodeFields.value || [];
      const allowed = this.nodeTypes[type].properties || [];
      console.log("Allowed node props:", allowed);
      // build minimal node object
      const node = { node_id: "new", node_type: type, new: true };
      if (allowed.includes("title"))      node.title = "";
      if (allowed.includes("scope"))      node.scope = "";
      if (allowed.includes("status"))     node.status = "live";
      if (allowed.includes("tags"))       node.tags = [];
      if (allowed.includes("references")) node.references = [];
      if (allowed.includes("description")) node.description = "";
      this.node = node;
      this.$router.push({ name: "NodeEdit", params: { id: "new" } });
      let formattedNode = formatFlowNodeProps(this.node);
      formattedNode.label = "New Node";
      // small delay so VueFlow has time to mount
      setTimeout(() => {
        this.subgraphData = { nodes: [formattedNode], edges: [] };
      }, 45);
    } else {
      this.fetchElementAndSubgraphData();
    }
  },
  methods: {
    async fetchElementAndSubgraphData() {
      console.log("fetchElementAndSubgraphData");
      try {
        const seed = this.nodeId || this.sourceId || this.targetId;
        const response = await api.get(
          `${import.meta.env.VITE_BACKEND_URL}/graph/${seed}`,
          { params: { levels: 10 } },
        );
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
        if (this.sourceId && this.targetId) {
          this.edge =
            updatedEdges.find(
              (edge) =>
                edge.source === parseInt(this.sourceId) &&
                edge.target === parseInt(this.targetId),
            ) || null;
        }
        // Build subgraphData using formatted nodes/edges.
        this.subgraphData = {
          nodes: fetched_nodes.map((node) => formatFlowNodeProps(node)),
          edges: updatedEdges.map((edge) => formatFlowEdgeProps(edge)),
        };
      } catch (error) {
        console.error("Error fetching induced subgraph:", error);
        this.node = null;
        this.edge = null;
        this.subgraphData = { nodes: [], edges: [] };
      }
    },
    async fetchNodeRatings(nodeIds) {
      if (!nodeIds.length) return;
      try {
        const response = await api.get(
          `${import.meta.env.VITE_BACKEND_URL}/rating/nodes/median`,
          { params: { node_ids: nodeIds } },
        );
        this.ratings = response.data; // Ratings stored separately
        console.log("Fetched ratings:", this.ratings);
        // Once ratings are fetched, update the node colours.
      } catch (error) {
        console.error("Error fetching node ratings:", error);
      }
    },

    async fetchEdgeRatings(edges) {
      if (!edges.length) return edges;
      try {
        // Build an array of keys from edges in the form "source-target"
        const edgeKeys = edges.map((edge) => `${edge.source}-${edge.target}`);
        const response = await api.get(
          `${import.meta.env.VITE_BACKEND_URL}/rating/edges/median`,
          { params: { edge_ids: edgeKeys } },
        );
        const edgeRatings = response.data; // Expecting an object keyed by "source-target"
        // Update each edge with the median rating, stored as causal_strength_rating.
        return edges.map((edge) => {
          const key = `${edge.source}-${edge.target}`;
          edge.causal_strength =
            edgeRatings[key] && edgeRatings[key].median_rating
              ? edgeRatings[key].median_rating
              : null;
          return edge;
        });
      } catch (error) {
        console.error("Error fetching edge ratings:", error);
        return edges; // Fallback: return original edges
      }
    },
    updateNodesWithRatings(rawNodes) {
      return rawNodes.map((node) => {
        if (
          this.ratings[node.node_id] &&
          this.ratings[node.node_id].median_rating
        ) {
          node.support = this.ratings[node.node_id].median_rating;
        }
        return node;
      });
    },
    async updateNodeFromBackend(node_id) {
      try {
        const response = await api.get(
          `${import.meta.env.VITE_BACKEND_URL}/nodes/${node_id}`,
        );
        this.node = response.data || undefined;
      } catch (error) {
        console.error("Error fetching node:", error);
        this.node = undefined;
      }
    },
    async updateEdgeFromBackend(source_id, target_id) {
      try {
        const response = await api.get(
          `${import.meta.env.VITE_BACKEND_URL}/edges/${source_id}/${target_id}`,
        );
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
      this.node = {...newNode.data,
        new: true,
        fromConnection: newNode.data.fromConnection,
      };
      this.$router.push({ name: "NodeEdit", params: { id: newNode.id } });
    },
    async openNewlyCreatedEdge(newEdge) {
      const { edgeTypes } = useConfig();
      const allowed = edgeTypes.value[newEdge.data.edge_type].properties || [];
      console.log("Allowed edge props:", allowed);

      this.edge = {
        source: parseInt(newEdge.data.source),
        target: parseInt(newEdge.data.target),
        edge_type: newEdge.data.edge_type,
        // references: [],
        new: true,
      };
      if (allowed.includes("description")) 
        this.edge.description = "";
      if (allowed.includes("references"))
        this.edge.references = [];

      this.$router.push({
        name: "EdgeEdit",
        params: {
          source_id: parseInt(newEdge.data.source),
          target_id: parseInt(newEdge.data.target)
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
  /* flex-grow: 1; */
  /* border: 1px solid blue; */
}

/* Left panel holds the info and rating cards */
.left-panel {
  width: 400px; /* Adjust width as needed */
  padding: 4px 4px 2px 4px;
  box-sizing: border-box;
  /* border-right: 1px solid green; */
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 5px; /* Space between cards */
  /* border: 1px solid var(--border-color); */
}

/* Card styling for left panel cards */
.card {
  border: 1px solid var(--border-color);
  border-radius: 5px;
  padding: 10px;
  margin: 0px;
  /* background-color: var(--background-color); */
}

/* Right panel for subgraph renderer; ensures full available space */
.right-panel {
  flex: 1;
  padding: 3px 9px 4px 2px;
  box-sizing: border-box; /* Include padding in height calculations */
  overflow-y: auto;
  overflow-x: hidden; /* Prevent horizontal scrolling */
  /* border: 1px solid red; */
}
.error-message {
  font-weight: bold;
  margin: 30px;
  text-align: center;
}
</style>
