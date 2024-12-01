<template>
    <div>
      <strong>title:  </strong>   "{{ node.title }}"<br />
      <strong>scope:  </strong>   {{ node.scope }}<br />
      <strong>type:</strong>   {{ node.node_type }}"<br />
      <strong>gradable:  </strong>   {{ node.gradable === undefined ? false : node.gradable}}<br />
      <strong>proponents:  </strong>   {{ node.proponents ? node.proponents.join(', ') : '' }}<br />
      <strong>references:  </strong><br />
      <ul class="references-list">
        <li v-for="reference in node.references" :key="reference">
          {{ reference }}
        </li>
      </ul>
      <strong>detailed description:</strong> <br />     
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