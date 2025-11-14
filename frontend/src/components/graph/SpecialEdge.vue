<template>
  <g>
    <title>{{ hoverText }}</title>
    <BaseEdge
      :path="path[0]"
      :style="style"
      @mouseenter="handleMouseEnter"
      @mouseleave="handleMouseLeave"
    />
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

  <Teleport to="body">
    <div v-if="showTooltip" class="edge-tooltip" :style="tooltipStyle">
      <div class="edge-tooltip-title">{{ edgeTooltipTitle }}</div>
      <div v-if="edgeTooltipMeta" class="edge-tooltip-meta">
        {{ edgeTooltipMeta }}
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { BaseEdge, EdgeLabelRenderer, getBezierPath } from "@vue-flow/core";
import { computed, ref } from "vue";

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

const showTooltip = ref(false);
const tooltipStyle = ref({});

const hoverText = computed(() => {
  const data = props.data || {};
  const baseLabel = data.edge_type || "Implication";
  const ratingLabel = data.ratingLabel;
  const ratingValue = data.causal_strength;

  if (!ratingLabel) {
    return baseLabel;
  }

  let formattedRating = "none";
  if (ratingValue != null) {
    formattedRating =
      typeof ratingValue === "number"
        ? Number(ratingValue).toFixed(2).replace(/\.00$/, "")
        : ratingValue;
  }

  return `${baseLabel}\nmedian ${ratingLabel}: ${formattedRating}`;
});

// Edge tooltip title (edge type)
const edgeTooltipTitle = computed(() => {
  if (!props.data) return "Edge";
  return props.data.edge_type || props.data.title || "Implication";
});

// Edge tooltip meta (source title -> target title and optional rating)
const edgeTooltipMeta = computed(() => {
  const sourceTitle =
    props.sourceNode?.data?.title || props.sourceNode?.label || "Source";
  const targetTitle =
    props.targetNode?.data?.title || props.targetNode?.label || "Target";

  let meta = `${sourceTitle} → ${targetTitle}`;

  const ratingLabel = props.data?.ratingLabel;
  const ratingValue = props.data?.causal_strength;

  if (ratingLabel) {
    let formattedRating = "none";
    if (ratingValue != null) {
      formattedRating =
        typeof ratingValue === "number"
          ? Number(ratingValue).toFixed(2).replace(/\.00$/, "")
          : ratingValue;
    }
    const ratingLine = `median ${ratingLabel}: ${formattedRating}`;
    meta += `\n${ratingLine}`;
  }

  return meta;
});

const handleMouseEnter = (event) => {
  // Calculate the middle point of the path
  const midX = props.sourceX + (props.targetX - props.sourceX) / 2;
  const midY = props.sourceY + (props.targetY - props.sourceY) / 2;

  tooltipStyle.value = {
    top: `${midY - 30}px`,
    left: `${midX - 60}px`,
  };
  showTooltip.value = true;
};

const handleMouseLeave = () => {
  showTooltip.value = false;
};
</script>

<!-- <script>
export default {
  name: "special",
  inheritAttrs: true,
};
</script> -->
