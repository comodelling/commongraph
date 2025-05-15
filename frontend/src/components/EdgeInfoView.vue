<template>
  <div>
    <h2 :title="edgeTypeTooltip">
      {{ edge.edge_type }}
    </h2>
    <strong v-if="isAllowed('references')" :title="tooltips.edge.references">References:</strong>
    <br>
    <ul class="references-list" v-if="localEdge.references && localEdge.references.length">
      <li v-for="reference in localEdge.references.filter((ref) => ref.trim())" :key="reference">
        {{ reference.trim() }}
      </li>
    </ul>
    <strong v-if="isAllowed('description')" :title="tooltips.edge.description">Description:</strong>
    <br>
    <p>{{ localEdge.description ? localEdge.description : "" }}</p>
  </div>
</template>

<script lang="ts">
import { defineComponent, computed, onMounted } from "vue";
import { useMetaConfig } from "../composables/useConfig";
import tooltips from "../assets/tooltips.json";

export default defineComponent({
  name: "EdgeInfoView",
  props: {
    edge: {
      type: Object,
      required: true,
    },
    sourceId: Number,
    targetId: Number,
  },
  emits: ["publish-edge"],
  setup(props) {
    const { edgeTypes, load } = useMetaConfig();
    onMounted(load);

    const allowed = computed(() => {
      // Ensure edgeTypes are loaded and the edge has a type.
      if (!edgeTypes.value || !props.edge.edge_type) return Object.keys(props.edge);
      return edgeTypes.value[props.edge.edge_type] || Object.keys(props.edge);
    });

    function isAllowed(prop: string): boolean {
      return allowed.value.includes(prop);
    }

    const edgeTypeTooltip = computed(() => {
      return tooltips.edge[props.edge.edge_type] || tooltips.edge.type;
    });

    return { isAllowed, edgeTypeTooltip };
  },
  data() {
    return {
      // localEdge is used so that modifications from watchers are applied.
      localEdge: this.edge,
      tooltips,
    };
  },
  computed: {
    sourceLink(): string {
      return ""; // your implementation here
    },
    targetLink(): string {
      return `/node/${this.localEdge.target}`;
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
});
</script>
