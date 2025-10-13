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
  if (!props.data) return '';
  
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
  
  let tooltip = parts.join(' ');
  
  // Add description on a new line if it exists
  if (props.data.description) {
    const desc = props.data.description.length > 100 
      ? props.data.description.substring(0, 100) + '...' 
      : props.data.description;
    tooltip += tooltip ? `\n${desc}` : desc;
  }
  
  return tooltip;
});

// console.log('sourcePosition', sourcePosition)
</script>

<template>
  <Handle
    type="source"
    :position="sourcePosition"
    title="Create implications"
  />

  <span :title="tooltipContent">{{ label }}</span>

  <Handle
    type="target"
    :position="targetPosition"
    title="Create conditions"
  />
</template>
