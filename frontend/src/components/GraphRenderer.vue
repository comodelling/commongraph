<script setup>
import axios from 'axios';
import { saveAs } from 'file-saver'
import { nextTick, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Panel, VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { ControlButton, Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import Icon from './Icon.vue' // Update this line
// import SpecialNode from '../components/SpecialNode.vue'
import { useLayout } from '../composables/useLayout'
import VueSimpleContextMenu from 'vue-simple-context-menu';
import 'vue-simple-context-menu/dist/vue-simple-context-menu.css';
// import { create } from 'axios';
// import SpecialEdge from './SpecialEdge.vue'


const { onInit,
  getNodes,
  getEdges,
  addNodes,
  addEdges,
  findNode,
  findEdge,
  setNodes,
  setEdges,
  updateNodeData,
  applyNodeChanges,
  applyEdgeChanges,
  removeEdges,
  updateEdge,
  updateEdgeData,
  // onConnect,
  // onConnectStart,
  // onConnectEnd,
  onNodeDragStop,
  setViewport,
  zoomTo,
  toObject,
  fitView,
  onNodeClick,
  onEdgeClick,
  // onNodeContextMenu,
  // onSelectionContextMenu,
 } = useVueFlow()


// props to receive nodes and edges data
const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
})

const router = useRouter()
const route = useRoute()
const emit = defineEmits(['nodeClick', 'edgeClick', 'newNodeCreated', 'newEdgeCreated'])



const { layout, layoutSingleton, previousDirection } = useLayout()

// refs for nodes and edges
const nodes = ref([])
const edges = ref([])
const connectionInfo = ref(null)
const dark = ref(false)
const contextMenuOptions = ref([]);
const contextMenuRef = ref(null);

 function updateGraphFromData(data) {
  setNodes(data.nodes || []);
  setEdges(data.edges || []);

  if (route.params.source_id && route.params.target_id) {
    const edgeId = `${route.params.source_id}-${route.params.target_id}`;
    console.log('selecting edgeId', edgeId);
    const edge = findEdge(edgeId);
    if (edge) {
      edge.selected = true;
    }
  } else {
    updateNodeData(route.params.id, { selected: true });
  }
}

onInit((vueFlowInstance) => {
  // instance is the same as the return of `useVueFlow`
  // vueFlowInstance.fitView()
  // set nodes and edges from props
  console.log('initiating graph from props')
  updateGraphFromData(props.data)
  // fitView()
  })


// watch for changes in props.data and update nodes and edges accordingly
watch(
  () => props.data,
  (newData) => {
    console.log('updating graph data following props change', newData)
    updateGraphFromData(newData)
    // fitView()
  },
  { immediate: true }
)

onNodeClick(({ node }) => {
  console.log('Node Click', node.id)
  // get current selection from route.params
  // route.params.id

  // is current node id same as clicked node id?
  // if (id === node.id) {
  //   // if yes, do nothing
  //   return
  // }

  // is the current element selected?
  // yes --> extend the selection and uri to the clicked node

  // no --> switch to the clicked node as sole selected element

  router.push({ name: 'NodeView', params: { id: node.id } })
  emit('nodeClick', node.id)
  // window.location.href = `/node/${node.node_id}`  full page reload
})

onEdgeClick(({ edge }) => {
  console.log('Edge Click', edge.source, edge.target)

  // window.location.href = `/edge/${node.node_id}`  full page reload
  router.push({ name: 'EdgeView', params: { source_id: edge.data.source, target_id: edge.data.target } })  // uri follows backend convention
  emit('edgeClick', edge.data.source, edge.data.target)  // emit event to parent component
})


const onNodesChange = async (changes) => {
  const nextChanges = []
  // console.log('Changes to perform (onNodesChange):', changes)
  for (let change of changes) {
    if (change.type === 'remove') {
      const isConfirmed = await confirm('Are you sure you want to delete this node and all its connections?')

      if (isConfirmed) {
        nextChanges.push(change)
        // console.log("change:", change)
        const node_id = change.id
        try {
          const response = await axios.delete(`${import.meta.env.VITE_BACKEND_URL}/nodes/${node_id}`);
          // console.log('Deleted node from backend returned:', response.data);
        } catch (error) {
          console.error('Failed to delete node:', error);
        }

        //find all edges connected to this node and delete them
        // note: edges on teh backend have already been deleted by the above call
        const connectedEdges = getEdges.value.filter(edge => edge.source === node_id || edge.target === node_id)

        for (const edge of connectedEdges) {
          removeEdges([edge.id])
        }
      }
    } else {
      // console.log('other change:', change)
      nextChanges.push(change)
    }
  }

  applyNodeChanges(nextChanges)
}

const onEdgesChange = async (changes) => {
  const nextChanges = []
  // console.log('Changes to perform (onEdgesChange):', changes)
  const { source_id, target_id } = route.params
  const is_edge_selected = source_id && target_id

  for (const change of changes) {
    if (change.type === 'remove' && (change.rightClick || is_edge_selected)) {
      const isConfirmed = await confirm('Are you sure you want to delete this edge?')

      if (isConfirmed) {
        nextChanges.push(change)
        // console.log("change:", change)
        const edge = findEdge(change.id)
        const source_id = edge.data.source
        const target_id = edge.data.target
        const edge_type = edge.data.edge_type
        try {
          const response = await axios.delete(`${import.meta.env.VITE_BACKEND_URL}/edges/${source_id}/${target_id}`,
            { 'edge_type': edge_type });
          // console.log('Deleted edge returned:', response.data);
        } catch (error) {
          console.error('Failed to delete edge:', error);
        }
      }
    } else {
      // console.log('other change:', change)
      nextChanges.push(change)
    }
  }

  applyEdgeChanges(nextChanges)
}

/**
 * onConnect is called when a new connection is created.
 *
 * You can add additional properties to your new edge (like a type or label) or block the creation altogether by not calling `addEdges`
 */
function onConnect(connection) {
  console.log('on connect', connection);
  addEdges(connection);
}

function onConnectStart({ nodeId, handleType }) {
  console.log('on connect start', { nodeId, handleType })
  connectionInfo.value = { nodeId, handleType }
}

function onConnectEnd(event) {
  console.log('on connect end', event);

  if (!connectionInfo.value) {
    console.error('No connection info available');
    return;
  }

  // Check if the connection is to an existing node handle
  const targetElement = event.target;
  const isConnectedToHandle = (targetElement && targetElement.classList.contains('vue-flow__handle'));
  let targetId = null;
  // let newNodeData = null;

  if  (isConnectedToHandle) {
    console.log('Connected to an existing node handle');
    targetId = targetElement.getAttribute('data-nodeid');
    const newEdgeData = createEdgeOnConnection(targetId);
    nextTick(() => {
      emit('newEdgeCreated', newEdgeData);
    });
    connectionInfo.value = null;
  }
  else {
    console.log('Connected to an empty space');
    const newNodeData = createNodeOnConnection(event);
    createEdgeOnConnection('temp-node');
    // console.log('opening search for new node');
    // searchBarPosition.value = { x: event.clientX, y: event.clientY };
    // showSearchBar.value = true;
    // connectionInfo.value = { nodeId, handleType };
    nextTick(() => {
      emit('newNodeCreated', newNodeData);
    });
    connectionInfo.value = null;
  }
}

function createEdgeOnConnection(targetId){
  const { nodeId, handleType } = connectionInfo.value;
  const newEdgeData = {
      id: `temp-edge`,
      source: handleType === 'source' ? nodeId : targetId,
      target: handleType === 'source' ? targetId : nodeId,
      // type: handleType === 'source' ? 'sourceType' : 'targetType',
      label: handleType === 'source' ? 'imply' : 'require',
      data: {
        edge_type: handleType === 'source' ? 'imply' : 'require',
        source: parseInt(nodeId),
        target: parseInt(targetId),
      }
    };
  addEdges(newEdgeData);
  return newEdgeData;
}


function createNodeOnConnection(event) {
  console.log('Connected to a new node');
  const { nodeId, handleType } = connectionInfo.value;
  const sourceNode = findNode(nodeId);

  const newNodeData = {
    id: `temp-node`,
    position: { x: event.clientX, y: event.clientY },
    label: 'New Node',
    data: {
      title: 'New Node',
      scope: sourceNode.data.scope,  // inherited scope
      node_type: 'potentiality',  // most general type
      satus: 'draft',
      tags: sourceNode.data.tags, // inherited tags
      fromConnection: {'id': nodeId, 'edge_type': handleType === 'source' ? 'imply' : 'require'} // to be used to update edge data
    },
  };
  addNodes(newNodeData);
  return newNodeData;
}



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

  console.log('Trying to update Node Positions')
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

  if (currentNodes.length === 1) {
    // console.warn('Nodes or edges are empty, cannot layout graph')
    nodes.value = layoutSingleton(currentNodes, direction)
    nextTick(() => {
      fitView()
      zoomTo(1.5)
    })
    return
  }
  else if (currentNodes.length === 0 || currentEdges.length === 0) {
    console.warn('Nodes or edges are empty, cannot layout graph')
    return
  }
  nodes.value = layout(currentNodes, currentEdges, direction)

  nextTick(() => {
    fitView()
  })
}

function exportGraph() {
  const nodes = getNodes.value.map(node => ({
    ...node.data
  }));

  const edges = getEdges.value.map(edge => ({
    ...edge.data
  }));

  const graphData = { nodes, edges };
  console.log('Exporting graph data:', graphData);
  const blob = new Blob([JSON.stringify(graphData, null, 2)], { type: 'application/json' });
  // console.log('Blob:', blob);
  saveAs(blob, 'export.json');
}


// ********* CONTEXT MENUS *********
// onNodeContextMenu((event, node) => {
//   showContextMenu(event, [
//     { label: 'Edit Node', action: () => editNode(node) },
//     { label: 'Delete Node', action: () => deleteNode(node) },
//   ]);
// })

function showContextMenu(event, options) {
  console.log('event location', event.clientX, event.clientY);
  console.log('options', options);
  event.preventDefault();
  contextMenuOptions.value = options;
  // event.clientX = event.clientX - 100;
  // event.clientX = event.clientX - 100;
  let newEvent = new MouseEvent('contextmenu', {
    bubbles: true,
    cancelable: true,
    clientX: event.clientX -640,
    clientY: event.clientY -50,
  });
  contextMenuRef.value.showMenu(newEvent);
}

function onNodeRightClick({ event, node }) {
  console.log('Node Right Click', node);
  showContextMenu(event, [
    { name: 'Edit Node', action: () => editNode(node) },
    { name: 'Delete Node', action: () => deleteNode(node) },
  ]);
}

function onEdgeRightClick({ event, edge }) {
  console.log('Edge Right Click', edge);
  showContextMenu(event, [
    { name: 'Edit Edge', action: () => editEdge(edge) },
    { name: 'Delete Edge', action: () => deleteEdge(edge) },
  ]);
}


function onSelectionRightClick({ event, selection }) {
  showContextMenu(event, [
    { name: 'Group Selection', action: () => groupSelection(selection) },
    { name: 'Delete Selection', action: () => deleteSelection(selection) },
  ]);
}

function onConnectEndEmpty(event) {
  showContextMenu(event, [
    { name: 'Create New Node', action: () => createNode(event) },

  ]);
}

function editNode(node) {
  console.log('Edit Node', node);
  router.push({ name: 'NodeEdit', params: { id: node.id } });
  // console.log(`Navigated to /node/${node.id}/edit`);
}

function deleteNode(node) {
  console.log('Delete Node', node);
  onNodesChange([{ type: 'remove', id: node.id}]);
}

function editEdge(edge) {
  console.log('Edit Edge', edge);
  router.push({ name: 'EdgeEdit', params: { source_id: edge.data.source , target_id: edge.data.target} });
  // console.log(`Navigated to /edge/${edge.source}/${edge.target}/edit`);
}

async function deleteEdge(edge) {
  console.log('Delete Edge', edge);
  onEdgesChange([{ type: 'remove', id: edge.id, rightClick: true}]);
  //TODO: merge with onEdgesChange
  // const isConfirmed = await confirm('Are you sure you want to delete this edge?')

  // if (isConfirmed) {
  //   // console.log("change:", change)
  //   const source_id = edge.data.source
  //   const target_id = edge.data.target
  //   const edge_type = edge.data.edge_type
  //   try {
  //     const response = await axios.delete(`${import.meta.env.VITE_BACKEND_URL}/edges/${source_id}/${target_id}`,
  //       { 'edge_type': edge_type });
  //     // console.log('Deleted edge returned:', response.data);
  //   } catch (error) {
  //     console.error('Failed to delete edge:', error);
  //   }
  // }
}

function groupSelection(selection) {
  console.log('Group Selection', selection);
}

function deleteSelection(selection) {
  console.log('Delete Selection', selection);
}

function optionClicked({ option }) {
  console.log('Option Clicked', option);
  option.action();
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
      :apply-default="false"
      @nodes-initialized="layoutGraph(previousDirection)"
      @nodes-change="onNodesChange"
      @edges-change="onEdgesChange"
      @connect="onConnect"
      @connect-start="onConnectStart"
      @connect-end="onConnectEnd"
      @node-context-menu="onNodeRightClick"
      @edge-context-menu="onEdgeRightClick"
      @selection-context-menu="onSelectionRightClick"
    >

    <!-- <div class="item-wrapper">
      <div
        v-for="item in items"
        @click.prevent.stop="handleClick($event, item)"
        class="item-wrapper__item"
      >
        {{item.name}}
      </div>
    </div> -->
    <!-- <template #node-special="specialNodeProps"> -->
      <!-- <SpecialNode v-bind="specialNodeProps" /> -->
    <!-- </template> -->

    <!-- <div class="list-group">
      <div
        v-for="(item, index) in itemArray1"
        :key="index"
        @contextmenu.prevent.stop="handleClick1($event, item)"
        class="list-group-item list-group-item-action"
      >
        {{ item.name }}
      </div>
    </div>
     -->
    <!-- <vue-simple-context-menu
      element-id="myFirstMenu"
      :options="optionsArray1"
      ref="vueSimpleContextMenu1"
      @option-clicked="optionClicked1"
    >
  </vue-simple-context-menu> -->


    <vue-simple-context-menu
        element-id="myUniqueId"
        :options="contextMenuOptions"
        ref="contextMenuRef"
        @option-clicked="optionClicked"
      />


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

      <ControlButton title="Export Graph" @click="exportGraph">
        <Icon name="export" />
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
    handleClick1(event, item) {
      this.$refs.vueSimpleContextMenu1.showMenu(event, item);
    },
  },

};
</script>




<style>

.graph-renderer {
  flex-grow: 1;
  border: 1px solid #ccc;
  margin: 5px;
  /* cursor: pointer!important; */
}
/* .graph-renderer .vue-flow__node,
.graph-renderer .vue-flow__edge {
  cursor: move!important;
}
.graph-renderer .vue-flow__pane {
  /* cursor: crosshair!important;
} */

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

/* Add this to your CSS file */
/* .vue-simple-context-menu {
  position: absolute;
  z-index: 1000;
}

.vue-simple-context-menu__item {
  padding: 8px 12px;
  cursor: pointer;
}

.vue-simple-context-menu__item:hover {
  background-color: #f0f0f0;
} */
</style>
