<template>
  <div class="focus">
    <NodeInfo v-if="!targetId" :node="node" @update-node="updateNode" />
    <EdgeInfo v-if="targetId && edge && Object.keys(edge).length" :edge="edge" @update-edge="updateEdge" />
    <GraphRenderer :data="graphData" @nodeClick="updateNodeFromBackend" @edgeClick="updateEdgeFromBackend" @newNodeCreated="openNewlyCreatedNode"/>
  </div>
</template>

<script>
import axios from 'axios';
import { Position } from '@vue-flow/core';
import NodeInfo from '../components/NodeInfo.vue';
import EdgeInfo from '../components/EdgeInfo.vue';
import GraphRenderer from '../components/GraphRenderer.vue';
import { ref } from 'vue';

export default {
  components: {
    NodeInfo,
    EdgeInfo,
    GraphRenderer,
  },
  data() {
    return {
      node: undefined,
      edge: undefined,
      graphData: {},
      causalDirection: 'LeftToRight',
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
      return this.$route.path.endsWith('/edit');
    },
  },
  created() {
    this.fetchElementAndSubgraphData();
  },
  methods: {
    async fetchElementAndSubgraphData() {
      try {
        const response = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/subgraph/${this.nodeId}`, {
          params: {
            levels: 5
          }
        });
        const fetched_nodes = response.data.nodes;
        const fetched_edges = response.data.edges;

        this.node = fetched_nodes.find(node => node.node_id === parseInt(this.nodeId)) || undefined;

        if (this.sourceId !== undefined && this.targetId !== undefined) {
          this.edge = fetched_edges.find(edge => edge.source === parseInt(this.sourceId) && edge.target === parseInt(this.targetId)) || undefined;
        }

        this.graphData = {
          nodes: fetched_nodes.map(node => ({
            id: node.node_id.toString(),
            position: { x: Math.random() * 500, y: Math.random() * 500 },
            data: {
              label: node.title, // move out of data? 
              title: node.title,
              scope: node.scope,
              node_type: node.node_type,
              gradable: node.gradable !== undefined ? node.gradable : node.node_type === "proposal",
              grade: node.grade,
            }
          })),
          edges: fetched_edges.map(edge => {
            const edgeLabel = edge.edge_type.toString();
            let source = edgeLabel === "imply" ? edge.source.toString() : edge.target.toString();
            let target = edgeLabel === "imply" ? edge.target.toString() : edge.source.toString();

            return {
              id: `${edge.source}-${edge.target}`,
              source: source,
              target: target,
              label: edgeLabel,
              markerEnd: edgeLabel === 'imply' ? "arrowclosed" : undefined,
              markerStart: edgeLabel === 'require' ? "arrowclosed" : undefined,
              data: {
                edge_type: edgeLabel,
                cprob: edge.cprob !== null ? edge.cprob * 100 : null,
                source: edge.source,
                target: edge.target,
                references: edge.references,
              },
            };
          })
        };
      } catch (error) {
        console.error('Error fetching induced subgraph:', error);
      }
    },
    async updateNodeFromBackend(node_id) {
      try {
        const response = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/nodes/${node_id}`);
        this.node = response.data || undefined;
      } catch (error) {
        console.error('Error fetching node:', error);
        this.node = undefined;
      }
    },
    async updateEdgeFromBackend(source_id, target_id) {
      try {
        const response = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/edges/${source_id}/${target_id}`);
        this.edge = response.data || undefined;
      } catch (error) {
        console.error('Error fetching edge:', error);
        this.edge = undefined;
      }
    },
    async updateNode(updatedNode) {
      try {
        this.node = updatedNode;
      } catch (error) {
        console.error('Failed to update node:', error);
      }
    },
    async updateEdge(updatedEdge) {
      try {
        this.edge = updatedEdge;
        // this.updateGraphEdge(response.data);
      } catch (error) {
        console.error('Failed to update edge:', error);
      }
    },
    openNewlyCreatedNode(newNode) {
      this.node = {
        node_id: newNode.id,  // temporary id
        title: newNode.data.title,
        scope: newNode.data.scope,
        node_type: newNode.data.node_type,
        references: [],
        new: true,
        fromConnection: newNode.data.fromConnection,
        // gradable: newNode.data.gradable,
        // grade: newNode.data.grade,
      };
      this.$router.push({ name: 'NodeEdit', params: { id: newNode.id } });
    },
    updateGraphNode(updatedNode) {
      const nodeIndex = this.graphData.nodes.findIndex(node => node.id === updatedNode.id.toString());
      if (nodeIndex !== -1) {
        this.graphData.nodes[nodeIndex].data = {
          ...this.graphData.nodes[nodeIndex].data,
          ...updatedNode,
        };
      }
    },
    updateGraphEdge(updatedEdge) {
      const edgeIndex = this.graphData.edges.findIndex(edge => edge.id === `${updatedEdge.source}-${updatedEdge.target}`);
      if (edgeIndex !== -1) {
        this.graphData.edges[edgeIndex].data = {
          ...this.graphData.edges[edgeIndex].data,
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

.graph-renderer {
  flex-grow: 1;
  border: 1px solid #ccc;
  margin: 5px;
}
</style>