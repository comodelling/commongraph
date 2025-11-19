<script setup>
import { Handle, Position, useVueFlow } from "@vue-flow/core";
import { computed, ref } from "vue";
import {
  getAllowedSourceNodeTypes,
  getAllowedTargetNodeTypes,
  isGraphSchemaLoaded,
} from "../../composables/useGraphSchema.js";

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

const showTooltip = ref(false);
const tooltipStyle = ref({});

const nodeType = computed(() => props.data?.node_type);
const schemaLoaded = computed(() => isGraphSchemaLoaded());

const canHaveChildren = computed(() => {
  if (!schemaLoaded.value) return true;
  if (!nodeType.value) return true;
  return getAllowedTargetNodeTypes(nodeType.value).length > 0;
});

const canHaveParents = computed(() => {
  if (!schemaLoaded.value) return true;
  if (!nodeType.value) return true;
  return getAllowedSourceNodeTypes(nodeType.value).length > 0;
});

// Tooltip title (node title)
const tooltipTitle = computed(() => {
  if (!props.data) return "";
  return props.data.title || props.label || "";
});

// Tooltip meta (status type (scope))
const tooltipMeta = computed(() => {
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

  let meta = parts.join(" ");

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
    meta += meta ? `\n${ratingLine}` : ratingLine;
  }

  return meta;
});

const handleMouseEnter = (event) => {
  const rect = event.target.getBoundingClientRect();
  tooltipStyle.value = {
    top: `${rect.top - 30}px`,
    left: `${rect.left + rect.width / 2 - 60}px`,
  };
  showTooltip.value = true;
};

const handleMouseLeave = () => {
  showTooltip.value = false;
};

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
    v-if="canHaveChildren"
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

  <span @mouseenter="handleMouseEnter" @mouseleave="handleMouseLeave">
    {{ label }}
  </span>

  <Teleport to="body">
    <div v-if="showTooltip" class="node-tooltip" :style="tooltipStyle">
      <div class="node-tooltip-title">{{ tooltipTitle }}</div>
      <div v-if="tooltipMeta" class="node-tooltip-meta">
        {{ tooltipMeta }}
      </div>
    </div>
  </Teleport>

  <Handle
    v-if="canHaveParents"
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
