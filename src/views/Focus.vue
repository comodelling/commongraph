<template>
  <div class="focus">
      <ElementInfo :element="element" />
      <GraphRenderer :data="graphData" />
  </div>
</template>

<script>
import ElementInfo from '../components/ElementInfo.vue';
import GraphRenderer from '../components/GraphRenderer.vue';
import axios from 'axios';

export default {
  components: {
    ElementInfo,
    GraphRenderer,
  },
  data() {
    return {
      element: {}, // Object to hold element data
      graphData: {}, // Object to hold graph data
    };
  },
  computed: {
    elementId() {
      return this.$route.params.id; // Get element ID from route
    },
  },
  created() {
    this.fetchElementAndSubgraphData(); // Fetch the element data on creation
  },
  methods: {
    async fetchElementAndSubgraphData() {
      try {
        const response = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/subgraph/${this.elementId}`);
        const nodes = response.data.nodes;
        const edges = response.data.edges;
        console.log('fetching subgraph for elementId', this.elementId);
        this.element  = nodes.find(node => node.node_id === parseInt(this.elementId));  //TODO: maybe parse incoming data even before this
        console.log('fetched element', this.element);
        console.log('fetched induced subgraph', nodes, edges);
        this.graphData = {
          nodes: nodes.map(node => ({
            id: node.node_id.toString(),
            position: { x: Math.random() * 500, y: Math.random() * 500 }, // Random positions for example
            label: node.title,
            data: {
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
          edges: edges.map(edge => ({
            id: `e${edge.source}-${edge.target}`,
            source: edge.source.toString(),
            target: edge.target.toString(),
          }))
        };
        console.log('graphData', this.graphData);
      } catch (error) {
        console.error('Error fetching induced subgraph:', error);
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
