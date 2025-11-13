<script setup>
import { Handle, Position, useVueFlow } from "@vue-flow/core";
import { computed } from "vue";

const props = defineProps({
  id: String,
  sourcePosition: String,
  targetPosition: String,
  data: Object,
  type: String,
  events: Object,
  selected: Boolean,
  resizing: Boolean,
  dragging: Boolean,
  connectable: Boolean,
  position: Object,
  dimensions: Object,
  isValidTargetPos: Boolean,
  isValidSourcePos: Boolean,
  parent: Object,
  parentNodeId: String,
  zIndex: Number,
  label: String,
  dragHandle: String,
});

defineEmits(["updateNodeInternals"]);

// Create tooltip content from node data
const tooltipContent = computed(() => {
  if (!props.data) return "";

  const parts = [];

  // Format as: status type (scope)
  if (props.data.status) {
    parts.push(props.data.status);
  }

  if (props.data.node_type) {
    parts.push(props.data.node_type);
  }

  if (props.data.scope) {
    parts.push(`(${props.data.scope})`);
  }

  let tooltip = parts.join(" ");

  // Add description on a new line if it exists
  // if (props.data.description) {
  //   const desc =
  //     props.data.description.length > 100
  //       ? props.data.description.substring(0, 100) + "..."
  //       : props.data.description;
  //   tooltip += tooltip ? `\n${desc}` : desc;
  // }

  const ratingLabel = props.data.ratingLabel;
  const ratingValue = props.data.support;
  if (ratingLabel) {
    let formattedRating = "none";
    if (ratingValue != null) {
      formattedRating =
        typeof ratingValue === "number"
          ? Number(ratingValue).toFixed(2).replace(/\.00$/, "")
          : ratingValue;
    }
    const ratingLine = `median ${ratingLabel}: ${formattedRating}`;
    tooltip += tooltip ? `\n${ratingLine}` : ratingLine;
  }

  return tooltip;
});

// All triangles point in the same causal direction based on source position
const triangleRotation = computed(() => {
  switch (props.sourcePosition) {
    case "right":
      return "0deg";
    case "bottom":
      return "90deg";
    case "left":
      return "180deg";
    case "top":
      return "270deg";
    default:
      return "0deg";
  }
});
</script>

<template>
  <Handle
    type="source"
    :position="sourcePosition"
    title="Create implications"
    class="triangle-handle source-handle"
  >
    <div
      class="triangle-arrow"
      :style="{ transform: `rotate(${triangleRotation})` }"
    ></div>
  </Handle>

  <span :title="tooltipContent">{{ label }}</span>

  <Handle
    type="target"
    :position="targetPosition"
    title="Create conditions"
    class="triangle-handle target-handle"
  >
    <div
      class="triangle-arrow"
      :style="{ transform: `rotate(${triangleRotation})` }"
    ></div>
  </Handle>
</template>

<style scoped>
/* Override the default circle handle but keep it interactive */
.triangle-handle {
  background: transparent !important;
  border: none !important;
  width: 14px !important;
  height: 14px !important;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: crosshair !important;
  /* Ensure the handle itself is clickable/draggable */
  pointer-events: auto !important;
}

/* Create a CSS triangle that points right by default */
.triangle-arrow {
  width: 0;
  height: 0;
  border-top: 12px solid transparent;
  border-bottom: 12px solid transparent;
  border-left: 18px solid var(--border-color);
  transform-origin: center;
  transition: all 0.2s ease;
  /* Triangle should not block pointer events - let them pass through to the handle */
  pointer-events: none;
}

/* Make triangle larger and darker on hover */
.triangle-handle:hover .triangle-arrow {
  border-top-width: 13px;
  border-bottom-width: 13px;
  border-left-width: 19px;
  border-left-color: var(--text-color);
}

/* Dark mode support - already uses CSS variables */
</style>
