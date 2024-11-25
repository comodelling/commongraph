<script setup>
import { ref, watch } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
// import { Background } from '@vue-flow/background'
// import { ControlButton, Controls } from '@vue-flow/controls'
// import { MiniMap } from '@vue-flow/minimap'

// import SpecialNode from './SpecialNode.vue'
// import SpecialEdge from './SpecialEdge.vue'

// props to receive nodes and edges data
const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
})

const { onInit, setNodes, setEdges, onNodeDragStop, onConnect, addEdges, setViewport, toObject } = useVueFlow()

// refs for nodes and edges
const nodes = ref([])
const edges = ref([])




onInit((vueFlowInstance) => {
  // instance is the same as the return of `useVueFlow`
  vueFlowInstance.fitView()
  // set nodes and edges from props
  console.log('onInit', props.data.nodes, props.data.edges)
  setNodes(props.data.nodes || [])
  setEdges(props.data.edges || [])
})


// watch for changes in props.data and update nodes and edges accordingly
watch(
  () => props.data,
  (newData) => {
    setNodes(newData.nodes || [])
    setEdges(newData.edges || [])
  },
  { immediate: true }
)

</script>

<template>
  <div class="graph-renderer">
    <VueFlow
      :nodes="nodes"
      :edges="edges"
      :default-viewport="{ zoom: 1.5 }"
      :min-zoom="0.2"
      :max-zoom="4"
    >
    </VueFlow>
  </div>
</template>

<script>
export default {
  props: {
    data: {
      type: Object,
      required: true,
    },
  },
  mounted() {
    this.renderGraph();
  },
  methods: {
    renderGraph() {
      const elementId = this.$route.params.id;  // central node id from route
      console.log('elementId', elementId, 'type', typeof elementId);

      console.log('Data for graph:', this.data.nodes, this.data.edges);
    },
  },
};
</script>




<style>
/* import the necessary styles for Vue Flow to work */
@import '@vue-flow/core/dist/style.css';

/* import the default theme, this is optional but generally recommended */
@import '@vue-flow/core/dist/theme-default.css';

</style>