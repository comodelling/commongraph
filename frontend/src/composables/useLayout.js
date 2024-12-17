// adapted from https://vueflow.dev/examples/layout/simple.html
import dagre from '@dagrejs/dagre'
import { Position, useVueFlow } from '@vue-flow/core'
import { ref } from 'vue'



/**
 * Composable to run the layout algorithm on the graph.
 * It uses the `dagre` library to calculate the layout of the nodes and edges.
 */
export function useLayout() {
  const { findNode } = useVueFlow()

  const graph = ref(new dagre.graphlib.Graph())

  const previousDirection = ref(localStorage.getItem('previousDirection') || 'LR')
  let targetPosition
  let sourcePosition

  function saveDirection(direction) {
    previousDirection.value = direction
    localStorage.setItem('previousDirection', direction)
  }

  function layoutSingleton(nodes, direction) {
    switch(direction) {
      case 'TB':
          targetPosition = Position.Top
          sourcePosition = Position.Bottom
          break
        case 'BT':
          targetPosition = Position.Bottom
          sourcePosition = Position.Top
          break
        case 'LR':
          targetPosition = Position.Left
          sourcePosition = Position.Right
          break
        case 'RL':
          targetPosition = Position.Right
          sourcePosition = Position.Left
          break
      }
    saveDirection(direction)
    return nodes.map((node) => {
      return {
        ...node,
        targetPosition: targetPosition,
        sourcePosition: sourcePosition,
      }
    })
  }

  function layout(nodes, edges, direction) {
    // we create a new graph instance, in case some nodes/edges were removed, otherwise dagre would act as if they were still there
    const dagreGraph = new dagre.graphlib.Graph()

    graph.value = dagreGraph

    dagreGraph.setDefaultEdgeLabel(() => ({}))

    let isHorizontal
    let targetPosition
    let sourcePosition
    switch (direction) {
      case 'TB':
        dagreGraph.setGraph({ rankdir: 'TB' })
        isHorizontal = false
        targetPosition = Position.Top
        sourcePosition = Position.Bottom
        break
      case 'BT':
        dagreGraph.setGraph({ rankdir: 'BT' })
        isHorizontal = false
        targetPosition = Position.Bottom
        sourcePosition = Position.Top
        break
      case 'LR':
        dagreGraph.setGraph({ rankdir: 'LR' })
        isHorizontal = true
        targetPosition = Position.Left
        sourcePosition = Position.Right
        break
      case 'RL':
        dagreGraph.setGraph({ rankdir: 'RL' })
        isHorizontal = true
        targetPosition = Position.Right
        sourcePosition = Position.Left
        break
    }
    dagreGraph.setGraph({ rankdir: direction })

    saveDirection(direction)

    for (const node of nodes) {
      // if you need width+height of nodes for your layout, you can use the dimensions property of the internal node (`GraphNode` type)
      const graphNode = findNode(node.id)

      dagreGraph.setNode(node.id, { width: graphNode.dimensions.width || 150, height: graphNode.dimensions.height || 50 })
    }

    for (const edge of edges) {
      dagreGraph.setEdge(edge.source, edge.target)
    }

    dagre.layout(dagreGraph)

    // set nodes with updated positions
    return nodes.map((node) => {
      const nodeWithPosition = dagreGraph.node(node.id)

      return {
        ...node,
        targetPosition: targetPosition,
        sourcePosition: sourcePosition,
        position: { x: nodeWithPosition.x, y: nodeWithPosition.y },
      }
    })
  }

  return { graph, layout, layoutSingleton, previousDirection }
}
