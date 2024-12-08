<template>
    <div>
      <strong>Title:  </strong>   "{{ node.title }}"<br />
      <strong>Scope:  </strong>   {{ node.scope }}<br />
      <strong>Type:</strong>   {{ node.node_type }}<br />
      <!-- <strong>gradable:  </strong>   {{ node.gradable === undefined ? false : node.gradable}}<br /> -->
      <!-- <strong>proponents:  </strong>   {{ node.proponents ? node.proponents.join(', ') : '' }}<br /> -->
      <strong>References:  </strong><br />
      <ul class="references-list">
        <li v-for="reference in node.references" :key="reference">
          {{ reference }}
        </li>
      </ul>
      <strong>Detailed description:</strong> <br />     
      <p>{{ node.description ? node.description : ''}}</p>
    </div>
  </template>
  
  <script>
  export default {
    props: {
      node: Object,
    },
  };
  </script>