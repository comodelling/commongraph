<template>
  <div class="element-info">
    <h2> Node Information</h2>
    <div v-if="node">
      <strong>title:  </strong>   "{{ node.title }}"<br />
      <strong>scope:  </strong>   {{ node.scope }}<br />
      <strong>type:</strong>   {{ node.node_type }}<br />
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
    <div v-else>
      <p>Node not found</p>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    node: {
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