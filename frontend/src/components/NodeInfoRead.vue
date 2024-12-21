<template>
  <div>
    <h2>{{ capitalise(node.node_type) }}</h2>
    <strong title="What is this node about?"> Title: </strong> "{{
      node.title
    }}"<br />
    <!-- <strong>Type:</strong> {{ capitalise(node.node_type) }}<br /> -->
    <strong title="Where/to whom does this node apply?">Scope: </strong>
    {{ node.scope }}<br />
    <strong title="Is this node currently live?">Status: </strong>
    {{ formatStatus(node.status) }}<br />
    <div class="tags-container" v-if="node.tags && node.tags.length">
      <strong title="Node tags">Tags: </strong>
      <span v-for="tag in node.tags" :key="tag" class="tag">{{ tag }}</span>
    </div>
    <strong title="A list of relevant references">References: </strong> <br />
    <ul
      class="references-list"
      v-if="node.references && node.references.length"
    >
      <li
        v-for="reference in node.references.filter((ref) => ref.trim())"
        :key="reference"
      >
        {{ reference.trim() }}
      </li>
    </ul>
    <strong title="A longer description of the node">Description:</strong>
    <br />
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
