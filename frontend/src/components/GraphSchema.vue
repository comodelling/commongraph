<template>
  <div id="container" class="schema-page"></div>
</template>

<script lang="ts">
import { onMounted, onBeforeUnmount } from "vue";
import api from "../axios";
import Graph from "graphology";
import Sigma from "sigma";

export default {
  name: "GraphSchema",
  setup() {
    let renderer: Sigma;

    onMounted(async () => {
      const graph = new Graph({ type: "directed", multi: true });

      // Compute text color from CSS variable:
      const computedLabelColor =
        getComputedStyle(document.body)
          .getPropertyValue("--text-color")
          .trim() || "#000";

      // 1) fetch schema
      const { data } = await api.get("/schema");
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
          labelColor: computedLabelColor
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
            size: 1,
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
</style>