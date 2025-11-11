<template>
  <div class="cosmos-graph-container">
    <div ref="cosmosContainer" class="cosmos-container"></div>
    <div class="controls" v-if="showControls">
      <button
        @click="toggleSimulation"
        class="control-button"
        :disabled="!enableSimulation"
      >
        <span v-if="!isSimulationRunning">Start Simulation</span>
        <span v-else>Pause Simulation</span>
      </button>
      <button
        @click="applyClusteredLayout"
        :class="['control-button', { active: layoutMode === 'clustered' }]"
      >
        Clustered Layout
      </button>
      <button
        @click="applyDirectionalLayout"
        :class="['control-button', { active: layoutMode === 'directional' }]"
      >
        Directional Layout
      </button>
      <button
        @click="applyRandomLayout"
        :class="['control-button', { active: layoutMode === 'random' }]"
      >
        Random Layout
      </button>
    </div>
  </div>
</template>

<script>
import { nextTick, onBeforeUnmount, onMounted, ref, toRef, watch } from "vue";
import { Graph as CosmosGraph } from "@cosmos.gl/graph";
import api from "../../api/axios";

const DEFAULT_NODE_COLOR = "#666666";
const DEFAULT_LINK_COLOR = "#cccccc";

const getCssVariable = (name, fallback) => {
  if (typeof window === "undefined") return fallback;
  const value = getComputedStyle(document.body).getPropertyValue(name).trim();
  return value || fallback;
};

export default {
  name: "CosmosGraphVis",
  props: {
    graphData: {
      type: Object,
      default: null,
    },
    apiEndpoint: {
      type: String,
      default: "/graph",
    },
    showControls: {
      type: Boolean,
      default: false,
    },
    autoStartForceAtlas: {
      type: Boolean,
      default: false,
    },
    enableSimulation: {
      type: Boolean,
      default: true,
    },
    height: {
      type: String,
      default: "400px",
    },
    initialLayout: {
      type: String,
      default: "clustered",
      validator: (value) =>
        ["clustered", "directional", "random"].includes(value),
    },
  },
  emits: ["nodeClick", "edgeClick", "graphLoaded"],
  setup(props, { emit }) {
    const cosmosContainer = ref(null);
    const cosmosGraph = ref(null);
    const isSimulationRunning = ref(false);
    const nodeIndexMeta = ref([]);
    const edgeIndexMeta = ref([]);
    const currentGraphData = ref({ nodes: [], edges: [] });
    const graphState = ref(null);
    const normalizeLayout = (layout) =>
      ["clustered", "directional", "random"].includes(layout)
        ? layout
        : "clustered";
    const layoutMode = ref(normalizeLayout(props.initialLayout));
    const enableSimulationRef = toRef(props, "enableSimulation");
    let lastFetchId = 0;

    const updateSimulationState = () => {
      if (!props.enableSimulation) {
        isSimulationRunning.value = false;
        return;
      }
      isSimulationRunning.value =
        cosmosGraph.value?.isSimulationRunning ?? false;
    };

    const destroyGraph = () => {
      cosmosGraph.value?.destroy();
      cosmosGraph.value = null;
      nodeIndexMeta.value = [];
      edgeIndexMeta.value = [];
      currentGraphData.value = { nodes: [], edges: [] };
      graphState.value = null;
      updateSimulationState();
    };

    const fetchGraphData = async () => {
      if (props.graphData) {
        return props.graphData;
      }

      const response = await api.get(props.apiEndpoint);
      return response.data;
    };

    const buildGraphState = (rawData = {}) => {
      const sourceNodes = Array.isArray(rawData?.nodes) ? rawData.nodes : [];
      const sourceEdges = Array.isArray(rawData?.edges) ? rawData.edges : [];

      const nodes = sourceNodes.map((node, index) => ({
        ...node,
        id: node.id ?? node.node_id ?? index,
      }));

      const totalNodes = nodes.length;
      const nodeMetaList = new Array(totalNodes);
      const idToIndex = new Map();
      const adjacencyOut = new Map();
      const adjacencyUndirected = new Map();

      nodes.forEach((node, index) => {
        const nodeKey = String(node.node_id ?? node.id ?? index);
        idToIndex.set(nodeKey, index);
        nodeMetaList[index] = { id: nodeKey, data: node };
        adjacencyOut.set(index, new Set());
        adjacencyUndirected.set(index, new Set());
      });

      const linkIndices = [];
      const edgesMetaList = [];
      const sanitizedEdges = [];

      sourceEdges.forEach((edge, edgeIndex) => {
        const sourceKey = String(edge.source_id ?? edge.source ?? "");
        const targetKey = String(edge.target_id ?? edge.target ?? "");
        const sourceNodeIndex = idToIndex.get(sourceKey);
        const targetNodeIndex = idToIndex.get(targetKey);

        if (sourceNodeIndex === undefined || targetNodeIndex === undefined) {
          return;
        }

        const edgeId = String(
          edge.edge_id ??
            edge.id ??
            `edge_${sourceKey}_${targetKey}_${edgeIndex}`,
        );

        linkIndices.push(sourceNodeIndex, targetNodeIndex);
        sanitizedEdges.push({ ...edge, edge_id: edgeId });
        edgesMetaList.push({
          id: edgeId,
          sourceIndex: sourceNodeIndex,
          targetIndex: targetNodeIndex,
          data: edge,
        });

        adjacencyOut.get(sourceNodeIndex)?.add(targetNodeIndex);
        adjacencyUndirected.get(sourceNodeIndex)?.add(targetNodeIndex);
        adjacencyUndirected.get(targetNodeIndex)?.add(sourceNodeIndex);
      });

      return {
        nodes,
        edges: sanitizedEdges,
        nodeMeta: nodeMetaList,
        edgeMeta: edgesMetaList,
        links:
          linkIndices.length > 0
            ? new Float32Array(linkIndices)
            : new Float32Array(0),
        adjacency: {
          out: adjacencyOut,
          undirected: adjacencyUndirected,
        },
        totalNodes,
      };
    };

    const computeConnectedComponents = (state) => {
      const total = state.totalNodes;
      if (!total) return [];

      const components = [];
      const visited = new Array(total).fill(false);

      for (let i = 0; i < total; i += 1) {
        if (visited[i]) continue;
        const stack = [i];
        const component = [];
        visited[i] = true;

        while (stack.length) {
          const nodeIndex = stack.pop();
          component.push(nodeIndex);
          const neighbors = state.adjacency.undirected.get(nodeIndex);
          if (!neighbors) continue;
          neighbors.forEach((neighbor) => {
            if (!visited[neighbor]) {
              visited[neighbor] = true;
              stack.push(neighbor);
            }
          });
        }

        components.push(component);
      }

      return components;
    };

    const generateClusteredPositions = (state, containerSize) => {
      const total = state.totalNodes;
      const positions = new Float32Array(total * 2);
      if (!total) return positions;

      const components = computeConnectedComponents(state);
      const width = containerSize?.width ?? 800;
      const height = containerSize?.height ?? 600;
      const maxDimension = Math.max(width, height);
      const baseRadius = Math.min(
        Math.max(220, Math.sqrt(total) * 75),
        maxDimension * 0.45,
      );
      const goldenAngle = Math.PI * (3 - Math.sqrt(5));

      components.forEach((component, componentIndex) => {
        const spiralRadius = baseRadius * Math.sqrt(componentIndex + 0.75);
        const angle = componentIndex * goldenAngle;
        const cx = Math.cos(angle) * spiralRadius;
        const cy = Math.sin(angle) * spiralRadius;
        const localCount = component.length;
        const localRadius =
          localCount <= 1
            ? 0
            : Math.min(
                Math.max(120, Math.sqrt(localCount) * 50),
                maxDimension * 0.3,
              );

        component.forEach((nodeIndex, localIndex) => {
          if (localCount <= 1) {
            positions[nodeIndex * 2] = cx;
            positions[nodeIndex * 2 + 1] = cy;
            return;
          }

          const theta = (2 * Math.PI * localIndex) / localCount;
          const jitter =
            (Math.random() - 0.5) * Math.min(18, localRadius * 0.1);
          positions[nodeIndex * 2] =
            cx + Math.cos(theta) * localRadius + jitter;
          positions[nodeIndex * 2 + 1] =
            cy + Math.sin(theta) * localRadius + jitter;
        });
      });

      return positions;
    };

    const generateDirectionalPositions = (state) => {
      const total = state.totalNodes;
      const positions = new Float32Array(total * 2);
      if (!total) return positions;

      const outMap = state.adjacency.out;
      const inDegree = new Array(total).fill(0);

      state.edgeMeta.forEach((edge) => {
        inDegree[edge.targetIndex] += 1;
      });

      const remainingInDegree = [...inDegree];
      const queue = [];
      const levels = new Array(total).fill(0);
      const visitOrder = [];

      for (let i = 0; i < total; i += 1) {
        if (remainingInDegree[i] === 0) {
          queue.push(i);
        }
      }

      while (queue.length) {
        const nodeIndex = queue.shift();
        visitOrder.push(nodeIndex);
        const neighbors = outMap.get(nodeIndex);
        if (!neighbors || neighbors.size === 0) continue;

        neighbors.forEach((neighbor) => {
          if (levels[neighbor] < levels[nodeIndex] + 1) {
            levels[neighbor] = levels[nodeIndex] + 1;
          }
          remainingInDegree[neighbor] -= 1;
          if (remainingInDegree[neighbor] === 0) {
            queue.push(neighbor);
          }
        });
      }

      const visitedSet = new Set(visitOrder);
      let fallbackLevel = Math.max(...levels);
      if (!Number.isFinite(fallbackLevel)) fallbackLevel = 0;

      for (let i = 0; i < total; i += 1) {
        if (visitedSet.has(i)) continue;
        fallbackLevel += 1;
        levels[i] = fallbackLevel;
      }

      const layerBuckets = new Map();
      for (let i = 0; i < total; i += 1) {
        const level = levels[i];
        const bucket = layerBuckets.get(level);
        if (bucket) bucket.push(i);
        else layerBuckets.set(level, [i]);
      }

      const sortedLevels = Array.from(layerBuckets.keys()).sort(
        (a, b) => a - b,
      );
      const maxLevel = sortedLevels[sortedLevels.length - 1] ?? 0;
      const layerSpacing = Math.max(240, Math.sqrt(total) * 90);

      sortedLevels.forEach((level) => {
        const nodesInLevel = layerBuckets.get(level) ?? [];
        if (!nodesInLevel.length) return;

        const nodeSpacing = Math.max(160, Math.sqrt(nodesInLevel.length) * 100);
        const offset = (nodesInLevel.length - 1) / 2;

        nodesInLevel.forEach((nodeIndex, index) => {
          const x = (level - maxLevel / 2) * layerSpacing;
          const y = (index - offset) * nodeSpacing;
          positions[nodeIndex * 2] = x;
          positions[nodeIndex * 2 + 1] = y;
        });
      });

      return positions;
    };

    const generateRandomPositions = (state, containerSize) => {
      const total = state.totalNodes;
      const positions = new Float32Array(total * 2);
      if (!total) return positions;

      const width = containerSize?.width ?? 800;
      const height = containerSize?.height ?? 600;

      for (let i = 0; i < total; i += 1) {
        positions[i * 2] = (Math.random() - 0.5) * width;
        positions[i * 2 + 1] = (Math.random() - 0.5) * height;
      }

      return positions;
    };

    const computePositions = (state, mode, containerSize) => {
      if (!state) return new Float32Array(0);
      switch (mode) {
        case "directional":
          return generateDirectionalPositions(state);
        case "random":
          return generateRandomPositions(state, containerSize);
        case "clustered":
        default:
          return generateClusteredPositions(state, containerSize);
      }
    };

    const handlePointClick = (index) => {
      const meta = nodeIndexMeta.value[index];
      if (!meta) return;
      emit("nodeClick", meta.id);
    };

    const handleLinkClick = (index) => {
      const meta = edgeIndexMeta.value[index];
      if (!meta) return;
      emit("edgeClick", meta.id);
    };

    const buildConfig = () => ({
      backgroundColor: getCssVariable("--background-color", "#ffffff"),
      pointColor: DEFAULT_NODE_COLOR,
      pointSize: 8,
      linkColor: getCssVariable("--border-color", DEFAULT_LINK_COLOR),
      linkWidth: 1.5,
      curvedLinks: true,
      enableSimulation: props.enableSimulation,
      enableZoom: true,
      enableDrag: true,
      rescalePositions: true,
      fitViewOnInit: false,
      fitViewPadding: 0.2,
      hoveredPointCursor: "pointer",
      hoveredLinkCursor: "pointer",
      enableRightClickRepulsion: false,
      linkArrows: true,
      onPointClick: handlePointClick,
      onLinkClick: handleLinkClick,
      onSimulationStart: updateSimulationState,
      onSimulationPause: updateSimulationState,
      onSimulationUnpause: updateSimulationState,
      onSimulationEnd: updateSimulationState,
    });

    const applyGraphData = (rawData, { respectSimulationState } = {}) => {
      if (!cosmosGraph.value) return;

      const state = buildGraphState(rawData ?? {});
      graphState.value = state;

      const containerSize = {
        width: cosmosContainer.value?.clientWidth ?? 800,
        height: cosmosContainer.value?.clientHeight ?? 600,
      };

      const positions = computePositions(
        state,
        layoutMode.value,
        containerSize,
      );

      cosmosGraph.value.setPointPositions(positions, true);
      cosmosGraph.value.setLinks(state.links);

      const shouldResume =
        props.enableSimulation &&
        (respectSimulationState
          ? cosmosGraph.value.isSimulationRunning
          : !!props.autoStartForceAtlas);

      cosmosGraph.value.render(0);
      if (shouldResume) cosmosGraph.value.start(1);
      else cosmosGraph.value.pause();

      nodeIndexMeta.value = state.nodeMeta;
      edgeIndexMeta.value = state.edgeMeta;
      currentGraphData.value = {
        nodes: state.nodes,
        edges: state.edges,
      };

      emit("graphLoaded", currentGraphData.value);
      updateSimulationState();

      if (state.totalNodes) {
        cosmosGraph.value.fitView(300, 0.18);
      }
    };

    const applyLayout = (mode) => {
      const normalized = normalizeLayout(mode);
      layoutMode.value = normalized;
      if (!cosmosGraph.value || !graphState.value) return;

      const wasRunning = props.enableSimulation
        ? (cosmosGraph.value.isSimulationRunning ?? false)
        : false;
      if (props.enableSimulation) {
        cosmosGraph.value.pause();
      }

      const containerSize = {
        width: cosmosContainer.value?.clientWidth ?? 800,
        height: cosmosContainer.value?.clientHeight ?? 600,
      };

      const positions = computePositions(
        graphState.value,
        normalized,
        containerSize,
      );

      cosmosGraph.value.setPointPositions(positions, true);
      cosmosGraph.value.render(0);

      if (graphState.value.totalNodes) {
        cosmosGraph.value.fitView(300, 0.18);
      }

      if (props.enableSimulation && wasRunning) {
        cosmosGraph.value.start(1);
      }

      updateSimulationState();
    };

    const initializeGraph = async () => {
      await nextTick();
      if (!cosmosContainer.value) return;

      destroyGraph();

      const fetchId = ++lastFetchId;
      try {
        const data = await fetchGraphData();
        if (fetchId !== lastFetchId) return;
        if (!cosmosContainer.value) return;

        cosmosGraph.value = new CosmosGraph(
          cosmosContainer.value,
          buildConfig(),
        );

        applyGraphData(data, { respectSimulationState: false });
      } catch (error) {
        console.error("Error initializing Cosmos graph:", error);
      }
    };

    const pauseSimulation = () => {
      if (!props.enableSimulation) return;
      cosmosGraph.value?.pause();
      updateSimulationState();
    };

    const startSimulation = () => {
      if (!props.enableSimulation) return;
      cosmosGraph.value?.start(1);
      updateSimulationState();
    };

    const toggleSimulation = () => {
      if (!props.enableSimulation) return;
      const running = cosmosGraph.value?.isSimulationRunning ?? false;
      if (running) pauseSimulation();
      else startSimulation();
    };

    const applyClusteredLayout = () => {
      applyLayout("clustered");
    };

    const applyDirectionalLayout = () => {
      applyLayout("directional");
    };

    const applyRandomLayout = () => {
      applyLayout("random");
    };

    watch(
      () => props.graphData,
      async (newData) => {
        if (!cosmosGraph.value) {
          if (newData) {
            await initializeGraph();
          }
          return;
        }

        try {
          const data = newData ?? (await fetchGraphData());
          applyGraphData(data, { respectSimulationState: true });
        } catch (error) {
          console.error("Error updating Cosmos graph data:", error);
        }
      },
      { deep: true },
    );

    watch(
      () => props.autoStartForceAtlas,
      (auto) => {
        if (!props.enableSimulation || !cosmosGraph.value) return;
        if (auto) startSimulation();
        else pauseSimulation();
      },
    );

    watch(
      () => props.initialLayout,
      (layout) => {
        const normalized = normalizeLayout(layout);
        if (!graphState.value) {
          layoutMode.value = normalized;
          return;
        }
        applyLayout(normalized);
      },
    );

    onMounted(() => {
      initializeGraph();
    });

    onBeforeUnmount(() => {
      destroyGraph();
    });

    return {
      cosmosContainer,
      isSimulationRunning,
      layoutMode,
      toggleSimulation,
      applyClusteredLayout,
      applyDirectionalLayout,
      applyRandomLayout,
      enableSimulation: enableSimulationRef,
    };
  },
};
</script>

<style scoped>
.cosmos-graph-container {
  position: relative;
  width: 100%;
  height: v-bind(height);
  display: flex;
  flex-direction: column;
}

.cosmos-container {
  width: 100%;
  height: 100%;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background-color: var(--background-color);
  position: relative;
  overflow: hidden;
}

.cosmos-container :deep(canvas) {
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

.control-button.active {
  font-weight: 600;
  border-color: var(--text-color);
}

.control-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

:global(body.dark) .control-button {
  background-color: #333;
  color: #fff;
  border-color: #555;
}

:global(body.dark) .control-button:hover {
  background-color: #444;
  border-color: #777;
}
</style>
