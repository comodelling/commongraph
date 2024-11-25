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
      element: {}, // Object to hold proposal data
      graphData: [], // Array to hold graph data
    };
  },
  computed: {
    elementId() {
      return this.$route.params.id; // Get proposal ID from route
    },
  },
  created() {
    this.fetchProposalData(); // Fetch the proposal data on creation
  },
  methods: {
    async fetchProposalData() {
      try {
        const response = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/nodes/${this.elementId}`);
        this.element = response.data;
        console.log('fetched node', this.element);
        // this.graphData = response.data.graphData;
        this.graphData = []
      } catch (error) {
        console.error('Error fetching proposal data:', error);
      }
    },
  },
};
</script>

<style scoped>
.focus {
  display: flex;                    /* Use flexbox for horizontal layout */
  flex-grow: 1;                    /* Make the proposal detail take available space */
}

.element-info {
  width: 400px;                    /* Fixed width for proposal information */
  border: 1px solid #ccc;          /* Border around the proposal info */
  margin: 10px;                    /* Default margin */
  padding: 20px;                   /* Padding for content */
}

.graph-renderer {
  flex-grow: 1;                    /* Use remaining space for graph renderer */
  border: 1px solid #ccc;          /* Border around graph */
  margin: 10px;                    /* Default margin */
}
</style>
