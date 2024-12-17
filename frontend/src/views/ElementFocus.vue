<template>
  <div class="focus">
    <NodeInfo v-if="!targetId" :node="node" @update-node="updateNode" />
    <EdgeInfo
      v-if="targetId && edge && Object.keys(edge).length"
      :edge="edge"
      @update-edge="updateEdge"
    />
    <SubnetRenderer
      :data="subnetData"
      @nodeClick="updateNodeFromBackend"
      @edgeClick="updateEdgeFromBackend"
      @newNodeCreated="openNewlyCreatedNode"
      @newEdgeCreated="openNewlyCreatedEdge"
    />
  </div>
</template>

<script>
import axios from "axios";
import NodeInfo from "../components/NodeInfo.vue";
import EdgeInfo from "../components/EdgeInfo.vue";
import SubnetRenderer from "../components/SubnetRenderer.vue";

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
      subnetData: {},
      causalDirection: "LeftToRight",
    };
  },
  computed: {
    nodeId() {
      return this.$route.params.id || this.$route.params.source_id;
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
        node_type: "potentiality",
        title: "New Node",
        scope: "",
        status: "draft",
        tags: [],
        references: [],
        new: true,
      };
      this.$router.push({ name: "NodeEdit", params: { id: "new" } });
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
      try {
        const response = await axios.get(
          `${import.meta.env.VITE_BACKEND_URL}/subnet/${this.nodeId}`,
          {
            params: {
              levels: 5,
            },
          },
        );
        const fetched_nodes = response.data.nodes;
        const fetched_edges = response.data.edges;

        this.node =
          fetched_nodes.find(
            (node) => node.node_id === parseInt(this.nodeId),
          ) || undefined;

        if (this.sourceId !== undefined && this.targetId !== undefined) {
          this.edge =
            fetched_edges.find(
              (edge) =>
                edge.source === parseInt(this.sourceId) &&
                edge.target === parseInt(this.targetId),
            ) || undefined;
        }

        this.subnetData = {
          nodes: fetched_nodes.map((node) => {
            const style = {
              opacity: node.status === "completed" ? 0.4 : 0.95,
              borderColor: node.status === "completed" ? "green" : "black",
              borderWidth: this.getBorderWidthByType(node.node_type),
              borderStyle: node.status === "draft" ? "dotted" : "solid",
              borderRadius: "8px",
            };
            return {
              id: node.node_id.toString(),
              position: { x: Math.random() * 500, y: Math.random() * 500 },
              label: node.title, // move out of data?
              style: style, // define rule in custom node component
              data: {
                ...node,
              },
            };
          }),
          edges: fetched_edges.map((edge) => {
            const edgeLabel = edge.edge_type.toString();
            let source =
              edgeLabel === "imply"
                ? edge.source.toString()
                : edge.target.toString();
            let target =
              edgeLabel === "imply"
                ? edge.target.toString()
                : edge.source.toString();

            return {
              id: `${edge.source}-${edge.target}`,
              source: source,
              target: target,
              label: edgeLabel,
              markerEnd: edgeLabel === "imply" ? "arrowclosed" : undefined,
              markerStart: edgeLabel === "require" ? "arrowclosed" : undefined,
              data: {
                ...edge,
              },
            };
          }),
        };
      } catch (error) {
        console.error("Error fetching induced subnet:", error);
      }
    },
    async updateNodeFromBackend(node_id) {
      try {
        const response = await axios.get(
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
        const response = await axios.get(
          `${import.meta.env.VITE_BACKEND_URL}/edges/${source_id}/${target_id}`,
        );
        console.log("response from edges/ api call", response.data);
        this.edge = response.data || undefined;
      } catch (error) {
        console.error("Error fetching edge:", error);
        this.edge = undefined;
      }
    },
    async updateNode(updatedNode) {
      try {
        this.node = updatedNode;
      } catch (error) {
        console.error("Failed to update node:", error);
      }
    },
    async updateEdge(updatedEdge) {
      try {
        this.edge = updatedEdge;
      } catch (error) {
        console.error("Failed to update edge:", error);
      }
    },
    openNewlyCreatedNode(newNode) {
      this.node = {
        node_id: newNode.id, // temporary id
        title: newNode.data.title,
        node_type: newNode.data.node_type,
        scope: newNode.data.scope,
        status: "draft",
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
    updateNodeViz(updatedNode) {
      const nodeIndex = this.subnetData.nodes.findIndex(
        (node) => node.id === updatedNode.id.toString(),
      );
      if (nodeIndex !== -1) {
        this.subnetData.nodes[nodeIndex].data = {
          ...this.subnetData.nodes[nodeIndex].data,
          ...updatedNode,
        };
      }
    },
    updateEdgeViz(updatedEdge) {
      const edgeIndex = this.subnetData.edges.findIndex(
        (edge) => edge.id === `${updatedEdge.source}-${updatedEdge.target}`,
      );
      if (edgeIndex !== -1) {
        this.subnetData.edges[edgeIndex].data = {
          ...this.subnetData.edges[edgeIndex].data,
          ...updatedEdge,
        };
      }
    },
  },
};
</script>

<style scoped>
.focus {
  display: flex;
  flex-grow: 1;
}
</style>
