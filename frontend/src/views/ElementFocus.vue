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

       <template v-if="isNode && nodePollsCount">
        <div class="card" 
             v-for="(pollConfig, pollLabel) in nodePolls" 
             :key="`node-${pollLabel}-${node.node_id}`">
          <ElementPollPane
            :element="{ node_id: node.node_id }"
            :poll-label="pollLabel"
            :poll-config="pollConfig"
          />
        </div>
      </template>

      <template v-else-if="isEdge && edgePollsCount">
        <div class="card"
             v-for="(pollConfig, pollLabel) in edgePolls"
             :key="`edge-${pollLabel}-${edge.source}-${edge.target}`">
          <ElementPollPane
            :element="{ edge: { source: edge.source, target: edge.target } }"
            :poll-label="pollLabel"
            :poll-config="pollConfig"
          />
        </div>
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
import { useConfig } from "../composables/useConfig";
import NodeInfo from "../components/node/NodeInfo.vue";
import EdgeInfo from "../components/edge/EdgeInfo.vue";
import ElementPollPane from "../components/poll/ElementPollPane.vue";
import SubgraphRenderer from "../components/graph/SubgraphRenderer.vue";
import {
  formatFlowEdgeProps,
  formatFlowNodeProps,
} from "../composables/formatFlowComponents";
import api from "../api/axios";
import { hydrate } from "vue";

export default {
  components: {
    NodeInfo,
    EdgeInfo,
    ElementPollPane,
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
  watch: {
    '$route.params.id'() {
      if (this.id) {
        this.hydrateNodeFromCache();
      }
    },
    '$route.params.source_id'() {
      console.log("Source ID changed to:", this.sourceId);
      if (this.sourceId) {
        this.hydrateEdgeFromCache();
      }
    },
    '$route.params.target_id'() {
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
       if (!this.node?.node_type) return []
       console.log("node Types allowed", this.nodeTypes);
       return this.nodeTypes[this.node.node_type].properties || []
    },
    allowedEdgeFields() {
      if (!this.edge?.edge_type) return []
      return this.edgeTypes[this.edge.edge_type].properties || []
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
          `/graph/${seed}`,
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
          const sourceNode = fetched_nodes.find(n => n.node_id === parseInt(this.sourceId));
          const targetNode = fetched_nodes.find(n => n.node_id === parseInt(this.targetId));
          this.edge = {
           ...this.edge,
           sourceNodeType: sourceNode?.node_type,
           targetNodeType: targetNode?.node_type
          };
          console.log("Edge found !!!!!!!!!! :", this.edge);
        } else {
          this.edge = null;
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
    hydrateEdgeFromCache() {
      const s = Number(this.sourceId)
      const t = Number(this.targetId)
      const nodes = this.subgraphData.nodes
      const edges = this.subgraphData.edges

      const sourceNode = nodes.find((n) => n.node_id === s)
      const targetNode = nodes.find((n) => n.node_id === t)
      const edgeRaw    = edges.find((e) => e.source === s && e.target === t)

      if (sourceNode && targetNode && edgeRaw) {
        // no network needed
        this.edge = {
          ...edgeRaw,
          sourceNodeType: sourceNode.node_type,
          targetNodeType: targetNode.node_type
        }
      }
      else {
        // fallback to two cheap calls
        Promise.all([
          api.get(`/edges/${s}/${t}`),
          api.get(`/nodes/${s}`),
          api.get(`/nodes/${t}`)
        ]).then(([eRes, sRes, tRes])=>{
          this.edge = {
            ...eRes.data,
            sourceNodeType: sRes.data.node_type,
            targetNodeType: tRes.data.node_type
          }
        })
      }
    },
    hydrateNodeFromCache() {
      const nodeId = this.nodeId
      const nodes = this.subgraphData.nodes
      const nodeRaw = nodes.find((n) => n.node_id === Number(nodeId))

      if (nodeRaw) {
        this.node = nodeRaw
      } else {
        // fallback to a single call
        api.get(`/nodes/${nodeId}`).then((res) => {
          this.node = res.data
        })
      }
    },
    async fetchNodeRatings(nodeIds) {
      if (!nodeIds.length) return;
      try {
        const { data } = await api.get("/nodes/ratings/median", {
          params: { node_ids: nodeIds },
        });
        this.ratings = data;
        console.log("Fetched node ratings:", this.ratings);
      } catch (err) {
        console.error("Error fetching node ratings:", err);
      }
    },

    async fetchEdgeRatings(edges) {
      if (!edges.length) return edges;
      try {
        const edgeKeys = edges.map((e) => `${e.source}-${e.target}`);
        const { data: edgeRatings } = await api.get(
          "/edges/ratings/median",
          { params: { edge_ids: edgeKeys } }
        );
        return edges.map((edge) => {
          const key = `${edge.source}-${edge.target}`;
          edge.causal_strength = edgeRatings[key]?.median_rating ?? null;
          return edge;
        });
      } catch (err) {
        console.error("Error fetching edge ratings:", err);
        return edges;
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
          `/nodes/${node_id}`,
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
          `/edges/${source_id}/${target_id}`,
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
    openNewlyCreatedEdge(newEdge) {
      // use this.edgeTypes instead of calling useConfig() again
      const allowed = this.edgeTypes[newEdge.data.edge_type].properties || [];
      this.edge = {
        source: parseInt(newEdge.data.source),
        target: parseInt(newEdge.data.target),
        edge_type: newEdge.data.edge_type,
        new: true,
      };
      if (allowed.includes("description"))    this.edge.description = "";
      if (allowed.includes("references"))     this.edge.references = [];
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
