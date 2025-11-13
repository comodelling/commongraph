// adapted from https://vueflow.dev/examples/layout/simple.html
import dagre from "@dagrejs/dagre";
import { Position, useVueFlow } from "@vue-flow/core";
import { ref } from "vue";

/**
 * Composable to run the layout algorithm on the graph.
 * It uses the `dagre` library to calculate the layout of the nodes and edges.
 */
export function useLayout() {
  const { findNode } = useVueFlow();

  const graph = ref(new dagre.graphlib.Graph());

  const previousDirection = ref(
    localStorage.getItem("previousDirection") || "LR",
  );
  let targetPosition;
  let sourcePosition;

  function saveDirection(direction) {
    previousDirection.value = direction;
    localStorage.setItem("previousDirection", direction);
  }

  function affectDirection(nodes, direction) {
    console.log("affectDirection", direction);
    switch (direction) {
      case "TB":
        targetPosition = Position.Top;
        sourcePosition = Position.Bottom;
        break;
      case "BT":
        targetPosition = Position.Bottom;
        sourcePosition = Position.Top;
        break;
      case "LR":
        targetPosition = Position.Left;
        sourcePosition = Position.Right;
        break;
      case "RL":
        targetPosition = Position.Right;
        sourcePosition = Position.Left;
        break;
    }
    saveDirection(direction);
    return nodes.map((node) => {
      return {
        ...node,
        targetPosition: targetPosition,
        sourcePosition: sourcePosition,
      };
    });
  }

  function layout(nodes, edges, direction) {
    // we create a new graph instance, in case some nodes/edges were removed, otherwise dagre would act as if they were still there
    const dagreGraph = new dagre.graphlib.Graph();

    graph.value = dagreGraph;

    dagreGraph.setDefaultEdgeLabel(() => ({}));

    let isHorizontal;
    let targetPosition;
    let sourcePosition;
    switch (direction) {
      case "TB":
        dagreGraph.setGraph({ rankdir: "TB" });
        isHorizontal = false;
        targetPosition = Position.Top;
        sourcePosition = Position.Bottom;
        break;
      case "BT":
        dagreGraph.setGraph({ rankdir: "BT" });
        isHorizontal = false;
        targetPosition = Position.Bottom;
        sourcePosition = Position.Top;
        break;
      case "LR":
        dagreGraph.setGraph({ rankdir: "LR" });
        isHorizontal = true;
        targetPosition = Position.Left;
        sourcePosition = Position.Right;
        break;
      case "RL":
        dagreGraph.setGraph({ rankdir: "RL" });
        isHorizontal = true;
        targetPosition = Position.Right;
        sourcePosition = Position.Left;
        break;
    }
    // configure dagre graph with spacing options so nodes don't overlap
    // nodesep: minimum separation between nodes on the same rank
    // ranksep: separation between ranks (levels)
    // marginx/marginy: outer margin
    const NODE_SEP = 50;
    const RANK_SEP = 100;
    const MARGIN_X = 20;
    const MARGIN_Y = 20;

    dagreGraph.setGraph({
      rankdir: direction,
      nodesep: NODE_SEP,
      ranksep: RANK_SEP,
      marginx: MARGIN_X,
      marginy: MARGIN_Y,
    });

    saveDirection(direction);

    for (const node of nodes) {
      // if you need width+height of nodes for your layout, you can use the dimensions property of the internal node (`GraphNode` type)
      const graphNode = findNode(node.id);

      // fallback sizes are slightly increased to reduce accidental overlaps
      let width = 200;
      let height = 60;
      if (graphNode && graphNode.dimensions) {
        if (graphNode.dimensions.width && graphNode.dimensions.height) {
          width = graphNode.dimensions.width;
          height = graphNode.dimensions.height;
        } else {
          console.warn(
            `Node ${node.id} missing dimensions, using fallback size. Actual:`,
            graphNode.dimensions,
          );
        }
      } else {
        console.warn(
          `Node ${node.id} not found or missing dimensions, using fallback size.`,
        );
      }

      dagreGraph.setNode(node.id, { width, height });
    }

    for (const edge of edges) {
      dagreGraph.setEdge(edge.source, edge.target);
    }

    dagre.layout(dagreGraph);

    // set nodes with updated positions
    // dagre returns the node center coordinates; Vue Flow expects the top-left
    // corner as the node position. Convert by subtracting half the width/height.
    return nodes.map((node) => {
      const nodeWithPosition = dagreGraph.node(node.id) || {
        x: 0,
        y: 0,
        width: 0,
        height: 0,
      };
      const w = nodeWithPosition.width || 0;
      const h = nodeWithPosition.height || 0;

      return {
        ...node,
        targetPosition: targetPosition,
        sourcePosition: sourcePosition,
        position: {
          x: nodeWithPosition.x - w / 2,
          y: nodeWithPosition.y - h / 2,
        },
      };
    });
  }

  return { graph, layout, affectDirection, previousDirection };
}
