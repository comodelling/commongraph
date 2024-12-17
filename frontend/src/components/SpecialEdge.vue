<script setup>
import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  MarkerType,
} from "@vue-flow/core";
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

const newMarkerEnd = computed(() => {
  if (props.data.edge_type === "imply") {
    return {
      type: MarkerType.ArrowClosed,
      color: "#ff0072",
      width: 20,
      height: 20,
    };
  }
  return undefined;
});

const newMarkerStart = computed(() => {
  if (props.data.edge_type === "require") {
    return {
      type: MarkerType.ArrowClosed,
      color: "#ff0072",
      width: 20,
      height: 20,
    };
  }
  return undefined;
});
</script>

<script>
export default {
  name: "special",
  inheritAttrs: true,
};
</script>

<template>
  <!-- You can use the `BaseEdge` component to create your own custom edge more easily -->
  <BaseEdge
    :path="path[0]"
    :marker-end="markerEnd"
    :marker-start="markerStart"
  />

  <!-- Use the `EdgeLabelRenderer` to escape the SVG world of edges and render your own custom label in a `<div>` ctx -->
  <EdgeLabelRenderer>
    <div
      :style="{
        pointerEvents: 'all',
        position: 'absolute',
        transform: `translate(-50%, -50%) translate(${path[1]}px,${path[2]}px)`,
        fontSize: '12px',
        opacity: 0.5,
      }"
      class="nodrag nopan"
    >
      <span v-if="data.cprob !== null">{{ data.cprob * 100 }}%</span>
    </div>
  </EdgeLabelRenderer>
</template>
