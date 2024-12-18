<template>
  <div>
    <strong>Title: </strong> "{{ node.title }}"<br />
    <strong>Type:</strong> {{ capitalise(node.node_type) }}<br />
    <strong>Scope: </strong> {{ node.scope }}<br />
    <strong>Status: </strong> {{ formatStatus(node.status) }}<br />
    <div class="tags-container" v-if="node.tags && node.tags.length">
      <strong>Tags: </strong>
      <span v-for="tag in node.tags" :key="tag" class="tag">{{ tag }}</span>
    </div>
    <strong>References: </strong> <br />
    <ul
      class="references-list"
      v-if="node.references && node.references.length"
    >
      <li v-for="reference in node.references" :key="reference">
        {{ reference.trim() || "(empty)" }}
      </li>
    </ul>
    <strong>Detailed description:</strong> <br />
    <p>{{ node.description ? node.description : "" }}</p>
  </div>
</template>
<script>
export default {
  props: {
    node: Object,
  },
  methods: {
    formatStatus(string) {
      if (string === "unspecified") {
        return "";
      }
      return this.capitalise(string);
    },
    capitalise(string) {
      return string.charAt(0).toUpperCase() + string.slice(1);
    },
  },
};
</script>

<style scoped>
.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.tag {
  background-color: #e0e0e0;
  border-radius: 3px;
  padding: 1px 3px;
  font-size: 12px;
  cursor: default;
  display: flex;
}
</style>
