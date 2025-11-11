<template>
  <div class="cosmos-graph-container">
    <div ref="cosmosContainer" class="cosmos-container"></div>
    <div class="controls" v-if="showControls">
      <button @click="toggleSimulation" class="control-button">
        <span v-if="!isSimulationRunning">Start Simulation</span>
        <span v-else>Pause Simulation</span>
      </button>
      <button @click="applyCircularLayout" class="control-button">
        Circular Layout
      </button>
      <button @click="applyRandomLayout" class="control-button">
        Random Layout
      </button>
    </div>
  </div>
</template>

<script>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
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
      default: true,
    },
    height: {
      type: String,
      default: "400px",
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
    let lastFetchId = 0;

    const updateSimulationState = () => {
      isSimulationRunning.value =
        cosmosGraph.value?.isSimulationRunning ?? false;
    };

    const destroyGraph = () => {
      cosmosGraph.value?.destroy();
      cosmosGraph.value = null;
      nodeIndexMeta.value = [];
      edgeIndexMeta.value = [];
      currentGraphData.value = { nodes: [], edges: [] };
      updateSimulationState();
    };

    const fetchGraphData = async () => {
      if (props.graphData) {
        return props.graphData;
      }

      const response = await api.get(props.apiEndpoint);
      return response.data;
    };

    const buildGraphPayload = (rawData) => {
      const sourceNodes = Array.isArray(rawData?.nodes) ? rawData.nodes : [];
      const sourceEdges = Array.isArray(rawData?.edges) ? rawData.edges : [];

      const nodes = sourceNodes.map((node, index) => ({
        ...node,
        id: node.id ?? node.node_id ?? index,
      }));

      const nodeMetaList = new Array(nodes.length);
      const idToIndex = new Map();
      const totalNodes = nodes.length;
      const radius = Math.max(400, Math.sqrt(Math.max(totalNodes, 1)) * 120);
      const positions = new Float32Array(totalNodes * 2);

      nodes.forEach((node, index) => {
        const nodeKey = String(node.node_id ?? node.id ?? index);
        idToIndex.set(nodeKey, index);
        nodeMetaList[index] = { id: nodeKey, data: node };

        const hasNumericCoordinates =
          typeof node.x === "number" && typeof node.y === "number";
        const hasPositionObject =
          node.position &&
          typeof node.position.x === "number" &&
          typeof node.position.y === "number";

        const angle = (2 * Math.PI * index) / Math.max(totalNodes, 1);
        const x = hasNumericCoordinates
          ? node.x
          : hasPositionObject
            ? node.position.x
            : Math.cos(angle) * radius;
        const y = hasNumericCoordinates
          ? node.y
          : hasPositionObject
            ? node.position.y
            : Math.sin(angle) * radius;

        positions[index * 2] = Number.isFinite(x) ? x : 0;
        positions[index * 2 + 1] = Number.isFinite(y) ? y : 0;
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
      });

      return {
        pointPositions: positions,
        links:
          linkIndices.length > 0
            ? new Float32Array(linkIndices)
            : new Float32Array(0),
        nodeMeta: nodeMetaList,
        edgeMeta: edgesMetaList,
        sanitized: {
          nodes,
          edges: sanitizedEdges,
        },
      };
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
      enableSimulation: true,
      enableZoom: true,
      enableDrag: true,
      rescalePositions: true,
      fitViewOnInit: true,
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

      const payload = buildGraphPayload(rawData ?? {});

      cosmosGraph.value.setPointPositions(payload.pointPositions);
      cosmosGraph.value.setLinks(payload.links);

      const shouldResume = respectSimulationState
        ? cosmosGraph.value.isSimulationRunning
        : !!props.autoStartForceAtlas;

      cosmosGraph.value.render(shouldResume ? 1 : 0);
      if (!shouldResume) {
        cosmosGraph.value.pause();
      }

      nodeIndexMeta.value = payload.nodeMeta;
      edgeIndexMeta.value = payload.edgeMeta;
      currentGraphData.value = payload.sanitized;

      emit("graphLoaded", currentGraphData.value);
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

        if (nodeIndexMeta.value.length) {
          cosmosGraph.value.fitView(0, 0.2);
        }
      } catch (error) {
        console.error("Error initializing Cosmos graph:", error);
      }
    };

    const pauseSimulation = () => {
      cosmosGraph.value?.pause();
      updateSimulationState();
    };

    const startSimulation = () => {
      cosmosGraph.value?.start(1);
      updateSimulationState();
    };

    const toggleSimulation = () => {
      const running = cosmosGraph.value?.isSimulationRunning ?? false;
      if (running) pauseSimulation();
      else startSimulation();
    };

    const applyCircularLayout = () => {
      if (!cosmosGraph.value || !nodeIndexMeta.value.length) return;

      pauseSimulation();

      const count = nodeIndexMeta.value.length;
      const radius = Math.max(
        150,
        Math.min(
          (cosmosContainer.value?.clientWidth ?? 600) * 0.45,
          (cosmosContainer.value?.clientHeight ?? 600) * 0.45,
        ),
      );
      const positions = new Float32Array(count * 2);

      for (let i = 0; i < count; i += 1) {
        const angle = (2 * Math.PI * i) / count;
        positions[i * 2] = Math.cos(angle) * radius;
        positions[i * 2 + 1] = Math.sin(angle) * radius;
      }

      cosmosGraph.value.setPointPositions(positions, true);
      cosmosGraph.value.render(0);
      cosmosGraph.value.fitView(400, 0.2);
      updateSimulationState();
    };

    const applyRandomLayout = () => {
      if (!cosmosGraph.value || !nodeIndexMeta.value.length) return;

      pauseSimulation();

      const width = cosmosContainer.value?.clientWidth ?? 600;
      const height = cosmosContainer.value?.clientHeight ?? 600;
      const positions = new Float32Array(nodeIndexMeta.value.length * 2);

      for (let i = 0; i < nodeIndexMeta.value.length; i += 1) {
        positions[i * 2] = (Math.random() - 0.5) * width;
        positions[i * 2 + 1] = (Math.random() - 0.5) * height;
      }

      cosmosGraph.value.setPointPositions(positions, true);
      cosmosGraph.value.render(0);
      cosmosGraph.value.fitView(400, 0.2);
      updateSimulationState();
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
        if (!cosmosGraph.value) return;
        if (auto) startSimulation();
        else pauseSimulation();
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
      toggleSimulation,
      applyCircularLayout,
      applyRandomLayout,
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
