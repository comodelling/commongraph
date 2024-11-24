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
      type: Array,
      required: true,
    },
  },
  mounted() {
    this.renderGraph();
  },
  methods: {
    renderGraph() {
      console.log('Data for graph:', this.data);
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