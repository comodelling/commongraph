<script setup>
import api from "../../api/axios.js";
import { useAuth } from "../../composables/useAuth.js";
import { saveAs } from "file-saver";
import { nextTick, ref, warn, watch, computed, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { Panel, VueFlow, useVueFlow, ConnectionMode } from "@vue-flow/core";
import { Background } from "@vue-flow/background";
import { ControlButton, Controls } from "@vue-flow/controls";
// import { MiniMap } from "@vue-flow/minimap";
import Icon from "../common/Icon.vue";
import { useLayout } from "../../composables/useLayout.js";
import VueSimpleContextMenu from "vue-simple-context-menu";
import "vue-simple-context-menu/dist/vue-simple-context-menu.css";
import SearchBar from "../common/SearchBar.vue";
import { parseSearchQuery, buildSearchParams } from "../../utils/searchParser.js";
import SpecialNode from "./SpecialNode.vue";
import SpecialEdge from "./SpecialEdge.vue";
import {
  formatFlowEdgeProps,
  formatFlowNodeProps,
} from "../../composables/formatFlowComponents.js";
import { useUnsaved } from "../../composables/useUnsaved.js";
import { useConfig } from "../../composables/useConfig.js";
import { loadGraphSchema, getAllowedEdgeTypes, getAllowedTargetNodeTypes, getAllowedSourceNodeTypes } from "../../composables/useGraphSchema.js";

const {
  nodeTypes,
  edgeTypes,
  defaultNodeType,
  defaultEdgeType,
  load: loadConfig,
  canCreate,
  canEdit,
  canDelete,
  canRate
} = useConfig()

onMounted(async () => {
  await loadConfig()
  await loadGraphSchema()
})

const { getAccessToken } = useAuth();

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
  // console.log("initiating subgraph viz");
  // updateSubgraphFromData(props.data);
  // fitView()
  console.log("VueFlow instance initialised");
  console.log("onInit, selected direction", selectedDirection.value);
});

// watch for changes in props.data and update nodes and edges accordingly
watch(
  () => props.data,
  (newData) => {
    console.log("updating subgraph data following props change");
    updateSubgraphFromData(newData);
    setTimeout(() => {
      layoutSubgraph(selectedDirection.value);
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
          delete formattedNode.new;
          const edge = getEdges.value.find(
            (edge) => edge.target === "new" || edge.source === "new",
          );
          updateNode(node.id, formattedNode);
          if (edge) {
            console.log(
              "Found an edge containing (the) new node. Edge: ",
              edge,
            );
            if (edge.target === "new") {
              console.log("Updating edge target to new node");
              edge.target = formattedNode.id;
              edge.id = `${edge.source}-${formattedNode.id}`;
              edge.selected = false;
              edge.data.source = parseInt(edge.source);
              edge.data.target = parseInt(formattedNode.id);
            } else if (edge.source === "new") {
              console.log("Updating edge source to new node");
              edge.source = formattedNode.id;
              edge.id = `${formattedNode.id}-${edge.target}`;
              edge.data.source = parseInt(formattedNode.id);
              edge.data.target = parseInt(edge.target);
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
        } else warn("Node not found in subgraph", formattedNode);
      }
    }
  },
  { immediate: true },
);

watch(
  () => props.updatedEdge,
  (newUpdatedEdge) => {
    console.log("Edge update detected:", newUpdatedEdge);
    if (!newUpdatedEdge) return;

    // Keep the existing causal_strength if missing from the updated edge
    const oldEdge = getEdges.value.find(
      (e) => e.id === `${newUpdatedEdge.source}-${newUpdatedEdge.target}`,
    );
    if (oldEdge?.data?.causal_strength && !newUpdatedEdge.causal_strength) {
      newUpdatedEdge.causal_strength = oldEdge.data.causal_strength;
    }

    const formattedEdge = formatFlowEdgeProps(newUpdatedEdge);
    setEdges((prevEdges) =>
      prevEdges.map((e) => (e.id === formattedEdge.id ? formattedEdge : e)),
    );
  },
  { immediate: true },
);

function updateSubgraphFromData(data) {
  console.log("Updating subgraph from data:", data);
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
    layoutSubgraph(direction);
  } else {
    nodes.value = affectDirection(getNodes.value, direction);
  }
}

async function layoutSubgraph(direction) {
  console.log("layouting subgraph with", direction);
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
    console.warn("Nodes or edges are empty, cannot layout subgraph");
    return;
  }
  nodes.value = layout(currentNodes, currentEdges, direction);

  nextTick(() => {
    fitView();
  });
}

function exportSubgraph() {
  if (!getNodes.value.length) {
    console.warn("No nodes to export");
    return;
  }

  if (route.name === "NodeEdit" || route.name === "EdgeEdit") {
    const confirmExport = confirm(
      "Exporting while editing may lose unsaved changes. Export anyway?",
    );
    if (!confirmExport) {
      return;
    }
  }
  const nodes = getNodes.value.map((node) => ({
    ...node.data,
  }));

  let edges = getEdges.value.map((edge) => ({
    ...edge.data,
  }));
  edges = edges.filter((edge) => edge.source && edge.target);

  const subgraphData = { nodes, edges };
  console.log("Exporting subgraph data:", subgraphData);
  const blob = new Blob([JSON.stringify(subgraphData, null, 2)], {
    type: "application/json",
  });
  const currentDate = new Date();
  const formattedDate = `${currentDate.getFullYear()}${(
    currentDate.getMonth() + 1
  )
    .toString()
    .padStart(
      2,
      "0",
    )}${currentDate.getDate().toString().padStart(2, "0")}-${currentDate
    .getHours()
    .toString()
    .padStart(
      2,
      "0",
    )}${currentDate.getMinutes().toString().padStart(2, "0")}${currentDate.getSeconds().toString().padStart(2, "0")}`;
  saveAs(blob, `commongraph-export-${formattedDate}.json`);
}

onNodeClick(({ node }) => {
  // if the node is already selected, do nothing
  const currentNode = findNode(route.params.id);
  if (currentNode && currentNode.id === node.id) {
    return;
  }
  const { hasUnsavedChanges, setUnsaved } = useUnsaved();
  if (hasUnsavedChanges.value) {
    if (!window.confirm("You have unsaved edits. Leave without saving?")) {
      // prevent clicked node from being selected
      updateNode(node.id, { ...node, selected: false });
      // make sure the current element remains selected
      if (currentNode) {
        updateNode(currentNode.id, { ...currentNode, selected: true });
      } else {
        // find edge
        const edge = findEdge(
          `${route.params.source_id}-${route.params.target_id}`,
        );
        if (edge) {
          edge.selected = true;
        }
      }

      return;
    }
    setUnsaved(false);
  }
  router.push({ name: "NodeView", params: { id: node.id } });
  emit("nodeClick", node.id);
  closeSearchBar();
});

onEdgeClick(({ edge }) => {
  const currentEdge = findEdge(
    `${route.params.source_id}-${route.params.target_id}`,
  );
  if (currentEdge && currentEdge.id === edge.id) {
    return;
  }
  const { hasUnsavedChanges, setUnsaved } = useUnsaved();
  if (hasUnsavedChanges.value) {
    if (!window.confirm("You have unsaved edits. Leave without saving?")) {
      // prevent clicked edge from being selected
      edge.selected = false;
      const currentNode = findNode(route.params.id);
      if (currentNode) {
        updateNode(currentNode.id, { ...currentNode, selected: true });
      } else {
        // find edge
        const edge = findEdge(
          `${route.params.source_id}-${route.params.target_id}`,
        );
        if (edge) {
          edge.selected = true;
        }
      }
      return;
    }
    setUnsaved(false);
  }
  router.push({
    name: "EdgeView",
    params: { source_id: edge.data.source, target_id: edge.data.target },
  });
  emit("edgeClick", edge.data.source, edge.data.target);
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
        const node_id = change.id;
        const token = getAccessToken();
        try {
          const response = await api.delete(
            `/nodes/${node_id}`,
            token ? { headers: { Authorization: `Bearer ${token}` } } : {},
          );
          
          // Only proceed with UI update if API call succeeded
          nextChanges.push(change);
          
          // find all edges connected to this node and delete them
          // note: edges on the backend have already been deleted by the above call
          const connectedEdges = getEdges.value.filter(
            (edge) => edge.source === node_id || edge.target === node_id,
          );

          for (const edge of connectedEdges) {
            removeEdges([edge.id]);
          }
        } catch (error) {
          console.error("Failed to delete node:", error);
          
          // Show user-friendly error message
          if (error.response?.status === 403) {
            alert("You don't have permission to delete nodes. Please log in with an account that has delete permissions.");
          } else if (error.response?.status === 401) {
            alert("You need to be logged in to delete nodes.");
          } else {
            alert("Failed to delete node. Please try again or contact support if the problem persists.");
          }
          
          // Don't add to nextChanges so UI doesn't update
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
        const edge = findEdge(change.id);
        const source_id = edge.data.source;
        const target_id = edge.data.target;
        const edge_type = edge.data.edge_type;
        const token = getAccessToken();
        try {
          const response = await api.delete(
            `/edges/${source_id}/${target_id}`,
            { edge_type: edge_type },
            token ? { headers: { Authorization: `Bearer ${token}` } } : {},
          );
          
          // Only proceed with UI update if API call succeeded
          nextChanges.push(change);
        } catch (error) {
          console.error("Failed to delete edge:", error);
          
          // Show user-friendly error message
          if (error.response?.status === 403) {
            alert("You don't have permission to delete edges. Please log in with an account that has delete permissions.");
          } else if (error.response?.status === 401) {
            alert("You need to be logged in to delete edges.");
          } else {
            alert("Failed to delete edge. Please try again or contact support if the problem persists.");
          }
          
          // Don't add to nextChanges so UI doesn't update
        }
      }
    } else {
      nextChanges.push(change);
    }
  }

  applyEdgeChanges(nextChanges);
};

function onConnectStart({ nodeId, handleType }) {
  console.log("on connect start", { nodeId, handleType });
  connectionInfo.value = { nodeId, handleType };
}

/**
 * onConnect is called when a new connection is created.
 *
 * You can add additional properties to your new edge (like a type or label) or block the creation altogether by not calling `addEdges`
 */
function onConnect(connection) {
  console.log("on connect", connection);
  
  // Check permissions first
  if (!canCreate.value) {
    alert("You don't have permission to create edges. Please log in with an account that has create permissions.");
    return; // Don't create the connection
  }
  
  // addEdges(connection);
  console.log("connectionInfo", connectionInfo.value);
  const target = connectionInfo.value.handleType === "source" ? connection.target : connection.source;
  const newEdgeData = createEdgeOnConnection(target);
  
  if (newEdgeData) { // Only proceed if edge creation is allowed
    nextTick(() => {
      emit("newEdgeCreated", newEdgeData);
    });
    addEdges(newEdgeData);
  }
  
  connectionInfo.value = null;
}

function onConnectEnd(event) {
  console.log("on connect end", event);

  if (connectionInfo.value) {
    console.log("Connected to an empty space");
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
  const source = handleType === "source" ? nodeId.toString() : targetId;
  const target = handleType === "source" ? targetId : nodeId.toString();

  const aNode = findNode(source);
  const bNode = findNode(target);

  // if the node is “new” its id is "new" → treat its type as undefined
  const isSourceNew = source === "new";
  const isTargetNew = target === "new";

  const sourceType = isSourceNew ? undefined : aNode?.data.node_type;
  const targetType = isTargetNew ? undefined : bNode?.data.node_type;

  const allowed = getAllowedEdgeTypes(sourceType, targetType);
  if (allowed.length === 0) {
    window.alert(
      `Cannot create any edge type between ${
        sourceType || "new"
      } → ${targetType || "new"}`
    );
    return null;
  }
  const chosenType = allowed[0];
  const newEdgeData = formatFlowEdgeProps({
    source: source,
    target: target,
    edge_type: chosenType
  });
  console.log("New edge data (direct connection):", newEdgeData);
  return newEdgeData;
}

function handleSearch(query) {
  console.log("Searching for:", query);
  let params = {};
  if (typeof query === "string") {
    if (!query.trim()) {
      searchResults.value = null;
      console.log("Empty query, not searching");
      return;
    }
    // if a raw string is provided, parse it first
    params = buildSearchParams(parseSearchQuery(query));
  } else if (typeof query === "object") {
    params = buildSearchParams(query);
  }

  api
    .get(`/nodes/`, { params })
    .then((response) => {
      console.log("Search results:", response.data);
      searchResults.value = response.data;
    })
    .catch((error) => {
      console.error("Failed to search nodes:", error);
    });
}

function createNodeAndEdge(event = null) {
  console.log("Creating a new node");
  
  // Check permissions first
  if (!canCreate.value) {
    alert("You don't have permission to create nodes. Please log in with an account that has create permissions.");
    closeSearchBar();
    return;
  }

  let scope = "";
  let tags = [];
  let fromConnection = null;
  let eventPosition = null;

  if (connectionInfo.value) {
    console.log("connectionInfo value detected, creating an edge too");
    const { nodeId, handleType } = connectionInfo.value;
    const sourceNode = findNode(nodeId);
    scope = sourceNode.data.scope; // inherited scope
    tags = sourceNode.data.tags; // inherited tags
    
    fromConnection = {
      id: nodeId,
      handle_type: handleType,
      node_type: sourceNode.data.node_type
      // edge_type: handleType === "source" ? "imply" : "require",
    }; // to be used to update edge data
    eventPosition = connectionInfo.value.position || {
      x: event?.clientX || 400,
      y: event?.clientY || 200,
    };
    //TODO: improve approximate offset between handle and node corner
    eventPosition.y -= 25;
    eventPosition.x -= handleType === "target" ? 225 : 0;
  } else {
    console.log("No connectionInfo available");
    // Default position for button clicks
    eventPosition = { 
      x: event?.clientX || 400, 
      y: event?.clientY || 200 
    };
    // console.log("Event position:", eventPosition);
  }
  // Get default type and allowed properties from the config
  // Build initial node data
  let newNodeData = formatFlowNodeProps({
    node_id: "new",
    title: "",
    status: "live",
    position: screenToFlowCoordinate(eventPosition),
    scope: scope,
    node_type: defaultNodeType.value,
    references: [],
    tags: tags,
    fromConnection: fromConnection,
  });

  if (connectionInfo.value) {
    // Get allowed node types from the source node’s type
    const fc = fromConnection; // { node_type, handle_type, ... }
    const allowedNodeTypes =
      fc.handle_type === "source"
        ? getAllowedTargetNodeTypes(fc.node_type)
        : getAllowedSourceNodeTypes(fc.node_type);
    // If defaultNodeType isn’t allowed, use the first allowed or fallback to default
    if (!allowedNodeTypes.includes(defaultNodeType.value)) {
      newNodeData.node_type = allowedNodeTypes[0] || defaultNodeType.value;
    }
  }

  // Remove properties not allowed by the default node type
  const allowedProps = nodeTypes.value[defaultNodeType.value].properties || [];
  if (!allowedProps.includes("status")) {
    delete newNodeData.status;
  }
  if (!allowedProps.includes("scope")) {
    delete newNodeData.scope;
  }
  if (!allowedProps.includes("tags")) {
    delete newNodeData.tags;
  }
  if (!allowedProps.includes("references")) {
    delete newNodeData.references;
  }
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

async function handleSearchResultClick(id, event) {
  console.log("search result clicked", id);
  try {
    const response = await api.get(
      `/nodes/${id}/`,
    );
    const node = response.data;
    // console.log("Fetched node:", node);
    let eventPosition = { x: event.clientX, y: event.clientY };
    // console.log("searhcbar position", searchBarPosition.value)  #TODO: maybe could use actual position of the original click not the result click
    // console.log("Event position:", eventPosition);
    node.position = screenToFlowCoordinate(eventPosition);
    const formattedNode = formatFlowNodeProps(node);
    addNodes(formattedNode);

    // if connected from existing node, create edge
    if (connectionInfo.value) 
    {
      if (!canCreate.value) {
        alert("You don't have permission to create edges. Please log in with an account that has create permissions.");
        return; // Don't create the connection
      }
      linkSourceToSearchResult(id);
    }
  } catch (error) {
    console.error("Failed to fetch node:", error);
  }
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
  const options = [];
  
  if (canEdit.value) {
    options.push({ name: "Edit Node", action: () => editNode(node) });
  }
  
  if (canDelete.value) {
    options.push({ name: "Delete Node", action: () => deleteNode(node) });
  }
  
  // Always show some option, even if just for information
  if (options.length === 0) {
    options.push({ name: "View Node", action: () => editNode(node) });
  }
  
  showContextMenu(event, options);
}

function onEdgeRightClick({ event, edge }) {
  console.log("Edge Right Click", edge);
  const options = [];
  
  if (canEdit.value) {
    options.push({ name: "Edit Edge", action: () => editEdge(edge) });
  }
  
  if (canDelete.value) {
    options.push({ name: "Delete Edge", action: () => deleteEdge(edge) });
  }
  
  // Always show some option, even if just for information
  if (options.length === 0) {
    options.push({ name: "View Edge", action: () => editEdge(edge) });
  }
  
  showContextMenu(event, options);
}

function onSelectionRightClick({ event, nodes }) {
  const options = [];
  
  // Group and Tag features are not yet implemented, so we'll comment them out for now
  // if (canEdit.value) {
  //   options.push({ name: "Create Group Node", action: () => groupSelection(nodes) });
  //   options.push({ name: "Tag Selection", action: () => tagSelection(nodes) });
  // }
  
  if (canDelete.value) {
    options.push({ name: "Delete Selection", action: () => deleteSelection(nodes) });
  }
  
  // If no actions are available, don't show context menu
  if (options.length > 0) {
    showContextMenu(event, options);
  }
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
  const options = [];
  
  if (canCreate.value) {
    options.push({ 
      name: "Create New Node", 
      action: () => createNodeAndEdge(event) 
    });
  } else {
    options.push({ 
      name: "Create New Node (No Permission)", 
      action: () => {
        alert("You don't have permission to create nodes. Please log in with an account that has create permissions.");
      },
      class: "disabled"
    });
  }
  
  showContextMenu(event, options);
}

function editNode(node) {
  console.log("Edit Node", node);
  
  // Check permissions first
  if (!canEdit.value) {
    alert("You don't have permission to edit nodes. Please log in with an account that has edit permissions.");
    return;
  }
  
  router.push({ name: "NodeEdit", params: { id: node.id } });
}

function deleteNode(node) {
  console.log("Delete Node", node);
  onNodesChange([{ type: "remove", id: node.id }]);
}

function editEdge(edge) {
  console.log("Edit Edge", edge);
  
  // Check permissions first
  if (!canEdit.value) {
    alert("You don't have permission to edit edges. Please log in with an account that has edit permissions.");
    return;
  }
  
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
  console.log("Create Group Node", selection);
  // not yet supported, show a message instead
  alert("Grouping nodes is not yet supported.");
}

function tagSelection(nodes) {
  console.log("Tag Selection", nodes);
  alert("Tagging nodes is not yet supported.");
  return;
  // potential issues: not all ndoes have a tag field, and edges may have tag field too 
  const nodeIds = nodes.map((node) => node.id);
  // collect tag from the user
  const tag = prompt("Enter a tag to apply to the selected nodes:");
  if (!tag) {
    console.warn("No tag provided, not applying any tags");
    return;
  }
  // send put request to the backend for each node which has the tag field and does not have this tag yet
}

function deleteSelection(nodes) {
  console.log("Delete Selection", nodes);
  const nodeIds = nodes.map((node) => node.id);
  onNodesChange(nodeIds.map((id) => ({ type: "remove", id })));
  // edge deletion is handled through the `onEdgesChange` method
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
  <div class="subgraph-renderer">
    <VueFlow
      :nodes="nodes"
      :edges="edges"
      :default-viewport="{ zoom: 1.5 }"
      :min-zoom="0.2"
      :max-zoom="4"
      :apply-default="false"
      :connection-mode="ConnectionMode.Strict"
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
            padding: 7px;
            border-radius: 2px;
            margin-top: 0px;
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
          :show-button="true"
          style="width: 100%"
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
            <span style="margin-right: 5px">➔</span>{{ result.title }} ({{ result.node_type || "— no type —" }})
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

      <!-- <MiniMap /> -->

      <Panel class="compass-panel" style="margin-top: 5px; margin-right: 2px; right: 2px">
        <div class="compass-container">
          <svg 
            class="compass-svg" 
            viewBox="0 0 120 120" 
            width="60" 
            height="60"
          >
            <!-- Outer circle -->
            <circle 
              cx="60" 
              cy="60" 
              r="58" 
              fill="transparent" 
              stroke="#ccc" 
              stroke-width="2"
            />
            
            <!-- Inner compass rose -->
            <g class="compass-rose">
              <!-- Main directional lines -->
              <line x1="60" y1="8" x2="60" y2="112" stroke="#ddd" stroke-width="1"/>
              <line x1="8" y1="60" x2="112" y2="60" stroke="#ddd" stroke-width="1"/>
              
              <!-- Diagonal lines -->
              <line x1="21.2" y1="21.2" x2="98.8" y2="98.8" stroke="#eee" stroke-width="1"/>
              <line x1="98.8" y1="21.2" x2="21.2" y2="98.8" stroke="#eee" stroke-width="1"/>
            </g>
            
            <!-- Combined quadrant groups for click and hover -->
            <g class="quadrant north" @click="selectDirection('BT', true)" title="Upward causality">
              <path d="M 60 60 L 15 15 L 60 2 L 105 15 Z" fill="transparent" class="compass-quadrant"/>
              <path d="M 60 60 L 45 45 L 60 8 L 75 45 Z" :fill="selectedDirection==='BT'?'#007bff':'white'" :stroke="selectedDirection==='BT'?'#007bff':'#666'" :stroke-width="selectedDirection==='BT'?3:2" class="compass-direction" pointer-events="none"/>
            </g>
            
            <g class="quadrant east" @click="selectDirection('LR', true)" title="Rightward causality">
              <path d="M 60 60 L 105 15 L 118 60 L 105 105 Z" fill="transparent" class="compass-quadrant"/>
              <path d="M 60 60 L 75 45 L 112 60 L 75 75 Z" :fill="selectedDirection==='LR'?'#007bff':'white'" :stroke="selectedDirection==='LR'?'#007bff':'#666'" :stroke-width="selectedDirection==='LR'?3:2" class="compass-direction" pointer-events="none"/>
            </g>
            
            <g class="quadrant south" @click="selectDirection('TB', true)" title="Downward causality">
              <path d="M 60 60 L 105 105 L 60 118 L 15 105 Z" fill="transparent" class="compass-quadrant"/>
              <path d="M 60 60 L 75 75 L 60 112 L 45 75 Z" :fill="selectedDirection==='TB'?'#007bff':'white'" :stroke="selectedDirection==='TB'?'#007bff':'#666'" :stroke-width="selectedDirection==='TB'?3:2" class="compass-direction" pointer-events="none"/>
            </g>
            
            <g class="quadrant west" @click="selectDirection('RL', true)" title="Leftward causality">
              <path d="M 60 60 L 15 105 L 2 60 L 15 15 Z" fill="transparent" class="compass-quadrant"/>
              <path d="M 60 60 L 45 75 L 8 60 L 45 45 Z" :fill="selectedDirection==='RL'?'#007bff':'white'" :stroke="selectedDirection==='RL'?'#007bff':'#666'" :stroke-width="selectedDirection==='RL'?3:2" class="compass-direction" pointer-events="none"/>
            </g>
            
            <!-- Discrete center lines to summits -->
            <line x1="60" y1="60" x2="60" y2="8" stroke="#999" stroke-width="1" class="compass-indicator"/>
            <line x1="60" y1="60" x2="112" y2="60" stroke="#999" stroke-width="1" class="compass-indicator"/>
            <line x1="60" y1="60" x2="60" y2="112" stroke="#999" stroke-width="1" class="compass-indicator"/>
            <line x1="60" y1="60" x2="8" y2="60" stroke="#999" stroke-width="1" class="compass-indicator"/>
            
           </svg>
        </div>
      </Panel>

      <Controls
        position="top-right"
        style="margin-top: 72px; margin-right: 20px"
      >
        <ControlButton title="Export subgraph as JSON" @click="exportSubgraph">
          <!-- style="background-color: var(--node-color); border-color: var(--node-color);" -->
          <Icon name="export" />
        </ControlButton>
      </Controls>
    </VueFlow>
  </div>
</template>

<style>
.subgraph-renderer {
  flex-grow: 1;
  border: 1px solid var(--border-color);
  border-radius: 5px;
  width: 100%;
  height: 100%;
  min-height: 300px;
  min-width: 300px;
  overflow: hidden;
}

.search-bar-container {
  position: absolute;
  background-color: var(--background-color);
  border: 1px solid var(--border-color);
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
  background-color: var(--border-color);
}

.search-bar-container .highlight {
  background-color: var(--highlight-color);
}

.search-bar-container .close-button {
  position: absolute;
  top: 1px;
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

.compass-container {
  display: flex;
  justify-content: center;
  align-items: center;
}

.compass-svg {
  cursor: pointer;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
}

.compass-quadrant {
  cursor: pointer;
}

.compass-direction {
  transition: all 0.2s ease-in-out;
}

.quadrant:hover .compass-direction {
  stroke-width: 5 !important;
  filter: brightness(1.5);
  /* background-color: blue !important */
  /* filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1)); */
}

.compass-direction.hovered {
  filter: brightness(1.15);
}

.compass-indicator {
  pointer-events: none;
}

.compass-rose {
  pointer-events: none;
}

/* Context menu disabled items */
.vue-simple-context-menu .disabled {
  color: #999 !important;
  cursor: not-allowed !important;
  opacity: 0.6;
  background-color: #f5f5f5 !important;
}

.vue-simple-context-menu .disabled:hover {
  background-color: #f5f5f5 !important;
  color: #999 !important;
}
</style>
