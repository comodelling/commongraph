<template>
  <div class="focus">
    <NodeInfo v-if="!targetId" :node="node" @update-node="updateNode" />
    <EdgeInfo v-if="targetId && edge && Object.keys(edge).length" :edge="edge" @update-edge="updateEdge" />
    <GraphRenderer :data="graphData" @nodeClick="updateNodeFromBackend" @edgeClick="updateEdgeFromBackend" @newNodeCreated="openNewlyCreatedNode" @newEdgeCreated="openNewlyCreatedEdge"/>
  </div>
</template>

<script>
import axios from 'axios';
import NodeInfo from '../components/NodeInfo.vue';
import EdgeInfo from '../components/EdgeInfo.vue';
import GraphRenderer from '../components/GraphRenderer.vue';

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
      return this.$route.params.id || this.$route.params.source_id;
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
    isBrandNewNode() {
      return this.nodeId === "new";  //TODO: distinguish brand new node and one from connection
    }
  },
  created() {
    // console.log('isbrandnewnode', this.isBrandNewNode)
    if (this.isBrandNewNode) {
      console.log('opening brand new node in focus');
      this.node = {
        node_id: 'new',  // temporary id
        node_type: "action",
        title: "New Node",
        scope: "Enter a scope",
        status: 'draft',
        references: [],
        new: true,
      };
      this.$router.push({ name: 'NodeEdit', params: { id: "new" } });
    }
    else {
      this.fetchElementAndSubgraphData();
    }
  },

  methods: {

    getBorderWidthByType(nodeType) {
      const typeToBorderWidthMap = {
        'change': '1px',
        'action': '2px',
        'proposal': '3px',
        'objective': '4px',
        // Add more mappings as needed
      };
      return typeToBorderWidthMap[nodeType]; // Default to 1 if type not found
    },

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
          nodes: fetched_nodes.map(node => {
            const style = {
              opacity: node.status === 'completed' ? 0.4 : 0.95, 
              borderColor: node.status === 'completed' ? 'green' : 'black',
              borderWidth: this.getBorderWidthByType(node.node_type),
              borderStyle: node.status === 'draft' ? 'dotted' : 'solid', // Ensure border style is set
              borderRadius: '8px',
            };
            console.log('Node style:', style); // Added console log to check the style object
            return {
              id: node.node_id.toString(),
              position: { x: Math.random() * 500, y: Math.random() * 500 },
              label: node.title, // move out of data? 
              style: style,  // define rule in custom node component
              data: {
                node_id: node.node_id,
                title: node.title,
                node_type: node.node_type,
                scope: node.scope,
                status: node.status,
                gradable: node.gradable,
                grade: node.grade,
              }
            };
          }),
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
                cprob: edge.cprob,
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
        console.log('response from edges/ api call', response.data);
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
        node_type: newNode.data.node_type,
        scope: newNode.data.scope,
        status: 'draft',
        references: [],
        new: true,
        fromConnection: newNode.data.fromConnection,
        // gradable: newNode.data.gradable,
        // grade: newNode.data.grade,
      };
      this.$router.push({ name: 'NodeEdit', params: { id: newNode.id } });
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
      this.$router.push({ name: 'EdgeEdit', params: { source_id: newEdge.data.source, target_id:  newEdge.data.target} });
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

</style>