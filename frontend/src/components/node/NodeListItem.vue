<template>
  <div
    class="node-item"
    @mouseenter="$emit('hover', node.node_id)"
    @mouseleave="$emit('leave', node.node_id)"
  >
    <router-link
      :to="`/node/${node.node_id}`"
      class="title"
      :style="{ color: typeColor(node.node_type) || 'var(--text-color)' }"
    >
      ➜ {{ node.title }}
      <span
        class="node-type"
        :style="{ color: typeColor(node.node_type) || 'var(--text-color)' }"
      >
        ({{ node.node_type }})
      </span>
    </router-link>
    <div class="subtitle">
      <span class="meta">
        {{ node.scope || "—" }} — {{ node.status || "—" }} —
        <span v-if="node.last_modified">{{
          formatDate(node.last_modified)
        }}</span>
        <span v-else>no date</span>
      </span>
    </div>
  </div>
</template>

<script>
import { useConfig } from "../../composables/useConfig";

export default {
  name: "NodeListItem",
  props: {
    node: {
      type: Object,
      required: true,
    },
  },
  emits: ["hover", "leave"],
  setup() {
    const { nodeTypes } = useConfig();

    function typeColor(nodeType) {
      if (!nodeType) return null;
      const style = nodeTypes.value?.[nodeType]?.style || {};
      // support both camelCase and snake_case variants
      return style.borderColor || style.border_colour || null;
    }

    return { typeColor };
  },
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
.title .node-type {
  font-size: 12px;
  font-weight: 400;
  margin-left: 2px;
}
.subtitle .meta {
  color: var(--muted-text-color);
}
</style>
