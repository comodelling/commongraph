<template>
  <div>
    <h2 :title="edgeTypeTooltip">
      {{ edge.edge_type === "require" ? "Condition" : "Implication" }}
    </h2>
    <!-- <strong>Type:</strong> {{ localEdge.edge_type }}<br /> -->

    <template v-if="localEdge.edge_type === 'require'">
      <strong :title="tooltips.edge.cprob_condition">
        Cond.Proba(<a :href="`/node/${localEdge.target}`">condition</a>|<a
          :href="`/node/${localEdge.source}`"
          >source</a
        >)
      </strong>
      = {{ localEdge.cprob * 100 || "? " }}%<br />
    </template>
    <template v-if="localEdge.edge_type === 'imply'">
      <strong :title="tooltips.edge.cprob_implication">
        Cond.Proba(<a :href="`/node/${localEdge.target}`">implication</a>|<a
          :href="`/node/${localEdge.source}`"
          >source</a
        >)
      </strong>
      = {{ localEdge.cprob * 100 || "? " }}%<br />
    </template>
    <strong :title="tooltips.edge.references">References: </strong> <br />
    <ul
      class="references-list"
      v-if="localEdge.references && localEdge.references.length"
    >
      <li
        v-for="reference in localEdge.references.filter((ref) => ref.trim())"
        :key="reference"
      >
        {{ reference.trim() }}
      </li>
    </ul>
    <strong :title="tooltips.edge.description">Description:</strong><br />
    <p>{{ localEdge.description ? localEdge.description : "" }}</p>
  </div>
</template>

<script>
import tooltips from "../assets/tooltips.json"; // Add this line

export default {
  props: {
    edge: Object,
  },
  data() {
    return {
      localEdge: this.edge,
      tooltips, // Add this line
    };
  },
  computed: {
    sourceLink() {
      return;
    },
    targetLink() {
      return `/nodes/${this.localEdge.target}`;
    },
    edgeTypeTooltip() {
      return this.tooltips.edge[this.edge.edge_type] || this.tooltips.edge.type;
    },
  },
  watch: {
    edge: {
      handler(newEdge) {
        this.localEdge = newEdge;
      },
      deep: true,
    },
  },
};
</script>
