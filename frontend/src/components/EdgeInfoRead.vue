<template>
  <div>
    <h2>{{ edge.edge_type === "require" ? "Condition" : "Implication" }}</h2>
    <!-- <strong>Type:</strong> {{ localEdge.edge_type }}<br /> -->

    <template v-if="localEdge.edge_type === 'require'">
      <strong>
        Cond.Proba(<a :href="`/node/${localEdge.target}`">condition</a>|<a
          :href="`/node/${localEdge.source}`"
          >source</a
        >)
      </strong>
      = {{ localEdge.cprob * 100 || "? " }}%<br />
    </template>
    <template v-if="localEdge.edge_type === 'imply'">
      <strong>
        Cond.Proba(<a :href="`/node/${localEdge.target}`">implication</a>|<a
          :href="`/node/${localEdge.source}`"
          >source</a
        >)
      </strong>
      = {{ localEdge.cprob * 100 || "? " }}%<br />
    </template>
    <strong>References: </strong> <br />
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
    <strong>Description:</strong><br />
    <p>{{ localEdge.description ? localEdge.description : "" }}</p>
  </div>
</template>

<script>
export default {
  props: {
    edge: Object,
  },
  data() {
    return {
      localEdge: this.edge,
    };
  },
  computed: {
    sourceLink() {
      return;
    },
    targetLink() {
      return `/nodes/${this.localEdge.target}`;
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
