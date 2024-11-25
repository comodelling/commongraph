<template>
  <div class="graph-renderer">
    <h2>Graph Visualization</h2>
    <div ref="graphContainer"></div>
  </div>
</template>

<script>
export default {
  props: {
    data: {
      type: Object,
      required: true,
    },
  },
  mounted() {
    this.renderGraph();
  },
  methods: {
    renderGraph() {
      const elementId = this.$route.params.id;  // central node id from route
      console.log('elementId', elementId, 'type', typeof elementId);

      console.log('Data for graph:', this.data.nodes, this.data.edges);
    },
  },
};
</script>

<!-- <style scoped>
.graph-renderer {
  flex: 1;
  padding: 20px;
  border: 1px solid #ccc;
}
</style> -->