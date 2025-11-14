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
    <div v-if="hoveredNode" class="node-tooltip" :style="hoveredNodeStyle">
      <div class="node-tooltip-title">{{ hoveredNodeTitle }}</div>
      <div v-if="hoveredNodeSummary" class="node-tooltip-meta">
        {{ hoveredNodeSummary }}
      </div>
    </div>
    <div v-if="hoveredEdge" class="edge-tooltip" :style="hoveredEdgeStyle">
      <div class="edge-tooltip-title">{{ hoveredEdgeLabel }}</div>
      <div v-if="hoveredEdgeSummary" class="edge-tooltip-meta">
        {{ hoveredEdgeSummary }}
      </div>
    </div>
  </div>
</template>

<script>
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from "vue";
import { Graph as CosmosGraph } from "@cosmos.gl/graph";
import api from "../../api/axios";
import { useTheme } from "../../composables/useTheme";

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

const hexToRgba = (hex, alpha = 1) => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return [0.4, 0.4, 0.4, alpha]; // Fallback gray
  const r = parseInt(result[1], 16) / 255;
  const g = parseInt(result[2], 16) / 255;
  const b = parseInt(result[3], 16) / 255;
  return [r, g, b, alpha];
};

const computePointColorsBuffer = (
  nodeMeta,
  defaultColor,
  opacityForSearchResult = 1.0,
  opacityForOther = 0.4,
) => {
  const totalNodes = nodeMeta.length;
  const colors = new Float32Array(totalNodes * 4);
  const [r, g, b] = hexToRgba(defaultColor);

  nodeMeta.forEach((meta, index) => {
    const isSearchResult = meta.data?.isSearchResult ?? false;
    const alpha = isSearchResult ? opacityForSearchResult : opacityForOther;
    colors[index * 4] = r;
    colors[index * 4 + 1] = g;
    colors[index * 4 + 2] = b;
    colors[index * 4 + 3] = alpha;
  });

  return colors;
};

const computeLinkColorsBuffer = (
  edgeMeta,
  nodeMeta,
  defaultColor,
  opacityForSearchResult = 1.0,
  opacityForOther = 0.4,
) => {
  const totalEdges = edgeMeta.length;
  const colors = new Float32Array(totalEdges * 4);
  const [r, g, b] = hexToRgba(defaultColor);

  edgeMeta.forEach((edgeMeta, index) => {
    // An edge is considered part of search results if both endpoints are search results
    const sourceNode = nodeMeta[edgeMeta.sourceIndex];
    const targetNode = nodeMeta[edgeMeta.targetIndex];
    const sourceIsSearchResult = sourceNode?.data?.isSearchResult ?? false;
    const targetIsSearchResult = targetNode?.data?.isSearchResult ?? false;
    const isSearchResult = sourceIsSearchResult && targetIsSearchResult;
    const alpha = isSearchResult ? opacityForSearchResult : opacityForOther;

    colors[index * 4] = r;
    colors[index * 4 + 1] = g;
    colors[index * 4 + 2] = b;
    colors[index * 4 + 3] = alpha;
  });

  return colors;
};

const computePointSizesBuffer = (
  nodeMeta,
  baseSize = 8,
  searchResultSize = 9,
  otherSize = 8,
) => {
  const totalNodes = nodeMeta.length;
  const sizes = new Float32Array(totalNodes);

  nodeMeta.forEach((meta, index) => {
    const isSearchResult = meta.data?.isSearchResult ?? false;
    sizes[index] = isSearchResult ? searchResultSize : otherSize;
  });

  return sizes;
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
      default: "100%",
    },
    initialLayout: {
      type: String,
      default: "force",
      validator: (value) => ["force", "random"].includes(value),
    },
    edgeRestLengthFactor: {
      type: Number,
      default: 1.2,
    },
    edgeSpringStrength: {
      type: Number,
      default: 0.6,
    },
    nodeSeparation: {
      type: Number,
      default: 32,
    },
    initialDirectionMode: {
      type: String,
      default: "LR",
      validator: (value) => ["LR", "RL", "TB", "BT", "NONE"].includes(value),
    },
    opacityMode: {
      type: String,
      default: "filter",
      validator: (value) => ["filter", "uniform"].includes(value),
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
    const selectionSource = ref(null);
    const hoveredNode = ref(null);
    const hoveredEdge = ref(null);
    const latestPointPositions = ref(new Float32Array(0));
    const lastMousePosition = ref({ x: 0, y: 0 });
    const normalizeLayout = (layout) =>
      ["force", "random"].includes(layout) ? layout : "force";
    const getStoredDirection = () => {
      if (typeof window === "undefined") return null;
      return localStorage.getItem("previousDirection");
    };

    const normalizeDirection = (direction) =>
      ["LR", "RL", "TB", "BT", "NONE"].includes(direction) ? direction : "LR";
    const layoutMode = ref(normalizeLayout(props.initialLayout));
    const directionMode = ref(
      normalizeDirection(
        getStoredDirection() ?? props.initialDirectionMode ?? "LR",
      ),
    );
    let lastFetchId = 0;

    // Theme reactivity
    const { isDark } = useTheme();

    const refreshDirectionMode = () => {
      const stored = getStoredDirection();
      if (stored) {
        directionMode.value = normalizeDirection(stored);
      }
    };

    const getSpacePositionForIndex = (index) => {
      if (typeof index !== "number" || index < 0) return null;
      const positions = latestPointPositions.value;
      if (!positions || positions.length < (index + 1) * 2) return null;
      return [positions[index * 2], positions[index * 2 + 1]];
    };

    const convertSpaceToScreen = (spacePosition) => {
      if (!cosmosGraph.value || !spacePosition) return null;
      const projector = cosmosGraph.value.spaceToScreenPosition;
      if (typeof projector !== "function") return null;
      try {
        const result = projector(spacePosition);
        if (Array.isArray(result) && result.length >= 2) {
          return result;
        }
        if (
          typeof result?.length === "number" &&
          result.length >= 2 &&
          typeof result[0] === "number"
        ) {
          return [result[0], result[1]];
        }
      } catch (error) {
        return null;
      }
      return null;
    };

    const mapScreenToContainer = (screenPosition) => {
      if (!screenPosition || !cosmosContainer.value) return null;
      const rect = cosmosContainer.value.getBoundingClientRect();
      if (!rect.width || !rect.height) return null;
      const canvas = cosmosContainer.value.querySelector("canvas");
      const canvasWidth = canvas?.width ?? rect.width;
      const canvasHeight = canvas?.height ?? rect.height;
      const ratioX = canvasWidth / rect.width;
      const ratioY = canvasHeight / rect.height;

      const [screenX, screenY] = screenPosition;

      const adjustedX = rect.width / 2 + screenX / ratioX;
      const adjustedY = rect.height / 2 - screenY / ratioY;

      return {
        x: adjustedX,
        y: adjustedY,
      };
    };

    const computeScreenCoordsForIndex = (index, pointPosition) => {
      if (!cosmosGraph.value || !cosmosContainer.value) return null;

      let spacePosition = null;
      if (
        pointPosition &&
        typeof pointPosition.length === "number" &&
        pointPosition.length >= 2
      ) {
        spacePosition = [pointPosition[0], pointPosition[1]];
      }

      if (!spacePosition) {
        spacePosition = getSpacePositionForIndex(index);
      }

      if (!spacePosition && cosmosGraph.value?.getPointPositions) {
        try {
          const currentPositions = cosmosGraph.value.getPointPositions();
          if (currentPositions && currentPositions.length >= (index + 1) * 2) {
            latestPointPositions.value = new Float32Array(currentPositions);
            spacePosition = [
              currentPositions[index * 2],
              currentPositions[index * 2 + 1],
            ];
          }
        } catch (error) {
          spacePosition = null;
        }
      }

      if (!spacePosition) return null;

      const screenPosition = convertSpaceToScreen(spacePosition);
      return mapScreenToContainer(screenPosition);
    };

    const resolveNodeTitle = (meta) => {
      if (!meta) return "";
      const data = meta.data ?? {};
      return data.title ?? data.label ?? data.name ?? meta.id ?? "";
    };

    const destroyGraph = () => {
      clearNodeHover();
      clearLinkHighlight();
      cosmosGraph.value?.destroy();
      cosmosGraph.value = null;
      nodeIndexMeta.value = [];
      edgeIndexMeta.value = [];
      currentGraphData.value = { nodes: [], edges: [] };
      graphState.value = null;
      latestPointPositions.value = new Float32Array(0);
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

    // Lay out nodes inside a connected component with configurable direction (mirrors FlowEditor dagre defaults).
    const computeComponentLayout = (component, state, direction) => {
      if (direction === "NONE") {
        const count = component.length;
        const radius = Math.max(140, Math.sqrt(count) * 65);
        const positions = new Map();
        component.forEach((nodeIndex, index) => {
          if (count === 1) {
            positions.set(nodeIndex, { x: 0, y: 0 });
            return;
          }
          const angle = (2 * Math.PI * index) / count;
          positions.set(nodeIndex, {
            x: Math.cos(angle) * radius,
            y: Math.sin(angle) * radius,
          });
        });

        return {
          positions,
          centerX: 0,
          centerY: 0,
          width: radius * 2,
          height: radius * 2,
        };
      }

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
      const basePositions = new Map();

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
          basePositions.set(nodeIndex, { x, y });
        });
      });

      const isHorizontal = direction === "LR" || direction === "RL";
      const invertPrimary = direction === "RL" || direction === "BT";

      const orientedPositions = new Map();

      basePositions.forEach((pos, nodeIndex) => {
        let x = pos.x;
        let y = pos.y;

        if (!isHorizontal) {
          const temp = x;
          x = y;
          y = temp;
        }

        if (invertPrimary) {
          x *= -1;
        }

        orientedPositions.set(nodeIndex, { x, y });
      });

      let minX = Infinity;
      let maxX = -Infinity;
      let minY = Infinity;
      let maxY = -Infinity;

      orientedPositions.forEach((pos) => {
        if (pos.x < minX) minX = pos.x;
        if (pos.x > maxX) maxX = pos.x;
        if (pos.y < minY) minY = pos.y;
        if (pos.y > maxY) maxY = pos.y;
      });

      const centerX = (minX + maxX) / 2;
      const centerY = (minY + maxY) / 2;
      const width = Math.max(maxX - minX, 1);
      const height = Math.max(maxY - minY, 1);

      return {
        positions: orientedPositions,
        centerX,
        centerY,
        width,
        height,
      };
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

        const layout = computeComponentLayout(
          component,
          state,
          directionMode.value,
        );
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

    // Native Cosmos GL simulation handles force layout now.
    // This function is kept for reference but no longer used.
    const runStaticForceLayout = (state, containerSize) => {
      // Delegate to directional seeding; GPU will simulate from here
      return generateForceSeedPositions(state, containerSize);
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

    const highlightLinkNodes = (edgeMeta) => {
      if (!edgeMeta || !cosmosGraph.value) return;
      clearNodeHover();
      const indices = [];
      if (
        typeof edgeMeta.sourceIndex === "number" &&
        Number.isFinite(edgeMeta.sourceIndex)
      ) {
        indices.push(edgeMeta.sourceIndex);
      }
      if (
        typeof edgeMeta.targetIndex === "number" &&
        Number.isFinite(edgeMeta.targetIndex)
      ) {
        indices.push(edgeMeta.targetIndex);
      }
      if (!indices.length) return;
      cosmosGraph.value.selectPointsByIndices(indices);
      selectionSource.value = "link";
    };

    const clearLinkHighlight = () => {
      hoveredEdge.value = null;
      if (selectionSource.value === "link") {
        cosmosGraph.value?.unselectPoints();
        selectionSource.value = null;
      }
    };

    const handleLinkMouseOver = (index) => {
      const edgeMeta = edgeIndexMeta.value[index];
      if (!edgeMeta) return;
      highlightLinkNodes(edgeMeta);

      // Use the last known mouse position
      let position = lastMousePosition.value
        ? { x: lastMousePosition.value.x, y: lastMousePosition.value.y }
        : null;

      if (!position && cosmosContainer.value) {
        position = {
          x: cosmosContainer.value.clientWidth / 2,
          y: cosmosContainer.value.clientHeight / 2,
        };
      }

      hoveredEdge.value = {
        index,
        id: edgeMeta.id,
        data: edgeMeta.data ?? {},
        sourceIndex: edgeMeta.sourceIndex,
        targetIndex: edgeMeta.targetIndex,
        screenX: position?.x ?? 0,
        screenY: position?.y ?? 0,
      };
    };

    const handleLinkMouseOut = () => {
      clearLinkHighlight();
    };

    const clearNodeHover = () => {
      if (selectionSource.value === "node") {
        cosmosGraph.value?.unselectPoints();
      }
      hoveredNode.value = null;
      if (selectionSource.value === "node") {
        selectionSource.value = null;
      }
    };

    const handlePointMouseOver = (index, pointPosition, event) => {
      const meta = nodeIndexMeta.value[index];
      if (!meta || !cosmosGraph.value || !cosmosContainer.value) return;

      hoveredEdge.value = null;

      let containerCoords = null;
      if (event?.clientX !== undefined && event?.clientY !== undefined) {
        const rect = cosmosContainer.value.getBoundingClientRect();
        containerCoords = {
          x: event.clientX - rect.left,
          y: event.clientY - rect.top,
        };
      }

      if (!containerCoords) {
        containerCoords = computeScreenCoordsForIndex(index, pointPosition);
      }

      if (!containerCoords) {
        return;
      }

      cosmosGraph.value.selectPointsByIndices([index]);
      selectionSource.value = "node";

      hoveredNode.value = {
        index,
        id: meta.id,
        data: meta.data ?? {},
        screenX: containerCoords.x,
        screenY: containerCoords.y,
      };
    };

    const handlePointMouseOut = () => {
      clearNodeHover();
    };

    const handlePointClick = (index) => {
      const meta = nodeIndexMeta.value[index];
      if (!meta) return;
      emit("nodeClick", meta.id);
    };

    const buildEdgePayload = (edgeMeta) => {
      if (!edgeMeta) return null;
      const sourceMeta = nodeIndexMeta.value[edgeMeta.sourceIndex];
      const targetMeta = nodeIndexMeta.value[edgeMeta.targetIndex];
      const data = edgeMeta.data ?? {};
      const sourceId = sourceMeta?.id ?? data.source_id ?? data.source ?? null;
      const targetId = targetMeta?.id ?? data.target_id ?? data.target ?? null;

      return {
        id: edgeMeta.id,
        sourceId,
        targetId,
        data,
      };
    };

    const handleLinkClick = (index) => {
      const meta = edgeIndexMeta.value[index];
      if (!meta) return;
      highlightLinkNodes(meta);
      const payload = buildEdgePayload(meta);
      emit("edgeClick", payload ?? meta.id);
    };

    const buildConfig = () => ({
      backgroundColor: getCssVariable("--background-color", "#ffffff"),
      pointColor: DEFAULT_NODE_COLOR,
      pointSize: 8,
      linkColor: getCssVariable("--border-color", DEFAULT_LINK_COLOR),
      linkWidth: 1.5,
      curvedLinks: true,
      enableSimulation: true,
      simulationLinkSpring: 0.6,
      simulationRepulsion: 280,
      simulationLinkDistance: 65,
      simulationFriction: 0.82,
      enableZoom: true,
      enableDrag: true,
      rescalePositions: false,
      fitViewOnInit: false,
      fitViewPadding: 0.2,
      hoveredPointCursor: "pointer",
      hoveredLinkCursor: "pointer",
      hoveredLinkColor: getCssVariable("--highlight-color", "#ffcc66"),
      hoveredLinkWidthIncrease: 2.5,
      renderHoveredPointRing: true,
      hoveredPointRingColor: getCssVariable("--highlight-color", "#ffcc66"),
      enableRightClickRepulsion: false,
      linkArrows: true,
      onPointClick: handlePointClick,
      onPointMouseOver: handlePointMouseOver,
      onPointMouseOut: handlePointMouseOut,
      onLinkClick: handleLinkClick,
      onLinkMouseOver: handleLinkMouseOver,
      onLinkMouseOut: handleLinkMouseOut,
    });

    const applyGraphData = (rawData, { respectSimulationState } = {}) => {
      if (!cosmosGraph.value) return;

      const state = buildGraphState(rawData ?? {});
      graphState.value = state;

      const containerSize = {
        width: cosmosContainer.value?.clientWidth ?? 800,
        height: cosmosContainer.value?.clientHeight ?? 600,
      };

      clearNodeHover();
      clearLinkHighlight();
      refreshDirectionMode();
      const positions = computePositions(
        state,
        layoutMode.value,
        containerSize,
      );

      latestPointPositions.value = new Float32Array(positions);

      cosmosGraph.value.setPointPositions(positions, true);
      cosmosGraph.value.setLinks(state.links);

      // Determine opacity settings based on opacityMode
      const opacitySettings =
        props.opacityMode === "uniform"
          ? { searchResultOpacity: 1.0, otherOpacity: 1.0 }
          : { searchResultOpacity: 1.0, otherOpacity: 0.4 };

      // Apply per-node and per-edge colors based on search result status
      const pointColors = computePointColorsBuffer(
        state.nodeMeta,
        DEFAULT_NODE_COLOR,
        opacitySettings.searchResultOpacity,
        opacitySettings.otherOpacity,
      );
      cosmosGraph.value.setPointColors(pointColors);

      // Apply per-node sizes
      const pointSizes = computePointSizesBuffer(state.nodeMeta);
      cosmosGraph.value.setPointSizes(pointSizes);

      const linkColors = computeLinkColorsBuffer(
        state.edgeMeta,
        state.nodeMeta,
        DEFAULT_LINK_COLOR,
        opacitySettings.searchResultOpacity,
        opacitySettings.otherOpacity,
      );
      cosmosGraph.value.setLinkColors(linkColors);

      cosmosGraph.value.render(0);

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

      // Allow native simulation to run for force layout, pause otherwise
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

      clearNodeHover();
      clearLinkHighlight();
      refreshDirectionMode();
      const positions = computePositions(
        graphState.value,
        normalized,
        containerSize,
      );

      latestPointPositions.value = new Float32Array(positions);

      cosmosGraph.value.setPointPositions(positions, true);

      // Determine opacity settings based on opacityMode
      const opacitySettings =
        props.opacityMode === "uniform"
          ? { searchResultOpacity: 1.0, otherOpacity: 1.0 }
          : { searchResultOpacity: 1.0, otherOpacity: 0.4 };

      // Reapply colors when layout changes
      const pointColors = computePointColorsBuffer(
        nodeIndexMeta.value,
        DEFAULT_NODE_COLOR,
        opacitySettings.searchResultOpacity,
        opacitySettings.otherOpacity,
      );
      cosmosGraph.value.setPointColors(pointColors);

      // Reapply point sizes
      const pointSizes = computePointSizesBuffer(nodeIndexMeta.value);
      cosmosGraph.value.setPointSizes(pointSizes);

      const linkColors = computeLinkColorsBuffer(
        edgeIndexMeta.value,
        nodeIndexMeta.value,
        DEFAULT_LINK_COLOR,
        opacitySettings.searchResultOpacity,
        opacitySettings.otherOpacity,
      );
      cosmosGraph.value.setLinkColors(linkColors);

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

    const reinitializeGraphWithCurrentData = async () => {
      await nextTick();
      if (!cosmosContainer.value || !currentGraphData.value) return;

      // Save current data before destroying
      const savedData = {
        nodes: [...(currentGraphData.value.nodes ?? [])],
        edges: [...(currentGraphData.value.edges ?? [])],
      };

      destroyGraph();

      if (!cosmosContainer.value) return;

      cosmosGraph.value = new CosmosGraph(cosmosContainer.value, buildConfig());

      applyGraphData(savedData, { respectSimulationState: false });
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

    // Watch for theme changes and reinitialize graph
    watch(
      () => isDark.value,
      async () => {
        if (!cosmosGraph.value || !currentGraphData.value) return;
        // Reinitialize with new theme colors, preserving current data
        await reinitializeGraphWithCurrentData();
      },
    );

    onMounted(() => {
      initializeGraph();

      // Track mouse position for edge tooltips
      const handleMouseMove = (event) => {
        if (cosmosContainer.value) {
          const rect = cosmosContainer.value.getBoundingClientRect();
          lastMousePosition.value = {
            x: event.clientX - rect.left,
            y: event.clientY - rect.top,
          };
        }
      };

      if (cosmosContainer.value) {
        cosmosContainer.value.addEventListener("mousemove", handleMouseMove);
      }
    });

    onBeforeUnmount(() => {
      destroyGraph();
    });

    const hoveredNodeTitle = computed(() => {
      if (!hoveredNode.value) return "";
      const data = hoveredNode.value.data ?? {};
      return data.title ?? data.label ?? hoveredNode.value.id ?? "";
    });

    const hoveredNodeStyle = computed(() => {
      if (!hoveredNode.value) return {};
      const offsetX = 14;
      const offsetY = -18;
      const top = Math.max(hoveredNode.value.screenY + offsetY, 0);
      const left = Math.max(hoveredNode.value.screenX + offsetX, 0);
      return {
        top: `${top}px`,
        left: `${left}px`,
      };
    });

    const hoveredNodeSummary = computed(() => {
      if (!hoveredNode.value) return "";
      const data = hoveredNode.value.data ?? {};
      const status = data.status ?? data.node_status ?? null;
      const type = data.node_type ?? data.type ?? null;
      const scope = data.scope ?? null;
      const ratingLabel = data.ratingLabel ?? null;
      const ratingValue = data.support ?? null;

      const parts = [];
      if (status) {
        parts.push(status);
      }
      if (type) {
        parts.push(type);
      }

      let summary = parts.join(" ");
      if (scope) {
        summary = summary ? `${summary} (${scope})` : `(${scope})`;
      }

      if (ratingLabel) {
        let formattedRating = "none";
        if (ratingValue != null) {
          formattedRating =
            typeof ratingValue === "number"
              ? Number(ratingValue).toFixed(2).replace(/\.00$/, "")
              : ratingValue;
        }
        const ratingLine = `median ${ratingLabel}: ${formattedRating}`;
        summary = summary ? `${summary}\n${ratingLine}` : ratingLine;
      }

      return summary;
    });

    const hoveredEdgeLabel = computed(() => {
      if (!hoveredEdge.value) return "";
      const data = hoveredEdge.value.data ?? {};
      return data.title ?? data.edge_type ?? data.type ?? "Implication";
    });

    const hoveredEdgeSummary = computed(() => {
      const edge = hoveredEdge.value;
      if (!edge) return "";

      const sourceMeta =
        typeof edge.sourceIndex === "number"
          ? nodeIndexMeta.value[edge.sourceIndex]
          : null;
      const targetMeta =
        typeof edge.targetIndex === "number"
          ? nodeIndexMeta.value[edge.targetIndex]
          : null;

      const sourceTitle = resolveNodeTitle(sourceMeta) || "Source";
      const targetTitle = resolveNodeTitle(targetMeta) || "Target";
      const ratingLabel = edge.data?.ratingLabel ?? null;
      const ratingValue = edge.data?.causal_strength ?? null;

      let summary = `${sourceTitle} → ${targetTitle}`;

      if (ratingLabel) {
        let formattedRating = "none";
        if (ratingValue != null) {
          formattedRating =
            typeof ratingValue === "number"
              ? Number(ratingValue).toFixed(2).replace(/\.00$/, "")
              : ratingValue;
        }
        summary = `${summary}\nmedian ${ratingLabel}: ${formattedRating}`;
      }

      return summary;
    });

    const hoveredEdgeStyle = computed(() => {
      if (!hoveredEdge.value) return {};
      const offsetX = 12;
      const offsetY = -12;
      const top = Math.max(hoveredEdge.value.screenY + offsetY, 0);
      const left = Math.max(hoveredEdge.value.screenX + offsetX, 0);
      return {
        top: `${top}px`,
        left: `${left}px`,
      };
    });

    return {
      cosmosContainer,
      layoutMode,
      applyForceLayout,
      applyRandomLayout,
      hoveredNode,
      hoveredNodeTitle,
      hoveredNodeStyle,
      hoveredNodeSummary,
      hoveredEdge,
      hoveredEdgeLabel,
      hoveredEdgeSummary,
      hoveredEdgeStyle,
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

/* GraphVis tooltips use absolute positioning within the container */
.node-tooltip,
.edge-tooltip {
  position: absolute !important;
  z-index: 12;
}
</style>
