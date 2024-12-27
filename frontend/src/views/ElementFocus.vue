<template>
  <div class="focus">
    <NodeInfo
      v-if="!targetId"
      :node="node"
      @update-node-from-editor="updateNodeFromEditor"
    />
    <EdgeInfo
      v-if="targetId && edge && Object.keys(edge).length"
      :edge="edge"
      @update-edge-from-editor="updateEdgeFromEditor"
    />
    <SubnetRenderer
      :data="subnetData"
      @nodeClick="updateNodeFromBackend"
      @edgeClick="updateEdgeFromBackend"
      @newNodeCreated="openNewlyCreatedNode"
      @newEdgeCreated="openNewlyCreatedEdge"
      :focusNode="node"
      :focusEdge="edge"
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

      // console.log('formatFlowNodeProps(this.node)', formatFlowNodeProps(this.node));
      const formattedNode = formatFlowNodeProps(this.node);

      setTimeout(() => {
        this.subnetData = {
          nodes: [formattedNode],
          edges: [],
        };
      }, 5);
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
        const response = await axios.get(
          `${import.meta.env.VITE_BACKEND_URL}/subnet/${this.nodeId}`,
          {
            params: {
              levels: 10,
            },
          },
        );
        console.timeEnd("axiosRequest");
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
        // if (this.node.node_id === "new" || updatedNode.new) {
        //   console.log("updating new node ID on the graph");
        //   // find the new node in the subnetData and update it
        //   console.log('this.subnetData.nodes', this.subnetData.nodes);
        //   let tempNode = this.subnetData.nodes.find(
        //     (node) => node.id === "new",
        //   );
        //   if (tempNode) {
        //     console.log('updating tempNode.id', updatedNode.node_id);
        //     tempNode.id = updatedNode.node_id;
        //   }
        // }
        //append formatted node to subnetData.nodes
        // this.subnetData.nodes.push(formatFlowNodeProps(updatedNode));
        this.node = updatedNode;
      } catch (error) {
        console.error("Failed to update node:", error);
      }
    },
    // currently useful to swap between edit and view mode
    // also to reduce changes of misalignment between backend and frontend data after update
    updateEdgeFromEditor(updatedEdge) {
      console.log("updating edge from editor", updatedEdge);
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
  },
};
</script>

<style scoped>
.focus {
  display: flex;
  flex-grow: 1;
}
</style>
