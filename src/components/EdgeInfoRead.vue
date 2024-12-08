<template>
  <div>
    <strong>Type:</strong> {{ localEdge.edge_type }}<br />
    <strong>
      <template v-if="localEdge.edge_type === 'require'">CProb(requirement) = {{ localEdge.cprob }}</template>
      <template v-else-if="localEdge.edge_type === 'imply'">CProb(implication) = {{ localEdge.cprob }}</template>
    </strong><br />
    <!-- <strong>Gradable:</strong> {{ localEdge.gradable === undefined ? false : localEdge.gradable }}<br /> -->
    <!-- <strong>Proponents:</strong> {{ localEdge.proponents ? localEdge.proponents.join(', ') : '' }}<br /> -->
    <strong>References:</strong><br />
    <ul class="references-list">
      <li v-for="reference in localEdge.references" :key="reference">
        {{ reference }}
      </li>
    </ul>
    <strong>Detailed description:</strong><br />
    <p>{{ localEdge.description ? localEdge.description : '' }}</p>
  </div>
</template>

  <script>
  export default {
    props: {
      edge: Object,
    },
    data() {
      return {
        localEdge: this.edge,
      };
    },
    watch: {
      edge: {
        handler(newEdge) {
          this.localEdge = newEdge;
        },
        deep: true,
      },
    },
  };
  </script>