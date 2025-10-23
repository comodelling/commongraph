<template>
  <div class="sigma-graph-container">
    <div ref="sigmaContainer" class="sigma-container"></div>
    <div class="controls" v-if="showControls">
      <button @click="toggleForceAtlas2" class="control-button">
        <span v-if="!isFA2Running">Start Force Atlas 2</span>
        <span v-else>Stop Force Atlas 2</span>
      </button>
      <button @click="circularLayout" class="control-button">Circular Layout</button>
      <button @click="randomLayout" class="control-button">Random Layout</button>
    </div>
  </div>
</template>

<script>
import { onMounted, onBeforeUnmount, ref, watch } from "vue";
import api from "../../api/axios";
import Graph from "graphology";
import Sigma from "sigma";
import forceAtlas2 from "graphology-layout-forceatlas2";
import { circular } from "graphology-layout";
import { animateNodes } from "sigma/utils";

export default {
  name: "SigmaGraphVis",
  props: {
    // If graphData is provided, use it directly. Otherwise fetch from API
    graphData: {
      type: Object,
      default: null
    },
    // API endpoint to fetch graph data from
    apiEndpoint: {
      type: String,
      default: "/graph"
    },
    // Show layout control buttons
    showControls: {
      type: Boolean,
      default: false
    },
    // Auto-start force atlas layout
    autoStartForceAtlas: {
      type: Boolean,
      default: true
    },
    // Graph container height
    height: {
      type: String,
      default: "400px"
    }
  },
  emits: ['nodeClick', 'edgeClick', 'graphLoaded'],
  setup(props, { emit }) {
    const sigmaContainer = ref(null);
    const graph = ref(null);
    const renderer = ref(null);
    const isFA2Running = ref(false);
    const fa2Worker = ref(null);
    const cancelCurrentAnimation = ref(null);
    const resizeObserver = ref(null);

    const initializeGraph = async () => {
      if (!sigmaContainer.value) return;

      try {
        // Create new graph instance
        graph.value = new Graph();

        let data;
        if (props.graphData) {
          // Use provided graph data
          data = props.graphData;
        } else {
          // Fetch graph data from API
          const response = await api.get(props.apiEndpoint);
          data = response.data;
        }

        // Convert your data format to graphology format
        if (data.nodes) {
          data.nodes.forEach(node => {
            const nodeId = String(node.node_id || node.id);
            graph.value.addNode(nodeId, {
              x: Math.random() * 100,
              y: Math.random() * 100,
              size: 10,
              label: node.title || node.label || `Node ${nodeId}`,
              color: "#666",
              highlighted: false
            });
          });
        }

        if (data.edges) {
          data.edges.forEach((edge, index) => {
            const sourceId = String(edge.source_id || edge.source);
            const targetId = String(edge.target_id || edge.target);
            
            if (graph.value.hasNode(sourceId) && graph.value.hasNode(targetId)) {
              // Create a unique edge ID if not provided
              const edgeId = edge.edge_id || edge.id || `edge_${sourceId}_${targetId}_${index}`;
            //   console.log(`Adding edge: ${edgeId} from ${sourceId} to ${targetId} (type: ${edge.edge_type || edge.type})`);
              
              // Ensure we're passing string IDs, not numbers
              const sourceIdStr = String(sourceId);
              const targetIdStr = String(targetId);
              const edgeIdStr = String(edgeId);
              
              try {
                // Define edge attributes
                const edgeAttributes = {
                  size: 2,
                  color: "#ccc",
                  label: edge.edge_type || edge.type || null,
                  highlighted: false,
                  type: "arrow"
                };
                
                // Try the method with key first, then fallback to auto-key
                if (typeof graph.value.addEdgeWithKey === 'function') {
                  graph.value.addEdgeWithKey(edgeIdStr, sourceIdStr, targetIdStr, edgeAttributes);
                //   console.log(`Successfully added edge during init with key: ${edgeIdStr}`);
                } else {
                  // Use auto-generated key method
                  const autoEdgeId = graph.value.addEdge(sourceIdStr, targetIdStr, edgeAttributes);
                //   console.log(`Successfully added edge during init with auto key: ${autoEdgeId}`);
                }
              } catch (error) {
                console.error(`Failed to add edge during init ${edgeIdStr}:`, error);
                console.error(`Graph methods available:`, Object.getOwnPropertyNames(graph.value).filter(name => name.includes('Edge')));
              }
            } else {
            //   console.warn(`Skipping edge - missing nodes: ${sourceId} -> ${targetId}`);
            }
          });
        }

        // Initialize Sigma renderer with settings
        renderer.value = new Sigma(graph.value, sigmaContainer.value, {
          renderLabels: false, // Hide labels by default
          renderEdgeLabels: true,
          enableEdgeHoverEvents: true, // Enable edge hover events
          enableEdgeClickEvents: true, // Enable edge click events
          edgeHoverHighlightNodes: 'circle',
                      // edgeReducer: (edge, data) => {
          //   if (data.highlighted) {
          //     return {
          //       ...data,
          //       color: "red", // Highlight color
          //       size: 4        // Thicker on hover
          //     };
          //   }
          //   return data;
          // }
        });

        // Ensure the renderer uses the full container size
        renderer.value.refresh();

        // Set up resize observer to handle container size changes
        resizeObserver.value = new ResizeObserver(() => {
          if (renderer.value) {
            renderer.value.refresh();
          }
        });
        
        resizeObserver.value.observe(sigmaContainer.value);

        // Set up event listeners
        renderer.value.on("clickNode", (event) => {
          console.log("Node clicked:", event.node);
          emit('nodeClick', event.node);
        });

        renderer.value.on("clickEdge", (event) => {
          console.log("Edge clicked:", event.edge);
          emit('edgeClick', event.edge);
        });

        // Show node label on hover
        renderer.value.on("enterNode", (event) => {
          renderer.value.getGraph().setNodeAttribute(event.node, "highlighted", true);
          renderer.value.refresh();
        });

        renderer.value.on("leaveNode", (event) => {
          renderer.value.getGraph().setNodeAttribute(event.node, "highlighted", false);
          renderer.value.refresh();
        });

        // Show edge label and highlight on hover
        renderer.value.on("enterEdge", (event) => {
          console.log("Edge enter event triggered:", event.edge);
          renderer.value.getGraph().setEdgeAttribute(event.edge, "highlighted", true);
          renderer.value.refresh();
        });

        renderer.value.on("leaveEdge", (event) => {
          console.log("Edge leave event triggered:", event.edge);
          renderer.value.getGraph().setEdgeAttribute(event.edge, "highlighted", false);
          renderer.value.refresh();
        });

        // Initialize Force Atlas 2 layout (synchronous version)
        if (graph.value.order > 0 && props.autoStartForceAtlas) {
          startFA2();
        }

        emit('graphLoaded', { nodes: data.nodes, edges: data.edges });

      } catch (error) {
        console.error("Error initializing graph:", error);
      }
    };

    const startFA2 = () => {
      if (!graph.value || isFA2Running.value) return;
      if (cancelCurrentAnimation.value) cancelCurrentAnimation.value();
      
      // Use synchronous Force Atlas 2
      const sensibleSettings = {barnesHutOptimize: true, adjustSizes: true};
      
      const runFA2Iteration = () => {
        if (isFA2Running.value) {
          forceAtlas2.assign(graph.value, { iterations: 1, settings: sensibleSettings });
          renderer.value.refresh();
          requestAnimationFrame(runFA2Iteration);
        }
      };
      
      isFA2Running.value = true;
      runFA2Iteration();
    };

    const stopFA2 = () => {
      isFA2Running.value = false;
    };

    const toggleForceAtlas2 = () => {
      if (isFA2Running.value) {
        stopFA2();
      } else {
        startFA2();
      }
    };

    const circularLayout = () => {
      if (!graph.value) return;
      
      // Stop FA2 if running
      stopFA2();
      if (cancelCurrentAnimation.value) cancelCurrentAnimation.value();

      // Apply circular layout with animation
      const circularPositions = circular(graph.value, { scale: 100 });
      cancelCurrentAnimation.value = animateNodes(graph.value, circularPositions, { 
        duration: 2000, 
        easing: "linear" 
      });
    };

    const randomLayout = () => {
      if (!graph.value) return;
      
      // Stop FA2 if running
      stopFA2();
      if (cancelCurrentAnimation.value) cancelCurrentAnimation.value();

      // Calculate current position extents
      const xExtents = { min: 0, max: 0 };
      const yExtents = { min: 0, max: 0 };
      
      graph.value.forEachNode((_node, attributes) => {
        xExtents.min = Math.min(attributes.x, xExtents.min);
        xExtents.max = Math.max(attributes.x, xExtents.max);
        yExtents.min = Math.min(attributes.y, yExtents.min);
        yExtents.max = Math.max(attributes.y, yExtents.max);
      });

      // Generate random positions
      const randomPositions = {};
      graph.value.forEachNode((node) => {
        randomPositions[node] = {
          x: Math.random() * (xExtents.max - xExtents.min),
          y: Math.random() * (yExtents.max - yExtents.min),
        };
      });

      // Apply with animation
      cancelCurrentAnimation.value = animateNodes(graph.value, randomPositions, { duration: 2000 });
    };

    const cleanup = () => {
      if (cancelCurrentAnimation.value) {
        cancelCurrentAnimation.value();
      }
      stopFA2();
      if (resizeObserver.value) {
        resizeObserver.value.disconnect();
      }
      if (renderer.value) {
        renderer.value.kill();
      }
    };

    // Watch for prop changes
    watch(() => props.graphData, (newData, oldData) => {
      // Only reinitialize if we actually have new data structure
      if (!renderer.value || !newData) {
        cleanup();
        initializeGraph();
        return;
      }
      
      // If we already have a renderer, just update the data
      updateGraphData(newData);
    }, { deep: true });

    const updateGraphData = (data) => {
      if (!renderer.value || !graph.value) return;
      
      try {
        // console.log("updateGraphData called with:", data);
        
        // Clear existing data
        graph.value.clear();
        
        // Add nodes
        if (data.nodes) {
        //   console.log(`Adding ${data.nodes.length} nodes`);
          data.nodes.forEach(node => {
            const nodeId = String(node.node_id || node.id);
            graph.value.addNode(nodeId, {
              x: Math.random() * 100,
              y: Math.random() * 100,
              size: 10,
              label: node.title || node.label || `Node ${nodeId}`,
              color: "#666",
              highlighted: false
            });
          });
        }
        
        // Add edges
        if (data.edges && data.edges.length > 0) {
        //   console.log(`Adding ${data.edges.length} edges:`, data.edges);
          data.edges.forEach((edge, index) => {
            const sourceId = String(edge.source_id || edge.source);
            const targetId = String(edge.target_id || edge.target);
            
            // console.log(`Processing edge ${index}:`, edge);
            // console.log(`Source: ${sourceId}, Target: ${targetId}`);
            // console.log(`Has source node: ${graph.value.hasNode(sourceId)}`);
            // console.log(`Has target node: ${graph.value.hasNode(targetId)}`);
            
            if (graph.value.hasNode(sourceId) && graph.value.hasNode(targetId)) {
              const edgeId = edge.edge_id || edge.id || `edge_${sourceId}_${targetId}_${index}`;
            //   console.log(`Adding edge: ${edgeId} from ${sourceId} to ${targetId} (type: ${edge.edge_type || edge.type})`);
              
              // Ensure we're passing string IDs, not numbers
              const sourceIdStr = String(sourceId);
              const targetIdStr = String(targetId);
              const edgeIdStr = String(edgeId);
              
            //   console.log(`Edge IDs - edgeId: "${edgeIdStr}" (${typeof edgeIdStr}), source: "${sourceIdStr}" (${typeof sourceIdStr}), target: "${targetIdStr}" (${typeof targetIdStr})`);
              
              try {
                // Define edge attributes
                const edgeAttributes = {
                  size: 2,
                  color: "#ccc",
                  label: edge.edge_type || edge.type || null,
                  highlighted: false
                };
                
                // console.log(`Attempting to add edge with parameters:`, {
                //   key: edgeIdStr,
                //   source: sourceIdStr,
                //   target: targetIdStr,
                //   attributes: edgeAttributes
                // });
                
                // Try the method with key first, then fallback to auto-key
                if (typeof graph.value.addEdgeWithKey === 'function') {
                  graph.value.addEdgeWithKey(edgeIdStr, sourceIdStr, targetIdStr, edgeAttributes);
                //   console.log(`Successfully added edge with key: ${edgeIdStr}`);
                } else {
                  // Use auto-generated key method
                  const autoEdgeId = graph.value.addEdge(sourceIdStr, targetIdStr, edgeAttributes);
                //   console.log(`Successfully added edge with auto key: ${autoEdgeId}`);
                }
              } catch (error) {
                console.error(`Failed to add edge ${edgeIdStr}:`, error);
                console.error(`Edge data:`, edge);
                console.error(`Graph methods available:`, Object.getOwnPropertyNames(graph.value).filter(name => name.includes('Edge')));
              }
            } else {
              console.warn(`Skipping edge - missing nodes: ${sourceId} -> ${targetId}`);
            }
          });
        } else {
        //   console.log("No edges to add:", data.edges);
        }
        
        // console.log(`Graph now has ${graph.value.order} nodes and ${graph.value.size} edges`);
        
        // Refresh the renderer
        renderer.value.refresh();
        
        // Restart Force Atlas if it was running
        if (props.autoStartForceAtlas && graph.value.order > 0) {
          startFA2();
        }
        
        emit('graphLoaded', { nodes: data.nodes, edges: data.edges });
        
      } catch (error) {
        console.error("Error updating graph data:", error);
      }
    };

    onMounted(() => {
      initializeGraph();
    });

    onBeforeUnmount(() => {
      cleanup();
    });

    return {
      sigmaContainer,
      isFA2Running,
      toggleForceAtlas2,
      circularLayout,
      randomLayout,
      renderer,
      graph,
      updateGraphData
    };
  }
};
</script>

<style scoped>
.sigma-graph-container {
  position: relative;
  width: 100%;
  height: v-bind(height);
  display: flex;
  flex-direction: column;
}

.sigma-container {
  width: 100%;
  height: 100%;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background-color: var(--background-color);
  position: relative;
  overflow: hidden;
}

/* Ensure Sigma canvas fills the container properly */
.sigma-container :deep(canvas) {
  display: block !important;
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  width: 100% !important;
  height: 100% !important;
}

.controls {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  z-index: 10;
}

.control-button {
  padding: 8px 12px;
  background-color: var(--background-color);
  color: var(--text-color);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-family: inherit;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.control-button:hover {
  background-color: var(--border-color);
  border-color: var(--text-color);
}

.control-button:active {
  transform: translateY(1px);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* Dark mode specific styling */
:global(body.dark) .control-button {
  background-color: #333;
  color: white;
  border-color: #555;
}

:global(body.dark) .control-button:hover {
  background-color: #444;
  border-color: #777;
}
</style>