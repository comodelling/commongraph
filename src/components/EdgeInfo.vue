<template>
    <div class="element-info">
      <h2> Edge Information</h2>
      <div v-if="edge">
        <strong>type:</strong>   {{ edge.edge_type }}<br />
        <strong>gradable:  </strong>   {{ edge.gradable === undefined ? false : edge.gradable}}<br />
        <strong>proponents:  </strong>   {{ edge.proponents ? edge.proponents.join(', ') : '' }}<br />
        <strong>references:  </strong><br />
          <ul class="references-list">
            <li v-for="reference in edge.references" :key="reference">
              {{ reference }}
            </li>
          </ul>
        <strong>detailed description:</strong> <br />     
        <p>{{ edge.description ? edge.description : ''}}</p>
      </div>
      <div v-else>
        <p>Edge not found</p>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    props: {
      edge: {
        type: Object,
        required: false,
        default: undefined,
      },
    },
  };
  </script>
  
  <style scoped>
  .references-list {
    margin: 0;
    padding-left: 20px;
    font-size: 0.9em;
  }
  
  .references-list li {
    margin: 2px 0;
  }
  </style>