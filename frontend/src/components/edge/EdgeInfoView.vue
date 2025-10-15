<template>
  <div class="edge-info-view">
    <!-- Type -->
    <div class="field-row">
      <strong :title="edgeTypeTooltip">Type:</strong>
      <span class="field-value">{{ edge.edge_type }}</span>
    </div>
    <!-- References -->
    <div class="field-row" v-if="isAllowed('references') && localEdge.references && localEdge.references.length">
      <strong :title="tooltips.edge.references">References:</strong>
      <div class="field-value">
        <ul class="references-list">
          <li v-for="reference in localEdge.references.filter((ref: any) => ref.trim())" :key="reference">
            {{ reference.trim() }}
          </li>
        </ul>
      </div>
    </div>
    <!-- Description -->
    <div class="field-row" v-if="isAllowed('description') && localEdge.description">
      <strong :title="tooltips.edge.description">Description:</strong>
      <span class="field-value">{{ localEdge.description }}</span>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, computed, onMounted } from "vue";
import { useConfig } from "../../composables/useConfig";
import tooltips from "../../assets/tooltips.json";

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
    const { edgeTypes, load } = useConfig();
    onMounted(load);

    const allowed = computed(() => {
      // Ensure edgeTypes are loaded and the edge has a type.
      if (!edgeTypes.value || !props.edge.edge_type) return Object.keys(props.edge);
      return edgeTypes.value[props.edge.edge_type].properties || Object.keys(props.edge);
    });

    function isAllowed(prop: string): boolean {
      return allowed.value.includes(prop);
    }

    const edgeTypeTooltip = computed(() => {
      return (tooltips.edge as any)[props.edge.edge_type] || tooltips.edge.type;
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

<style scoped>
.field-row {
  display: flex;
  align-items: flex-start;
  margin: 8px 0;
  gap: 10px;
}

.field-row strong {
  min-width: 80px;
  flex-shrink: 0;
}

.field-value {
  flex: 1;
}
</style>
