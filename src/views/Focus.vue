<template>
  <div class="focus">
      <ElementInfo :element="element" />
      <GraphRenderer :data="graphData" />
  </div>
</template>

<script>
import ElementInfo from '../components/ElementInfo.vue';
import GraphRenderer from '../components/GraphRenderer.vue';

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
    fetchProposalData() {
      // This would typically involve an API call to fetch proposal data
      const sampleData = {
        title: 'Sample Proposal',
        description: 'This is a sample proposal description.',
        creator: 'User A',
        date: '2023-01-01',
      };

      const sampleGraphData = []; // Replace this with actual graph data

      // Set the fetched data
      this.element = sampleData;
      this.graphData = sampleGraphData; // Set the appropriate data structure for the graph
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
