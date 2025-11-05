<template>
  <g>
    <title>{{ hoverText }}</title>
    <BaseEdge :path="path[0]" :style="style" />
  </g>

  <EdgeLabelRenderer>
    <div
      :style="{
        pointerEvents: 'none',
        position: 'absolute',
        transform: `translate(-50%, -50%) translate(${path[1]}px,${path[2]}px)`,
        fontSize: '12px',
        opacity: 0.5,
      }"
      class="nodrag nopan"
    >
      <span v-if="data.cprob !== null && data.cprob !== undefined"
        >{{ data.cprob * 100 }}%</span
      >
    </div>
  </EdgeLabelRenderer>
</template>

<script setup>
import { BaseEdge, EdgeLabelRenderer, getBezierPath } from "@vue-flow/core";
import { computed } from "vue";

const props = defineProps({
  sourceX: Number,
  sourceY: Number,
  targetX: Number,
  targetY: Number,
  sourcePosition: String,
  targetPosition: String,
  sourceDimension: Object,
  targetDimension: Object,
  data: Object,
  id: String,
  sourceNode: Object,
  targetNode: Object,
  source: String,
  target: String,
  type: String,
  updatable: Boolean,
  selected: Boolean,
  animated: Boolean,
  label: String,
  labelStyle: Object,
  labelShowBg: Boolean,
  labelBgStyle: Object,
  labelBgPadding: Array,
  labelBgBorderRadius: Number,
  events: Object,
  style: Object,
  markerStart: String,
  markerEnd: String,
  sourceHandleId: String,
  targetHandleId: String,
  interactionWidth: Number,
});

const path = computed(() => getBezierPath(props));

const hoverText = computed(
  () => props.data.edge_type,
  // props.data.edge_type === "require" ? "Condition" : "Implication",
);
</script>

<!-- <script>
export default {
  name: "special",
  inheritAttrs: true,
};
</script> -->
