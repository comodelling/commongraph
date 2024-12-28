<script setup>
import axios from "axios";
import { saveAs } from "file-saver";
import { nextTick, ref, warn, watch, computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { Panel, VueFlow, useVueFlow } from "@vue-flow/core";
import { Background } from "@vue-flow/background";
import { ControlButton, Controls } from "@vue-flow/controls";
import { MiniMap } from "@vue-flow/minimap";
import Icon from "./Icon.vue";
import { useLayout } from "../composables/useLayout";
import VueSimpleContextMenu from "vue-simple-context-menu";
import "vue-simple-context-menu/dist/vue-simple-context-menu.css";
import SearchBar from "./SearchBar.vue"; // Import the SearchBar component
import SpecialNode from "../components/SpecialNode.vue";
import SpecialEdge from "./SpecialEdge.vue";
import {
  formatFlowEdgeProps,
  formatFlowNodeProps,
} from "../composables/formatFlowComponents";

const {
  onInit,
  getNodes,
  getEdges,
  addNodes,
  addEdges,
  findNode,
  findEdge,
  setNodes,
  setEdges,
  updateNode,
  updateNodeData,
  applyNodeChanges,
  applyEdgeChanges,
  removeEdges,
  onNodeDragStart,
  onNodeDragStop,
  zoomTo,
  fitView,
  onNodeClick,
  onEdgeClick,
  onPaneClick,
  onEdgeMouseEnter,
  onEdgeMouseLeave,
  screenToFlowCoordinate,
} = useVueFlow();

// props to receive nodes and edges data
const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
  updatedNode: Object,
  updatedEdge: Object,
});

const router = useRouter();
const route = useRoute();
const emit = defineEmits([
  "nodeClick",
  "edgeClick",
  "newNodeCreated",
  "newEdgeCreated",
]);

const { layout, affectDirection, previousDirection } = useLayout();

// refs for nodes and edges
const nodes = ref([]);
const edges = ref([]);
const connectionInfo = ref(null);
const dark = ref(false);
const contextMenuOptions = ref([]);
const contextMenuRef = ref(null);
const showSearchBar = ref(false);
const searchBarPosition = ref({ x: 0, y: 0 });
const searchResults = ref(null);
const selectedDirection = ref(previousDirection.value || null);

const currentNodeIds = computed(() => {
  return new Set(nodes.value.map((node) => node.id));
});

onInit((vueFlowInstance) => {
  // instance is the same as the return of `useVueFlow`
  // vueFlowInstance.fitView()
  // set nodes and edges from props
  // console.log("initiating subnet viz");
  // updateSubnetFromData(props.data);
  // fitView()
  console.log("VueFlow instance initialised");
  console.log("onInit, selected direction", selectedDirection.value);
});

// watch for changes in props.data and update nodes and edges accordingly
watch(
  () => props.data,
  (newData) => {
    console.log("updating subnet data following props change");
    updateSubnetFromData(newData);
    setTimeout(() => {
      layoutSubnet(selectedDirection.value);
    }, 16); // leave time for nodes to initialise (size)
  },
  { immediate: false },
);

watch(
  () => props.updatedNode,
  (newUpdatedNode) => {
    if (newUpdatedNode) {
      console.log("new updated node detected:", newUpdatedNode);
      // console.log("old updated node is:", oldUpdatedNode);
      let formattedNode = formatFlowNodeProps(newUpdatedNode);
      // case of a new node (with possibly new connection too)
      if (newUpdatedNode.new) {
        console.log("Replacing temporary new node with a proper node");
        const node = findNode("new");
        if (node) {
          formattedNode = {
            ...node,
            ...formattedNode,
            id: formattedNode.id,
            selected: true,
            position: node.position,
          };
          const edge = getEdges.value.find(
            (edge) => edge.target === "new" || edge.source === "new",
          );
          updateNode(node.id, formattedNode);
          if (edge) {
            console.log("Updating edge target to new node");
            if (edge.target === "new") {
              edge.target = formattedNode.id;
              edge.id = `${edge.source}-${formattedNode.id}`;
              edge.selected = false;
              edge.data.target = formattedNode.id;
            } else if (edge.source === "new") {
              edge.source = formattedNode.id;
              edge.id = `${formattedNode.id}-${edge.target}`;
              edge.data.target = formattedNode.id;
            }
          } else {
            console.log("No edge found for new node", getEdges.value);
          }
        }
      }
      // case of an existing node to update
      else if (newUpdatedNode.node_id !== "new") {
        console.log("updating existing node with id", newUpdatedNode.node_id);
        const node = findNode(formattedNode.id);
        if (node) {
          formattedNode = {
            ...node,
            ...formattedNode,
            selected: true,
            position: node.position,
          };
          updateNode(node.id, formattedNode);
        } else warn("Node not found in subnet", formattedNode);
      }
    }
  },
  { immediate: true },
);

watch(
  () => props.updatedEdge,
  (newUpdatedEdge) => {
    console.log("Edge update detected:", newUpdatedEdge);
    if (newUpdatedEdge) {
      let updatedEdge = formatFlowEdgeProps(newUpdatedEdge);
      let edge = findEdge(updatedEdge.id);
      console.log("found edge", edge);
      if (edge) {
        Object.assign(edge, updatedEdge); // Update each field from updatedEdge
        edge.selected = true;
      }
      // console.log('updatedNode', updatedNode)
      // edge = updatedEdge;
    }
  },
  { immediate: true },
);

function updateSubnetFromData(data) {
  console.log("Updating subnet from data:", data);
  setNodes(data.nodes || []);
  setEdges(data.edges || []);

  if (route.params.source_id && route.params.target_id) {
    const edgeId = `${route.params.source_id}-${route.params.target_id}`;
    const edge = findEdge(edgeId);
    if (edge) {
      edge.selected = true;
    }
  } else {
    updateNodeData(route.params.id, { selected: true });
  }
}

function selectDirection(direction, layout = false) {
  selectedDirection.value = direction;
  if (layout) {
    layoutSubnet(direction);
  } else {
    nodes.value = affectDirection(getNodes.value, direction);
  }
}

async function layoutSubnet(direction) {
  console.log("layouting subnet with", direction);
  const currentNodes = getNodes.value;
  const currentEdges = getEdges.value;

  if (currentNodes.length === 1) {
    nodes.value = affectDirection(currentNodes, direction);
    nextTick(() => {
      fitView();
      zoomTo(1.5);
    });
    return;
  } else if (currentNodes.length === 0 || currentEdges.length === 0) {
    console.warn("Nodes or edges are empty, cannot layout subnet");
    return;
  }
  nodes.value = layout(currentNodes, currentEdges, direction);

  nextTick(() => {
    fitView();
  });
}

function exportSubnet() {
  const nodes = getNodes.value.map((node) => ({
    ...node.data,
  }));

  const edges = getEdges.value.map((edge) => ({
    ...edge.data,
  }));

  const subnetData = { nodes, edges };
  console.log("Exporting subnet data:", subnetData);
  const blob = new Blob([JSON.stringify(subnetData, null, 2)], {
    type: "application/json",
  });
  saveAs(blob, "export.json");
}

onNodeClick(({ node }) => {
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

  router.push({ name: "NodeView", params: { id: node.id } });
  emit("nodeClick", node.id);
  // window.location.href = `/node/${node.node_id}`  full page reload
  closeSearchBar();
});

onEdgeClick(({ edge }) => {
  router.push({
    name: "EdgeView",
    params: { source_id: edge.data.source, target_id: edge.data.target },
  }); // uri follows backend convention
  emit("edgeClick", edge.data.source, edge.data.target); // emit event to parent component
  closeSearchBar();
});

onPaneClick(({ event }) => {
  console.log("Pane Click", event);
  closeSearchBar();
});

const onNodesChange = async (changes) => {
  // console.log("Nodes change", changes);
  const nextChanges = [];
  for (let change of changes) {
    if (change.type === "remove") {
      const isConfirmed = await confirm(
        "Are you sure you want to delete this node and all its connections?",
      );

      if (isConfirmed) {
        nextChanges.push(change);
        const node_id = change.id;
        try {
          const response = await axios.delete(
            `${import.meta.env.VITE_BACKEND_URL}/nodes/${node_id}`,
          );
        } catch (error) {
          console.error("Failed to delete node:", error);
        }

        // find all edges connected to this node and delete them
        // note: edges on the backend have already been deleted by the above call
        const connectedEdges = getEdges.value.filter(
          (edge) => edge.source === node_id || edge.target === node_id,
        );

        for (const edge of connectedEdges) {
          removeEdges([edge.id]);
        }
      }
    } else {
      nextChanges.push(change);
    }
  }

  applyNodeChanges(nextChanges);
};

const onEdgesChange = async (changes) => {
  const nextChanges = [];
  const { source_id, target_id } = route.params;
  const is_edge_selected = source_id && target_id;

  for (const change of changes) {
    if (change.type === "remove" && (change.rightClick || is_edge_selected)) {
      const isConfirmed = await confirm(
        "Are you sure you want to delete this edge?",
      );

      if (isConfirmed) {
        nextChanges.push(change);
        const edge = findEdge(change.id);
        const source_id = edge.data.source;
        const target_id = edge.data.target;
        const edge_type = edge.data.edge_type;
        try {
          const response = await axios.delete(
            `${import.meta.env.VITE_BACKEND_URL}/edges/${source_id}/${target_id}`,
            { edge_type: edge_type },
          );
        } catch (error) {
          console.error("Failed to delete edge:", error);
        }
      }
    } else {
      nextChanges.push(change);
    }
  }

  applyEdgeChanges(nextChanges);
};

/**
 * onConnect is called when a new connection is created.
 *
 * You can add additional properties to your new edge (like a type or label) or block the creation altogether by not calling `addEdges`
 */
function onConnect(connection) {
  console.log("on connect", connection);
  addEdges(connection);
}

function onConnectStart({ nodeId, handleType }) {
  console.log("on connect start", { nodeId, handleType });
  connectionInfo.value = { nodeId, handleType };
}

function onConnectEnd(event) {
  console.log("on connect end", event);

  if (!connectionInfo.value) {
    console.error("No connection info available");
    return;
  }

  // Check if the connection is to an existing node handle
  const targetElement = event.target;
  const isConnectedToHandle =
    targetElement && targetElement.classList.contains("vue-flow__handle");
  let targetId = null;
  const { nodeId, handleType } = connectionInfo.value;

  if (isConnectedToHandle) {
    console.log("Connected to an existing node handle");
    targetId = targetElement.getAttribute("data-nodeid");
    const newEdgeData = createEdgeOnConnection(targetId);
    nextTick(() => {
      emit("newEdgeCreated", newEdgeData);
    });
    addEdges(newEdgeData);
    connectionInfo.value = null;
  } else {
    console.log("Connected to an empty space");
    connectionInfo.value = { nodeId, handleType };
    searchBarPosition.value = determinePositionWithinWindow(event);
    setTimeout(() => {
      showSearchBar.value = true;
    }, 10);
  }
}

function determinePositionWithinWindow(event) {
  const { innerWidth, innerHeight } = window;
  const offsetX = 370; // offset from the edges
  const offsetY = 200;
  let x = event.layerX;
  let y = event.layerY;

  if (event.clientX + offsetX > innerWidth) {
    x = x + innerWidth - event.clientX - offsetX;
  }
  if (event.clientY + offsetY > innerHeight) {
    y = y + innerHeight - event.clientY - offsetY;
  }

  return { x: x, y: y };
}

// direct connection between existing handles
function createEdgeOnConnection(targetId) {
  const { nodeId, handleType } = connectionInfo.value;
  const newEdgeData = formatFlowEdgeProps({
    source: parseInt(nodeId),
    target: targetId, // targetId is a string
    edge_type: handleType === "source" ? "imply" : "require",
  });
  console.log("New edge data (direct connection):", newEdgeData);
  return newEdgeData;
}

function handleSearch(query) {
  // Perform search and update searchResults
  console.log("Searching for:", query);
  if (!query.trim()) {
    searchResults.value = null;
    console.log("Empty query, not searching");
    return;
  }
  try {
    axios
      .get(`${import.meta.env.VITE_BACKEND_URL}/nodes/`, {
        params: { title: query },
      })
      .then((response) => {
        console.log("Search results:", response.data);
        searchResults.value = response.data;
      })
      .catch((error) => {
        console.error("Failed to search nodes:", error);
      });
  } catch (error) {
    console.error("Failed to search nodes:", error);
  }
}

function createNodeAndEdge(event = null) {
  console.log("Creating a new node");

  let scope = "";
  let tags = [];
  let fromConnection = null;

  if (connectionInfo.value) {
    console.log("connectionInfo value detected, creating an edge too");
    const { nodeId, handleType } = connectionInfo.value;
    const sourceNode = findNode(nodeId);
    scope = sourceNode.data.scope; // inherited scope
    tags = sourceNode.data.tags; // inherited tags
    fromConnection = {
      id: nodeId,
      edge_type: handleType === "source" ? "imply" : "require",
    }; // to be used to update edge data
  } else {
    console.log("No connectionInfo available");
  }
  const newNodeData = formatFlowNodeProps({
    node_id: `new`,
    title: "New Node",
    status: "draft",
    position: screenToFlowCoordinate({ x: event.clientX, y: event.clientY }),
    scope: scope,
    node_type: "potentiality", // most general type
    tags: tags,
    fromConnection: fromConnection,
  });
  addNodes(newNodeData);

  if (connectionInfo.value) {
    const newEdgeData = createEdgeOnConnection("new");
    addEdges(newEdgeData);
  }

  nextTick(() => {
    emit("newNodeCreated", newNodeData);
  });
  connectionInfo.value = null;
  closeSearchBar();
}

function handleSearchResultClick(id, event) {
  console.log("search result clicked", id);

  //TODO: if id not present in current subnet, fetch node from backend and add it to viz here (question, with its induced subnet or not? )

  // if connected from existing node, create edge
  if (connectionInfo.value) linkSourceToSearchResult(id);
}

function linkSourceToSearchResult(id) {
  console.log("Linking source to search result id:", id);
  const newEdgeData = createEdgeOnConnection(id);
  console.log("New edge data (towards search result):", newEdgeData);
  if (findNode(id)) {
    console.log("Node already exists, adding edge first");
    addEdges(newEdgeData);
    nextTick(() => {
      emit("newEdgeCreated", newEdgeData);
    });
  } else {
    nextTick(() => {
      emit("newEdgeCreated", newEdgeData);
    });
    addEdges(newEdgeData);
  }

  closeSearchBar();
}

function closeSearchBar() {
  showSearchBar.value = false;
  searchResults.value = null;
}

onNodeDragStart(({ event, node }) => {
  // console.log("Node Drag Start", { event, nodes, node });
});

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
  // console.log("Node Drag Stop", { event, nodes, node });
});

/**
 * To update a node or multiple nodes, you can
 * 1. Mutate the node objects *if* you're using `v-model`
 * 2. Use the `updateNode` method (from `useVueFlow`) to update the node(s)
 * 3. Create a new array of nodes and pass it to the `nodes` ref
 */
function updatePos() {
  console.log("Updaing Node Positions");
  const outValue = nodes.value.map((node) => {
    return {
      ...node,
      position: {
        x: Math.random() * 400,
        y: Math.random() * 400,
      },
    };
  });
  setNodes(outValue);
}

function toggleDarkMode() {
  dark.value = !dark.value;
}

// ********* CONTEXT MENUS *********

function showContextMenu(event, options) {
  console.log("event location", event.clientX, event.clientY);
  console.log("options", options);
  event.preventDefault();
  contextMenuOptions.value = options;
  let newEvent = new MouseEvent("contextmenu", {
    bubbles: true,
    cancelable: true,
    clientX: event.clientX - 640,
    clientY: event.clientY - 50,
  });
  contextMenuRef.value.showMenu(newEvent);
}

function onNodeRightClick({ event, node }) {
  console.log("Node Right Click", node);
  showContextMenu(event, [
    { name: "Edit Node", action: () => editNode(node) },
    { name: "Delete Node", action: () => deleteNode(node) },
  ]);
}

function onEdgeRightClick({ event, edge }) {
  console.log("Edge Right Click", edge);
  showContextMenu(event, [
    { name: "Edit Edge", action: () => editEdge(edge) },
    { name: "Delete Edge", action: () => deleteEdge(edge) },
  ]);
}

function onSelectionRightClick({ event, selection }) {
  showContextMenu(event, [
    { name: "Group Selection", action: () => groupSelection(selection) },
    { name: "Delete Selection", action: () => deleteSelection(selection) },
  ]);
}

function onPaneRightClick(event) {
  event.preventDefault();
  console.log("Pane Right Click", event);

  searchBarPosition.value = determinePositionWithinWindow(event);
  setTimeout(() => {
    showSearchBar.value = true;
  }, 10);
}

function onConnectEndEmpty(event) {
  showContextMenu(event, [
    { name: "Create New Node", action: () => createNode(event) },
  ]);
}

function editNode(node) {
  console.log("Edit Node", node);
  router.push({ name: "NodeEdit", params: { id: node.id } });
}

function deleteNode(node) {
  console.log("Delete Node", node);
  onNodesChange([{ type: "remove", id: node.id }]);
}

function editEdge(edge) {
  console.log("Edit Edge", edge);
  router.push({
    name: "EdgeEdit",
    params: { source_id: edge.data.source, target_id: edge.data.target },
  });
}

async function deleteEdge(edge) {
  console.log("Delete Edge", edge);
  onEdgesChange([{ type: "remove", id: edge.id, rightClick: true }]);
}

function groupSelection(selection) {
  console.log("Group Selection", selection);
}

function deleteSelection(selection) {
  console.log("Delete Selection", selection);
}

function optionClicked({ option }) {
  console.log("Option Clicked", option);
  option.action();
}

onEdgeMouseEnter(({ edge }) => {
  // edge.style = {
  //   strokeWidth: edge.style.strokeWidth ? edge.style.strokeWidth * 2 : 1,
  // };
});

onEdgeMouseLeave(({ edge }) => {
  // edge.style = {
  //   strokeWidth: edge.style.strokeWidth / 2,
  // };
});
</script>

<template>
  <div class="subnet-renderer">
    <VueFlow
      :nodes="nodes"
      :edges="edges"
      :default-viewport="{ zoom: 1.5 }"
      :min-zoom="0.2"
      :max-zoom="4"
      :apply-default="false"
      @nodes-initialized="selectDirection(selectedDirection)"
      @nodes-change="onNodesChange"
      @edges-change="onEdgesChange"
      @connect="onConnect"
      @connect-start="onConnectStart"
      @connect-end="onConnectEnd"
      @node-context-menu="onNodeRightClick"
      @edge-context-menu="onEdgeRightClick"
      @selection-context-menu="onSelectionRightClick"
      @pane-context-menu="onPaneRightClick"
    >
      <template #edge-special="props">
        <SpecialEdge v-bind="props" />
      </template>

      <template #node-special="props">
        <SpecialNode v-bind="props" />
      </template>

      <vue-simple-context-menu
        element-id="myUniqueId"
        :options="contextMenuOptions"
        ref="contextMenuRef"
        @option-clicked="optionClicked"
      />

      <div
        v-if="showSearchBar"
        class="search-bar-container"
        :style="{
          position: 'absolute',
          top: searchBarPosition.y + 'px',
          left: searchBarPosition.x + 'px',
        }"
      >
        <button class="close-button" @click="closeSearchBar">✖</button>
        <button
          @click="createNodeAndEdge"
          style="
            padding: 5px;
            margin-top: 6px;
            border-radius: 2px;
            margin-top: 2px;
            margin-bottom: 3px;
            width: 100%;
            text-align: left;
            font-size: 14px;
          "
        >
          Create New Node
        </button>

        <SearchBar
          @search="handleSearch"
          :placeholder="'Or search for existing nodes...'"
          :show-button="false"
          style="width: 104%"
        />
        <ul
          v-if="searchResults && searchResults.length"
          style="font-size: 10px"
        >
          <li
            v-for="result in searchResults"
            :key="result.node_id"
            @click="handleSearchResultClick(result.node_id.toString(), $event)"
            :class="{
              highlight: currentNodeIds.has(result.node_id.toString()),
            }"
            :title="
              connectionInfo
                ? 'Connect to node ' + result.node_id
                : 'Fetching unnconnected nodes is not yet supported'
            "
          >
            <span style="margin-right: 5px">➔</span>{{ result.title }}
          </li>
        </ul>
        <p
          v-else-if="searchResults && !searchResults.length"
          style="font-size: 10px"
        >
          No results found
        </p>
      </div>

      <Background pattern-color="#aaa" :gap="16" />

      <MiniMap />

      <Panel class="compass-panel" position="top-right">
        <div class="compass-container">
          <button
            class="compass-button top"
            :class="{ selected: selectedDirection === 'BT' }"
            title="Upward causality"
            @click="selectDirection('BT', true)"
          >
            <Icon name="arrow-up" />
          </button>
          <button
            class="compass-button left"
            :class="{ selected: selectedDirection === 'RL' }"
            title="Leftward causality"
            @click="selectDirection('RL', true)"
          >
            <Icon name="arrow-left" />
          </button>
          <button
            class="compass-button bottom"
            :class="{ selected: selectedDirection === 'TB' }"
            title="Downward causality"
            @click="selectDirection('TB', true)"
          >
            <Icon name="arrow-down" />
          </button>
          <button
            class="compass-button right"
            :class="{ selected: selectedDirection === 'LR' }"
            title="Rightward causality"
            @click="selectDirection('LR', true)"
          >
            <Icon name="arrow-right" />
          </button>
        </div>
      </Panel>

      <Controls
        position="top-right"
        style="margin-top: 72px; margin-right: 20px"
      >
        <ControlButton title="Export subnet as JSON" @click="exportSubnet">
          <Icon name="export" />
        </ControlButton>
      </Controls>
    </VueFlow>
  </div>
</template>

<style>
.subnet-renderer {
  flex-grow: 1;
  border: 1px solid #ccc;
  margin: 5px;
}

.search-bar-container {
  position: absolute;
  background: white;
  border: 1px solid #ccc;
  border-radius: 5px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  padding: 5px;
  z-index: 1000;
  max-width: 250px;
  min-width: 50px;
  max-height: 300px;
  overflow-y: auto;
  overflow: hidden;
}

.search-bar-container ul {
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: 11px;
  max-height: 150px;
  overflow-y: auto;
}

.search-bar-container li {
  padding: 8px;
  cursor: pointer;
}

.search-bar-container li:hover {
  background-color: #f0f0f0;
}

.search-bar-container .highlight {
  background-color: #ffff99; /* Highlight color */
}

.search-bar-container .close-button {
  position: absolute;
  top: 0px;
  right: 3px;
  padding: 0;
  background: transparent;
  border: none;
  font-size: 10px;
  cursor: pointer;
}

.process-panel,
.layout-panel {
  display: flex;
  gap: 10px;
}

.compass-panel {
  /* margin: 20px; */
  padding: 0px;
}

.compass-container {
  display: grid;
  grid-template-areas:
    ". top ."
    "left . right"
    ". bottom .";
  gap: 0px; /* Adjusted gap between buttons */
  justify-items: center;
  align-items: center;
}

.compass-button {
  width: 19px; /* Slightly bigger than the icons */
  height: 19px;
  /* display: flex; */
  justify-content: center;
  align-items: center;
  background: white;
  border: 1px solid #ccc; /* Ensure buttons are visible */
  padding: 0;
  line-height: 0px; /* Center the icon vertically */
  text-align: center; /* Center the icon horizontally */
  border-radius: 15%; /* Make the button round */
  opacity: 0.8; /* Slightly transparent */
}

.compass-button.top {
  /* margin-top: -5px; */
  margin-top: -10px;
  grid-area: top;
}

.compass-button.left {
  grid-area: left;
}

.compass-button.bottom {
  grid-area: bottom;
}

.compass-button.right {
  grid-area: right;

  margin-right: -10px; /* Wider margin to the right */
}

.compass-button.selected {
  background-color: #007bff; /* Change to your preferred color */
  color: white;
}

.compass-button svg {
  width: 10px; /* Icon size */
  height: 10px;
}
</style>
