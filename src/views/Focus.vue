<template>
  <div class="focus">
      <NodeInfo v-if="!targetId" :node="node" />
      <EdgeInfo v-if="targetId && edge && Object.keys(edge).length" :edge="edge" />
      <GraphRenderer :data="graphData"  @nodeClick="updateNodeInfo"  @edgeClick="updateEdgeInfo"/>
  </div>
</template>

<script>
import axios from 'axios';
import { Position } from '@vue-flow/core'
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
      node: undefined, // Object to hold node data
      edge: undefined, // Object to hold edge data
      graphData: {}, // Object to hold graph data
      causalDirection: 'LeftToRight', // Direction for positions
    };
  },
  computed: {
    nodeId() {
      return this.$route.params.id; // Get element ID from route
    },
    targetId() {
      console.log('targetId', this.$route.params.targetId);
      return this.$route.params.targetId; // Get target element ID from route
    },
    handlePosition() {
      console.log('causalDirection', this.causalDirection);
      switch (this.causalDirection) {
        case 'LeftToRight':
          return { target: Position.Left, source: Position.Right };
        case 'RightToLeft':
          return { target: Position.Right, source: Position.Left };
        case 'TopToBottom':
          return { target: Position.Top, source: Position.Bottom };
        case 'BottomToTop':
          return { target: Position.Bottom, source: Position.Top };
        default:
          return { target: Position.Left, source: Position.Right };
      }
    },
  },

  created() {
    this.fetchElementAndSubgraphData(); // Fetch the element data on creation
  },
  methods: {
    async fetchElementAndSubgraphData() {

      try {
        console.log(this.targetId);
        const response = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/subgraph/${this.nodeId}`);
        const fetched_nodes = response.data.nodes;
        const fetched_edges = response.data.edges;
        console.log('fetching subgraph for node id', this.nodeId);
        this.node  = fetched_nodes.find(node => node.node_id === parseInt(this.nodeId)) || undefined;  //TODO: maybe parse incoming data even before this
        console.log('fetched element', this.node);
        console.log('fetched induced subgraph', fetched_nodes, fetched_edges);

        if (this.targetId !== undefined) {
          console.log('fetching edge for target id', this.targetId);
          this.edge = fetched_edges.find(edge => edge.source === parseInt(this.nodeId) && edge.target === parseInt(this.targetId)) || undefined;
          console.log('fetched edge', this.edge);
        }

        this.graphData = {
          nodes: fetched_nodes.map(node => ({
            // type: 'special',
            id: node.node_id.toString(),
            position: { x: Math.random() * 500, y: Math.random() * 500 }, // Random positions for example

            // sourcePosition: this.handlePosition.source,
            // targetPosition: this.handlePosition.target,
            data: {
              label: node.title,
              title: node.title,
              scope: node.scope,
              node_type: node.node_type,
              gradable: node.gradable !== undefined? node.gradable : node.node_type === "proposal",
              grade: node.grade,
            }
            //   description: node.description,
            //   proponents: node.proponents,
            //   references: node.references,
            // },
            // type: 'custom-node',
          })),
          
          edges: fetched_edges.map(edge => {
            const edgeLabel = edge.edge_type.toString();
            console.log('received edge to import:', edge);
            let source = edgeLabel === "imply" ? edge.source.toString() : edge.target.toString();
            let target = edgeLabel === "imply" ? edge.target.toString() : edge.source.toString();

            return {
              id: `${edge.source}-${edge.target}`,  //note that this is using original source/target
              source: source,
              target: target,
              label: edgeLabel,
              markerEnd: edgeLabel === 'imply' ? "arrowclosed" : undefined,
              markerStart: edgeLabel === 'require' ? "arrowclosed" : undefined,
              data: {
                edge_type: edgeLabel,
                cprob: edge.cprob !== null ? edge.cprob * 100 : null,
                source: edge.source,  // original source
                target: edge.target,  // original target
                references: edge.references,
                // references: edge.references, not needed for graph viz
              },
            };
        })
        } || {};
        console.log('graphData', this.graphData);
      } catch (error) {
        console.error('Error fetching induced subgraph:', error);
      }
    },
    async updateNodeInfo(node_id) {
      //TODO: determine the best strategy here, fetch data or cache it all in the graphData
      try {
        const response = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/nodes/${node_id}`);
        this.node = response.data || undefined;
      }
      catch (error) {
        console.error('Error fetching element:', error);
        this.node = undefined;
      }

    },
    async updateEdgeInfo(source_id, target_id) {
      //TODO: determine the best strategy here, fetch data or cache it all in the graphData
      try {
        console.log('fetching edge with edges/ API', source_id, target_id);
        const response = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/edges/${source_id}/${target_id}`);
        this.edge = response.data || undefined;
      }
      catch (error) {
        console.error('Error fetching element:', error);
        this.edge = undefined;
      }

    },
  },
};
</script>

<style scoped>
.focus {
  display: flex;                    /* Use flexbox for horizontal layout */
  flex-grow: 1;                    /* Make the element detail take available space */
}

.element-info {
  width: 400px;                    /* Fixed width for element information */
  border: 1px solid #ccc;          /* Border around the element info */
  margin: 10px;                    /* Default margin */
  padding: 20px;                   /* Padding for content */
  font-size: 13px;;
}

.graph-renderer {
  flex-grow: 1;                    /* Use remaining space for graph renderer */
  border: 1px solid #ccc;          /* Border around graph */
  margin: 10px;                    /* Default margin */
}
</style>
