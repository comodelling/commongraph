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
        console.log('elementId', this.elementId, 'type', typeof this.elementId);
        this.element  = nodes.find(node => node.node_id === parseInt(this.elementId));  //TODO: maybe parse incoming data even before this
        console.log('fetched element', this.element);
        console.log('fetched induced subgraph', nodes, edges);
        this.graphData = { "nodes": nodes, "edges": edges };
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
