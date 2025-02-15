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

      <template v-if="isNode && !isBrandNewNode">
        <div class="card">
          <ElementRating
            :key="node ? node.node_id : nodeId"
            :element="{ node_id: node ? node.node_id : nodeId }"
            property="support"
          />
        </div>
      </template>
      <template v-else-if="isEdge">
        <!-- <div class="card">
            <ElementRating
              :element="{ edge: { source: sourceId, target: targetId } }"
              property="causal_strength"
            />
          </div> -->
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
        </div>
      </template>
    </div>

    <div class="right-panel">
      <SubnetRenderer
        :data="subnetData"
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
import axios from "axios";
import NodeInfo from "../components/NodeInfo.vue";
import EdgeInfo from "../components/EdgeInfo.vue";
import ElementRating from "../components/ElementRating.vue";
import SubnetRenderer from "../components/SubnetRenderer.vue";
import {
  formatFlowEdgeProps,
  formatFlowNodeProps,
} from "../composables/formatFlowComponents";

export default {
  components: {
    NodeInfo,
    EdgeInfo,
    ElementRating,
    SubnetRenderer,
  },
  data() {
    return {
      node: undefined,
      edge: undefined,
      updatedNode: undefined,
      updatedEdge: undefined,
      subnetData: {},
      causalDirection: "LeftToRight",
    };
  },
  computed: {
    nodeId() {
      return this.$route.params.id;
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
  },
  created() {
    if (this.isBrandNewNode) {
      console.log("Opening brand new node in focus");
      this.node = {
        node_id: "new", // temporary id
        node_type: "action",
        title: "",
        scope: "",
        status: "live",
        tags: [],
        references: [],
        new: true,
      };
      this.$router.push({ name: "NodeEdit", params: { id: "new" } });
      let formattedNode = formatFlowNodeProps(this.node);
      formattedNode.label = "New Node";
      setTimeout(() => {
        this.subnetData = {
          nodes: [formattedNode],
          edges: [],
        };
      }, 45);
    } else {
      this.fetchElementAndSubnetData();
    }
  },
  methods: {
    async fetchElementAndSubnetData() {
      console.log("fetchElementAndSubnetData");
      try {
        const seed = this.nodeId || this.sourceId || this.targetId;
        const response = await axios.get(
          `${import.meta.env.VITE_BACKEND_URL}/subnet/${seed}`,
          { params: { levels: 10 } },
        );
        const fetched_nodes = response.data.nodes || [];
        const fetched_edges = response.data.edges || [];
        this.node =
          fetched_nodes.find((node) => node.node_id === parseInt(seed)) || null;
        if (this.sourceId && this.targetId) {
          this.edge =
            fetched_edges.find(
              (edge) =>
                edge.source === parseInt(this.sourceId) &&
                edge.target === parseInt(this.targetId),
            ) || null;
        }
        this.subnetData = {
          nodes: fetched_nodes.map((node) => formatFlowNodeProps(node)),
          edges: fetched_edges.map((edge) => formatFlowEdgeProps(edge)),
        };
      } catch (error) {
        console.error("Error fetching induced subnet:", error);
        this.node = null;
        this.edge = null;
        this.subnetData = { nodes: [], edges: [] };
      }
    },
    async updateNodeFromBackend(node_id) {
      try {
        const response = await axios.get(
          `${import.meta.env.VITE_BACKEND_URL}/node/${node_id}`,
        );
        this.node = response.data || undefined;
      } catch (error) {
        console.error("Error fetching node:", error);
        this.node = undefined;
      }
    },
    async updateEdgeFromBackend(source_id, target_id) {
      try {
        const response = await axios.get(
          `${import.meta.env.VITE_BACKEND_URL}/edge/${source_id}/${target_id}`,
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
        this.node = { ...updatedNode, new: false };
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
        node_id: newNode.id,
        title: "",
        node_type: newNode.data.node_type,
        scope: newNode.data.scope,
        status: "live",
        tags: newNode.data.tags,
        references: [],
        new: true,
        fromConnection: newNode.data.fromConnection,
      };
      this.$router.push({ name: "NodeEdit", params: { id: newNode.id } });
    },
    openNewlyCreatedEdge(newEdge) {
      this.edge = {
        source: newEdge.data.source,
        target: newEdge.data.target,
        edge_type: newEdge.data.edge_type,
        cprob: undefined,
        references: [],
        new: true,
      };
      this.$router.push({
        name: "EdgeEdit",
        params: {
          source_id: newEdge.data.source,
          target_id: newEdge.data.target,
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
  padding: 10px 10px 5px 10px;
  box-sizing: border-box;
  /* border-right: 1px solid green; */
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 15px; /* Space between cards */
}

/* Card styling for left panel cards */
.card {
  border: 1px solid var(--border-color);
  border-radius: 5px;
  padding: 10px;
  /* background-color: var(--background-color); */
}

/* Right panel for subnet renderer; ensures full available space */
.right-panel {
  flex: 1;
  padding: 10px 10px 10px 5px;
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
