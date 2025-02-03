<template>
  <div class="focus">
    <NodeInfo
      v-if="nodeId && node"
      :node="node"
      @update-node-from-editor="updateNodeFromEditor"
    />
    <div v-else-if="nodeId" class="error-message">Node not found</div>
    <EdgeInfo
      v-if="sourceId && targetId && edge"
      :edge="edge"
      @update-edge-from-editor="updateEdgeFromEditor"
    />
    <div v-else-if="sourceId && targetId" class="error-message">
      Edge not found
    </div>
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
</template>

<script>
import axios from "axios";
import NodeInfo from "../components/NodeInfo.vue";
import EdgeInfo from "../components/EdgeInfo.vue";
import SubnetRenderer from "../components/SubnetRenderer.vue";
import {
  formatFlowEdgeProps,
  formatFlowNodeProps,
} from "../composables/formatFlowComponents";
import _ from "lodash";

export default {
  components: {
    NodeInfo,
    EdgeInfo,
    SubnetRenderer: SubnetRenderer,
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
  },
  created() {
    if (this.isBrandNewNode) {
      console.log("opening brand new node in focus");
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

      // console.log('formatFlowNodeProps(this.node)', formatFlowNodeProps(this.node));
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
    getBorderWidthByType(nodeType) {
      const typeToBorderWidthMap = {
        change: "1px",
        potentiality: "1px",
        action: "2px",
        proposal: "3px",
        objective: "4px",
      };
      return typeToBorderWidthMap[nodeType];
    },

    async fetchElementAndSubnetData() {
      console.log("fetchElementAndSubnetData");
      try {
        console.time("axiosRequest");

        const seed = this.nodeId || this.sourceId || this.targetId;
        //TODO: allow fetching subnet from two seeds instead of one
        const response = await axios.get(
          `${import.meta.env.VITE_BACKEND_URL}/subnet/${seed}`,
          {
            params: {
              levels: 10,
            },
          },
        );
        console.timeEnd("axiosRequest");
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
          nodes: fetched_nodes.map((node) => {
            const props = formatFlowNodeProps(node);
            return props;
          }),
          edges: fetched_edges.map((edge) => {
            const props = formatFlowEdgeProps(edge);
            return props;
          }),
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
    // currently useful to swap between edit and view mode
    // also to reduce chances of misalignment between backend and frontend data after update
    updateNodeFromEditor(updatedNode) {
      console.log("updating node from editor", updatedNode);
      try {
        this.node = { ...updatedNode, new: false }; // node in focus with new set to false
        this.updatedNode = { ...updatedNode }; // trigger update on graph view with new unchanged
      } catch (error) {
        console.error("Failed to update node:", error);
      }
    },
    // currently useful to swap between edit and view mode
    // also to reduce changes of misalignment between backend and frontend data after update
    updateEdgeFromEditor(updatedEdge) {
      console.log("updating edge from editor", updatedEdge);
      try {
        this.edge = { ...updatedEdge, new: true }; // edge in focus
        this.updatedEdge = { ...updatedEdge }; // trigger update on graph view
      } catch (error) {
        console.error("Failed to update edge:", error);
      }
    },
    openNewlyCreatedNode(newNode) {
      this.node = {
        node_id: newNode.id, // temporary id
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
  flex-grow: 1;
}
.error-message {
  font-weight: bold;
  margin: auto;
  padding: 30px 50px;
}
</style>
