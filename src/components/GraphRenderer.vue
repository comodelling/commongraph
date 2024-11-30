<script setup>
import { nextTick, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
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

const emit = defineEmits(['nodeClick'])


const { onInit, 
  getNodes, 
  getEdges, 
  setNodes, 
  setEdges, 
  updateNode,
  onConnect, 
  addEdges, 
  onNodeDragStop, 
  setViewport, 
  toObject, 
  fitView,
  onNodeClick } = useVueFlow()
const { layout } = useLayout()

// refs for nodes and edges
const nodes = ref([])
const edges = ref([])
const dark = ref(false)
const router = useRouter()
const route = useRoute()



onInit((vueFlowInstance) => {
  // instance is the same as the return of `useVueFlow`
  vueFlowInstance.fitView()
  // set nodes and edges from props
  console.log('onInit', props.data.nodes, props.data.edges)
  setNodes(props.data.nodes || [])
  setEdges(props.data.edges || [])
  updateNode(route.params.id, { selected: true })
})


// watch for changes in props.data and update nodes and edges accordingly
watch(
  () => props.data,
  (newData) => {
    setNodes(newData.nodes || [])
    setEdges(newData.edges || [])
    updateNode(route.params.id, { selected: true })
  },
  { immediate: true }
)

/**
 * onConnect is called when a new connection is created.
 *
 * You can add additional properties to your new edge (like a type or label) or block the creation altogether by not calling `addEdges`
 */
 onConnect((connection) => {
  addEdges(connection)
})

onNodeClick(({ node }) => {
  console.log('Node Double Click', node.id)
  // window.location.href = `/focus/${node.node_id}`  full page reload
  router.push({ name: 'Focus', params: { id: node.id } })
  emit('nodeClick', node.id)
})


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
      :max-zoom="4"
      @nodes-initialized="layoutGraph('LR')"
    >  
    <template #node-special="specialNodeProps">
      <SpecialNode v-bind="specialNodeProps" />
    </template>

    <Background pattern-color="#aaa" :gap="16" />

    <MiniMap />

    <Panel class="compass-panel" position="top-right">
        <button class="compass-button bottom" title="Top-Bottom" @click="layoutGraph('TB')">
          <Icon name="vertical" />
        </button>
        <button class="compass-button left" title="Right-Left" @click="layoutGraph('RL')">
          <Icon name="horizontal" />
        </button>
        <button class="compass-button top" title="Bottom-Top" @click="layoutGraph('BT')">
          <Icon name="vertical" />
        </button>
        <button class="compass-button right" title="Left-Right" @click="layoutGraph('LR')">
          <Icon name="horizontal" />
        </button>
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

.compass-panel {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 100px;
  height: 100px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.compass-button {
  position: absolute;
  width: 30px;
  height: 30px;
  border: none;
  border-radius: 50%;
  background-color: #4a5568;
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
}

.compass-button.top {
  top: 0;
  left: 50%;
  transform: translateX(-50%);
}

.compass-button.right {
  right: 0;
  top: 50%;
  transform: translateY(-50%);
}

.compass-button.bottom {
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
}

.compass-button.left {
  left: 0;
  top: 50%;
  transform: translateY(-50%);
}

.compass-button:hover {
  background-color: #2563eb;
  transition: background-color 0.2s;
}

</style>