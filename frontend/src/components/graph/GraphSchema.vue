<template>
  <div class="schema-page" id="schema-container">
    <div id="container"></div>
    <div id="tooltip" class="tooltip"></div>
  </div>
</template>

<script lang="ts">
import { onMounted, onBeforeUnmount } from "vue";
import { useConfig } from "../../composables/useConfig";
import api from "../../api/axios";
import Graph from "graphology";
import Sigma from "sigma";

export default {
  name: "GraphSchema",
  setup() {
    let renderer: Sigma;
    const { load, nodeTypes, getNodePolls } = useConfig();

    onMounted(async () => {
      await load();
      const graph = new Graph({ type: "directed", multi: true });

      // Compute text color from CSS variable:
      const computedLabelColor =
        getComputedStyle(document.body)
          .getPropertyValue("--text-color")
          .trim() || "#000";

      // 1) fetch schema
      const { data } = await api.get("/graph/schema");
      const types: string[] = data.node_types;
      const relations: {
        source_type: string;
        target_type: string;
        label: string;
      }[] = data.edge_types;

      // 2) add nodes in a circle
      const N = types.length;
      types.forEach((t, i) => {
        const angle = (2 * Math.PI * i) / N;
        graph.addNode(t, {
          label: t,
          x: Math.cos(angle),
          y: Math.sin(angle),
          size: 20,
          color: "#66ccff",
          // labelColor: "red"
          labelColor: computedLabelColor,
          nodeType: t
        });
      });

      // 3) add directed edges with type "arrow"
      relations.forEach((r, i) => {
        graph.addEdgeWithKey(
          `${r.label}-${i}`,
          r.source_type,
          r.target_type,
          {
            label: r.label,
            size: 4,
            // color: "#999",
            type: "arrow",
            // labelColor: computedLabelColor
          }
        );
      });

      // 4) mount Sigma using its built-in settings.
      // Passing defaultLabelColor ensures node labels adapt to the theme.
      renderer = new Sigma(
        graph,
        document.getElementById("container") as HTMLDivElement,
        {
          defaultNodeType: "circle",
          defaultEdgeType: "arrow",
          renderEdgeLabels: true,
          labelColor: { attribute: "labelColor", color: computedLabelColor },
          edgeLabelColor: { attribute: "labelColor", color: computedLabelColor },
          // defaultLabelColor: computedLabelColor,
        }
      );
      // Attach hover tooltip for nodes showing properties and polls
      const tooltip = document.getElementById("tooltip") as HTMLDivElement;
      renderer.on("enterNode", ({ node, event }) => {
        const type = graph.getNodeAttribute(node, "nodeType");
        const props = nodeTypes.value[type].properties || {};
        const polls = Object.keys(getNodePolls(type));
        const html = `<strong>${type}</strong><br/>Properties: ${props.length? props.join(", "): "None"}<br/>Polls: ${polls.length? polls.join(", "): "None"}`;
        tooltip.innerHTML = html;
        tooltip.style.display = "block";
        // compute position ensuring tooltip stays within viewport
        const rect = tooltip.getBoundingClientRect();
        let x = event.x;
        let y = event.y;
        if (x + rect.width > window.innerWidth) {
          x = window.innerWidth - rect.width - 10;
        }
        if (y + rect.height > window.innerHeight) {
          y = event.y - rect.height - 10;
        }
        tooltip.style.left = `${x}px`;
        tooltip.style.top = `${y}px`;
      });
      renderer.on("leaveNode", () => {
        tooltip.style.display = "none";
      });
    });

    onBeforeUnmount(() => {
      if (renderer) renderer.kill();
    });

    return {};
  },
};
</script>

<style scoped>
.schema-page,
#container {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden;
  background-color: var(--background-color);
  /* color: var(--text-color); */
}
.tooltip {
  position: absolute;
  pointer-events: none;
  background: var(--background-color);
  color: var(--text-color);
  border: 1px solid var(--text-color);
  padding: 4px 8px;
  border-radius: 4px;
  white-space: nowrap;
  display: none;
  z-index: 1000;
}
</style>