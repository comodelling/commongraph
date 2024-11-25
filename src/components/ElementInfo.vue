<template>
  <div class="element-info">
    <h2> Element Information</h2>
    <div>
      <strong>title:  </strong>   "{{ element.title }}"<br />
      <!-- <strong>Node ID:</strong> {{ element.node_id }} -->
      <strong>scope:  </strong>   {{ element.scope }}<br />
      <strong>type:</strong>   {{ element.node_type }}<br />
      <strong>gradable:  </strong>   {{ element.gradable === undefined ? false : element.gradable}}<br />
      <strong>proponents:  </strong>   {{ element.proponents ? element.proponents.join(', ') : '' }}<br />
      <strong>references:  </strong><br />
        <ul class="references-list">
          <li v-for="reference in element.references" :key="reference">
            <!-- <a :href="reference">{{ reference }}</a> -->
            {{ reference }}
          </li>
        </ul>
      <strong>detailed description:</strong> <br />     
      <p>{{ element.description ? element.description : ''}}</p>
      <!-- <strong>Category:</strong> {{ element.category }} -->
      <!-- <strong>Created:</strong> {{ element.created_at }} -->
    </div>
  </div>
</template>

<script>
export default {
  props: {
    element: {
      type: Object,
      required: true,
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