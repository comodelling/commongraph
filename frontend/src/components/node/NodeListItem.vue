<template>
  <div class="node-item">
    <router-link :to="`/node/${node.node_id}`" class="title">
      ➜ {{ node.title }}
    </router-link>
    <div class="subtitle">
      {{ node.node_type }}
    </div>
  </div>
</template>


<script>
export default {
  name: "NodeListItem",
  props: {
    node: {
      type: Object,
      required: true,
    },
  },
};
</script>

<style scoped>
.node-item {
  margin-bottom: 12px;
}
.title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color);
  text-decoration: none;
  color: blue
}
.title:hover {
  text-decoration: underline;
}
.subtitle {
  font-size: 11px;
  color: var(--muted-text-color);
  margin-top: -3px;
}
</style>