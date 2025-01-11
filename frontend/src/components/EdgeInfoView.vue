<template>
  <div>
    <h2 :title="edgeTypeTooltip">
      {{ edge.edge_type === "require" ? "Condition" : "Implication" }}
    </h2>
    <!-- <strong>Type:</strong> {{ localEdge.edge_type }}<br /> -->

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

  <strong :title="tooltips.edge.causal_strength_rating"> Causal Rating:</strong>
  {{
    localEdge.causal_strength_rating
      ? localEdge.causal_strength_rating + " (" + edgeCausalRatingTooltip + ")"
      : ""
  }}<br />
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
    edgeCausalRatingTooltip() {
      return (
        this.tooltips.edge[this.edge.causal_strength_rating] ||
        this.tooltips.edge.causal_strength_rating
      );
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
