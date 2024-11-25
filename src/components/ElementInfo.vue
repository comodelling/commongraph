<template>
  <div class="element-info">
    <h2> Element Information</h2>
    <div>
      <strong>title:</strong> {{ element.title }}<br />
      <!-- <strong>Node ID:</strong> {{ element.node_id }} -->
      <strong>scope:</strong> {{ element.scope }}<br />
      <strong>type:</strong> {{ element.node_type }}<br />
      <strong>gradable:</strong> {{ element.gradable }}<br />
      <strong>description:</strong> {{ element.description}}<br />     
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

<!-- <style scoped>
.element-info {
  width: 600px;
  padding: 20px;
  border: 1px solid #ccc;
}
</style> -->