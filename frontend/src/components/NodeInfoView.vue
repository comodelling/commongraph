<template>
  <div>
    <h2 :title="nodeTypeTooltip">{{ capitalise(node.node_type) }}</h2>
    <strong :title="tooltips.node.title"> Title: </strong> "{{
      node.title
    }}"<br />
    <strong :title="tooltips.node.scope">Scope: </strong>
    {{ node.scope }}<br />
    <strong :title="tooltips.node.status">Status: </strong>
    {{ formatStatus(node.status) }}<br />
    <div class="tags-container" v-if="node.tags && node.tags.length">
      <strong :title="tooltips.node.tags">Tags: </strong>
      <span v-for="tag in node.tags" :key="tag" class="tag">{{ tag }}</span>
    </div>
    <strong :title="tooltips.node.references">References: </strong> <br />
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
    <strong :title="tooltips.node.description">Description:</strong>
    <br />
    <p>{{ node.description ? node.description : "" }}</p>
    <strong :title="tooltips.node.support">Support: </strong>
    {{ node.support ? node.support + " (" + nodeSupportTooltip + ")" : ""
    }}<br />
  </div>
</template>

<script>
import tooltips from "../assets/tooltips.json";

export default {
  props: {
    node: Object,
  },
  data() {
    return {
      tooltips, // Add this line
    };
  },
  computed: {
    nodeTypeTooltip() {
      return this.tooltips.node[this.node.node_type] || this.tooltips.node.type;
    },
    nodeSupportTooltip() {
      return (
        this.tooltips.node[this.node.support] || this.tooltips.node.support
      );
    },
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
