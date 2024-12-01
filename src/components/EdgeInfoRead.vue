<template>
    <div>
      <strong>Type:</strong> {{ edge.edge_type }}<br />
      <strong>Gradable:</strong> {{ edge.gradable === undefined ? false : edge.gradable }}<br />
      <strong>Proponents:</strong> {{ edge.proponents ? edge.proponents.join(', ') : '' }}<br />
      <strong>References:</strong><br />
      <ul class="references-list">
        <li v-for="reference in edge.references" :key="reference">
          {{ reference }}
        </li>
      </ul>
      <strong>Detailed Description:</strong><br />
      <p>{{ edge.description ? edge.description : '' }}</p>
    </div>
  </template>
  
  <script>
  export default {
    props: {
      edge: Object,
    },
  };
  </script>
  