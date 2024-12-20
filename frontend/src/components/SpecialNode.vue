<script setup>
import { Handle, Position, useVueFlow } from "@vue-flow/core";

defineProps({
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

// console.log('sourcePosition', sourcePosition)
</script>

<template>
  <Handle
    type="source"
    :position="sourcePosition"
    title="Connect to implications by dragging"
  />

  <span>{{ label }}</span>

  <Handle
    type="target"
    :position="targetPosition"
    title="Connect to conditions by dragging"
  />
</template>
