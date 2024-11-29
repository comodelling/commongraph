<script setup>
import { nextTick, ref, watch } from 'vue'
import { Panel, VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { ControlButton, Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import Icon from './Icon.vue' // Update this line
import SpecialNode from '../components/SpecialNode.vue'
import { useLayout } from '../composables/useLayout'
// import SpecialEdge from './SpecialEdge.vue'

// props to receive nodes and edges data
const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
})

const { onInit, getNodes, getEdges, setNodes, setEdges, onConnect, addEdges, onNodeDragStop, setViewport, toObject, fitView } = useVueFlow()
const { layout } = useLayout()

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

async function layoutGraph(direction) {

  const currentNodes = getNodes.value
  const currentEdges = getEdges.value

  if (currentNodes.length === 0 || currentEdges.length === 0) {
    console.warn('Nodes or edges are empty, cannot layout graph')
    return
  }

  nodes.value = layout(currentNodes, currentEdges, direction)

  nextTick(() => {
    fitView()
  })
}

</script>

<template>
  <div class="graph-renderer">
    <VueFlow
      :nodes="nodes"
      :edges="edges"
      :default-viewport="{ zoom: 1.5 }"
      :min-zoom="0.2"
      :max-zoom="4">
    <template #node-special="specialNodeProps">
      <SpecialNode v-bind="specialNodeProps" />
    </template>

    <Background pattern-color="#aaa" :gap="16" />

    <MiniMap />

    <Panel class="process-panel" position="top-right">
        <div class="layout-panel">
          <button title="set horizontal layout" @click="layoutGraph('LR')">
            <Icon name="horizontal" />
            <span>Hor</span>
          </button>

          <button title="set vertical layout" @click="layoutGraph('TB')">
            <Icon name="vertical" />
            <span>Ver</span>
          </button>
        </div>
      </Panel>

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


.process-panel,
.layout-panel {
  display: flex;
  gap: 10px;
}

.process-panel {
  background-color: #2d3748;
  padding: 10px;
  border-radius: 8px;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
}

.process-panel button {
  border: none;
  cursor: pointer;
  background-color: #4a5568;
  border-radius: 8px;
  color: white;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
}

.process-panel button {
  font-size: 16px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.checkbox-panel {
  display: flex;
  align-items: center;
  gap: 10px;
}

.process-panel button:hover,
.layout-panel button:hover {
  background-color: #2563eb;
  transition: background-color 0.2s;
}

.process-panel label {
  color: white;
  font-size: 12px;
}

.stop-btn svg {
  display: none;
}

.stop-btn:hover svg {
  display: block;
}

.stop-btn:hover .spinner {
  display: none;
}

.spinner {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #2563eb;
  border-radius: 50%;
  width: 10px;
  height: 10px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

</style>