<template>
  <div class="cosmos-graph-container">
    <div ref="cosmosContainer" class="cosmos-container"></div>
    <div class="controls" v-if="showControls">
      <button
        @click="applyForceLayout"
        :class="['control-button', { active: layoutMode === 'force' }]"
      >
        Force Layout
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

const deterministicNoise = (index, axis = 0) => {
  const seed = Math.sin(index * 12.9898 + axis * 78.233) * 43758.5453;
  return seed - Math.floor(seed);
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
    height: {
      type: String,
      default: "400px",
    },
    initialLayout: {
      type: String,
      default: "force",
      validator: (value) => ["force", "random"].includes(value),
    },
  },
  emits: ["nodeClick", "edgeClick", "graphLoaded"],
  setup(props, { emit }) {
    const cosmosContainer = ref(null);
    const cosmosGraph = ref(null);
    const nodeIndexMeta = ref([]);
    const edgeIndexMeta = ref([]);
    const currentGraphData = ref({ nodes: [], edges: [] });
    const graphState = ref(null);
    const normalizeLayout = (layout) =>
      ["force", "random"].includes(layout) ? layout : "force";
    const layoutMode = ref(normalizeLayout(props.initialLayout));
    let lastFetchId = 0;

    const destroyGraph = () => {
      cosmosGraph.value?.destroy();
      cosmosGraph.value = null;
      nodeIndexMeta.value = [];
      edgeIndexMeta.value = [];
      currentGraphData.value = { nodes: [], edges: [] };
      graphState.value = null;
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

    // Lay out nodes inside a connected component left-to-right, similar to the dagre setup in FlowEditor.
    const computeComponentDirectionalLayout = (component, state) => {
      const nodesInComponent = new Set(component);
      const inDegree = new Map();

      component.forEach((nodeIndex) => {
        inDegree.set(nodeIndex, 0);
      });

      component.forEach((nodeIndex) => {
        const outgoing = state.adjacency.out.get(nodeIndex);
        if (!outgoing) return;
        outgoing.forEach((target) => {
          if (!nodesInComponent.has(target)) return;
          inDegree.set(target, (inDegree.get(target) ?? 0) + 1);
        });
      });

      const queue = [];
      component.forEach((nodeIndex) => {
        if ((inDegree.get(nodeIndex) ?? 0) === 0) {
          queue.push(nodeIndex);
        }
      });

      const visitOrder = [];
      const levelMap = new Map();

      while (queue.length) {
        const nodeIndex = queue.shift();
        visitOrder.push(nodeIndex);
        const level = levelMap.get(nodeIndex) ?? 0;

        const outgoing = state.adjacency.out.get(nodeIndex);
        if (!outgoing) continue;
        outgoing.forEach((target) => {
          if (!nodesInComponent.has(target)) return;
          const nextLevel = Math.max(level + 1, levelMap.get(target) ?? 0);
          levelMap.set(target, nextLevel);
          const remaining = (inDegree.get(target) ?? 0) - 1;
          inDegree.set(target, remaining);
          if (remaining === 0) {
            queue.push(target);
          }
        });
      }

      if (visitOrder.length < component.length) {
        let fallbackLevel = Math.max(0, ...Array.from(levelMap.values()));
        component.forEach((nodeIndex) => {
          if (!levelMap.has(nodeIndex)) {
            fallbackLevel += 1;
            levelMap.set(nodeIndex, fallbackLevel);
          }
        });
      }

      const bucketMap = new Map();
      component.forEach((nodeIndex) => {
        const level = levelMap.get(nodeIndex) ?? 0;
        const bucket = bucketMap.get(level);
        if (bucket) bucket.push(nodeIndex);
        else bucketMap.set(level, [nodeIndex]);
      });

      const sortedLevels = Array.from(bucketMap.keys()).sort((a, b) => a - b);
      const levelSpacing = Math.max(220, Math.sqrt(component.length) * 110);
      const positions = new Map();

      sortedLevels.forEach((levelValue, order) => {
        const nodesAtLevel = bucketMap.get(levelValue) ?? [];
        const verticalSpacing = Math.max(
          120,
          Math.sqrt(nodesAtLevel.length) * 90,
        );
        const offset = (nodesAtLevel.length - 1) / 2;

        nodesAtLevel.forEach((nodeIndex, index) => {
          const x = order * levelSpacing;
          const y = (index - offset) * verticalSpacing;
          positions.set(nodeIndex, { x, y });
        });
      });

      let minX = Infinity;
      let maxX = -Infinity;
      let minY = Infinity;
      let maxY = -Infinity;

      positions.forEach((pos) => {
        if (pos.x < minX) minX = pos.x;
        if (pos.x > maxX) maxX = pos.x;
        if (pos.y < minY) minY = pos.y;
        if (pos.y > maxY) maxY = pos.y;
      });

      const centerX = (minX + maxX) / 2;
      const centerY = (minY + maxY) / 2;
      const width = Math.max(maxX - minX, 1);
      const height = Math.max(maxY - minY, 1);

      return { positions, centerX, centerY, width, height };
    };

    const generateForceSeedPositions = (state, containerSize) => {
      const total = state.totalNodes;
      const positions = new Float32Array(total * 2);
      if (!total) return positions;

      const components = computeConnectedComponents(state);
      const width = containerSize?.width ?? 800;
      const height = containerSize?.height ?? 600;
      const maxDimension = Math.max(width, height);
      const baseRadius = Math.min(
        Math.max(220, Math.sqrt(total) * 80),
        maxDimension * 0.45,
      );
      const goldenAngle = Math.PI * (3 - Math.sqrt(5));
      const maxAllowedWidth = maxDimension * 0.75;
      const maxAllowedHeight = maxDimension * 0.65;

      components.forEach((component, componentIndex) => {
        const spiralRadius = baseRadius * Math.sqrt(componentIndex + 0.75);
        const angle = componentIndex * goldenAngle;
        const cx = Math.cos(angle) * spiralRadius;
        const cy = Math.sin(angle) * spiralRadius;

        if (component.length === 1) {
          const nodeIndex = component[0];
          positions[nodeIndex * 2] = cx;
          positions[nodeIndex * 2 + 1] = cy;
          return;
        }

        const layout = computeComponentDirectionalLayout(component, state);
        const scale = Math.min(
          1.4,
          maxAllowedWidth / Math.max(layout.width, 1),
          maxAllowedHeight / Math.max(layout.height, 1),
        );

        layout.positions.forEach((pos, nodeIndex) => {
          const jitterStrength = 18;
          const jitterX =
            (deterministicNoise(nodeIndex, componentIndex) - 0.5) *
            2 *
            jitterStrength;
          const jitterY =
            (deterministicNoise(nodeIndex, componentIndex + 1) - 0.5) *
            2 *
            jitterStrength;
          positions[nodeIndex * 2] =
            cx + (pos.x - layout.centerX) * scale + jitterX;
          positions[nodeIndex * 2 + 1] =
            cy + (pos.y - layout.centerY) * scale + jitterY;
        });
      });

      return positions;
    };

    const runStaticForceLayout = (state, containerSize) => {
      const total = state.totalNodes;
      if (!total) return new Float32Array(0);

      const seeded = generateForceSeedPositions(state, containerSize);
      const working = new Float32Array(seeded);
      const dx = new Float32Array(total);
      const dy = new Float32Array(total);

      const width = containerSize?.width ?? 800;
      const height = containerSize?.height ?? 600;
      const area = Math.max(width * height, 1);
      const k = Math.sqrt(area / Math.max(total, 1));
      const iterations = Math.max(60, Math.min(200, total * 6));
      let temperature = Math.min(width, height) * 0.25;

      const attractiveEdges = state.edgeMeta ?? [];

      for (let iter = 0; iter < iterations; iter += 1) {
        dx.fill(0);
        dy.fill(0);

        for (let i = 0; i < total; i += 1) {
          for (let j = i + 1; j < total; j += 1) {
            const deltaX = working[i * 2] - working[j * 2];
            const deltaY = working[i * 2 + 1] - working[j * 2 + 1];
            const distance = Math.max(Math.hypot(deltaX, deltaY), 0.01);
            const force = (k * k) / distance;
            const fx = (deltaX / distance) * force;
            const fy = (deltaY / distance) * force;

            dx[i] += fx;
            dy[i] += fy;
            dx[j] -= fx;
            dy[j] -= fy;
          }
        }

        attractiveEdges.forEach((edge) => {
          const source = edge.sourceIndex;
          const target = edge.targetIndex;
          if (
            source === undefined ||
            target === undefined ||
            source === target
          ) {
            return;
          }

          const deltaX = working[source * 2] - working[target * 2];
          const deltaY = working[source * 2 + 1] - working[target * 2 + 1];
          const distance = Math.max(Math.hypot(deltaX, deltaY), 0.01);
          const force = (distance * distance) / k;
          const fx = (deltaX / distance) * force;
          const fy = (deltaY / distance) * force;

          dx[source] -= fx;
          dy[source] -= fy;
          dx[target] += fx;
          dy[target] += fy;
        });

        for (let i = 0; i < total; i += 1) {
          const disp = Math.hypot(dx[i], dy[i]);
          if (!disp) continue;
          const limited = Math.min(disp, temperature);
          working[i * 2] += (dx[i] / disp) * limited;
          working[i * 2 + 1] += (dy[i] / disp) * limited;
        }

        temperature *= 0.92;
      }

      let minX = Infinity;
      let maxX = -Infinity;
      let minY = Infinity;
      let maxY = -Infinity;

      for (let i = 0; i < total; i += 1) {
        const x = working[i * 2];
        const y = working[i * 2 + 1];
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }

      const layoutWidth = Math.max(maxX - minX, 1);
      const layoutHeight = Math.max(maxY - minY, 1);
      const centerX = (minX + maxX) / 2;
      const centerY = (minY + maxY) / 2;
      const marginRatio = 0.02;
      const availableWidth = Math.max(width * (1 - marginRatio * 2), 200);
      const availableHeight = Math.max(height * (1 - marginRatio * 2), 200);
      const scaleX = availableWidth / layoutWidth;
      const scaleY = availableHeight / layoutHeight;

      const result = new Float32Array(total * 2);
      for (let i = 0; i < total; i += 1) {
        result[i * 2] = (working[i * 2] - centerX) * scaleX;
        result[i * 2 + 1] = (working[i * 2 + 1] - centerY) * scaleY;
      }

      return result;
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
        case "random":
          return generateRandomPositions(state, containerSize);
        case "force":
        default:
          return runStaticForceLayout(state, containerSize);
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
      enableSimulation: false,
      enableZoom: true,
      enableDrag: true,
      rescalePositions: false,
      fitViewOnInit: false,
      fitViewPadding: 0.2,
      hoveredPointCursor: "pointer",
      hoveredLinkCursor: "pointer",
      enableRightClickRepulsion: false,
      linkArrows: true,
      onPointClick: handlePointClick,
      onLinkClick: handleLinkClick,
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

      cosmosGraph.value.render(0);
      cosmosGraph.value.pause?.();

      nodeIndexMeta.value = state.nodeMeta;
      edgeIndexMeta.value = state.edgeMeta;
      currentGraphData.value = {
        nodes: state.nodes,
        edges: state.edges,
      };

      emit("graphLoaded", currentGraphData.value);

      if (state.totalNodes) {
        cosmosGraph.value.fitView(200, 0.06);
      }

      if (layoutMode.value !== "force") {
        cosmosGraph.value?.pause?.();
      }
    };

    const applyLayout = (mode) => {
      const normalized = normalizeLayout(mode);
      layoutMode.value = normalized;
      if (!cosmosGraph.value || !graphState.value) return;

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
        cosmosGraph.value.fitView(200, 0.06);
      }

      if (normalized !== "force") {
        cosmosGraph.value?.pause?.();
      }
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

    const applyForceLayout = () => {
      applyLayout("force");
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
      layoutMode,
      applyForceLayout,
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

.control-button.active {
  font-weight: 600;
  border-color: var(--text-color);
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
