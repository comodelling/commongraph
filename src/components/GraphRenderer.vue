<script setup>
import { ref, watch } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { ControlButton, Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import Icon from './Icon.vue' // Update this line
import SpecialNode from '../components/SpecialNode.vue';
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

const dark = ref(false)



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



/**
 * onNodeDragStop is called when a node is done being dragged
 *
 * Node drag events provide you with:
 * 1. the event object
 * 2. the nodes array (if multiple nodes are dragged)
 * 3. the node that initiated the drag
 * 4. any intersections with other nodes
 */
 onNodeDragStop(({ event, nodes, node }) => {
  console.log('Node Drag Stop', { event, nodes, node })
})

/**
 * onConnect is called when a new connection is created.
 *
 * You can add additional properties to your new edge (like a type or label) or block the creation altogether by not calling `addEdges`
 */
onConnect((connection) => {
  addEdges(connection)
})

/**
 * To update a node or multiple nodes, you can
 * 1. Mutate the node objects *if* you're using `v-model`
 * 2. Use the `updateNode` method (from `useVueFlow`) to update the node(s)
 * 3. Create a new array of nodes and pass it to the `nodes` ref
 */
function updatePos() {
  //TODO: fix this

  console.log('Trying to ypdating Node Positions')
  console.log('Current Nodes:', nodes)
  const outValue =nodes.value.map((node) => {
    return {
      ...node,
      position: {
        x: Math.random() * 400,
        y: Math.random() * 400,
      },
    }
  })
  console.log('New Nodes:', outValue)
  setNodes(outValue)
}

/**
 * toObject transforms your current graph data to an easily persist-able object
 */
function logToObject() {
  console.log(toObject())
}

/**
 * Resets the current viewport transformation (zoom & pan)
 */
function resetTransform() {
  setViewport({ x: 0, y: 0, zoom: 1 })
}

function toggleDarkMode() {
  dark.value = !dark.value
}

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
    <template #node-special="specialNodeProps">
      <SpecialNode v-bind="specialNodeProps" />
    </template>

    <Background pattern-color="#aaa" :gap="16" />

    <MiniMap />

    <Controls position="top-right">
      <ControlButton title="Reset Transform" @click="resetTransform">
        <Icon name="reset" />
      </ControlButton>

      <ControlButton title="Shuffle Node Positions" @click="updatePos">
        <Icon name="update" />
      </ControlButton>

      <ControlButton title="Toggle Dark Mode" @click="toggleDarkMode">
        <Icon v-if="dark" name="sun" />
        <Icon v-else name="moon" />
      </ControlButton>

      <ControlButton title="Log `toObject`" @click="logToObject">
        <Icon name="log" />
      </ControlButton>
    </Controls>
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