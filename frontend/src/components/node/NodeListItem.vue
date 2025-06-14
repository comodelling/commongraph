<template>
  <li class="node-item">
    <router-link :to="`/node/${node.node_id}`">
      {{ node.title }} <span v-if="node.scope"></span>
    </router-link>
  </li>
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
  cursor: pointer;
  margin-bottom: 5px;
  font-size: 12px;
}
</style>
