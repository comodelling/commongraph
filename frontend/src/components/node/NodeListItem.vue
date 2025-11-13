<template>
  <div
    class="node-item"
    @mouseenter="$emit('hover', node.node_id)"
    @mouseleave="$emit('leave', node.node_id)"
  >
    <router-link :to="`/node/${node.node_id}`" class="title">
      ➜ {{ node.title }}
    </router-link>
    <div class="subtitle">
      {{ node.node_type }}
      <span v-if="node.last_modified"
        >— {{ formatDate(node.last_modified) }}</span
      >
      <span v-else>— no date</span>
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
  emits: ["hover", "leave"],
  methods: {
    formatDate(iso) {
      const d = new Date(iso);
      return d.toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
      // e.g. "Jun 21, 2025, 03:30 PM"
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
  /* color: var(--text-color); */
  text-decoration: none;
  color: #646cff;
}
.title:hover {
  text-decoration: underline;
  color: #535bf2;
}
.subtitle {
  font-size: 11px;
  color: var(--muted-text-color);
  margin-top: -3px;
}
</style>
