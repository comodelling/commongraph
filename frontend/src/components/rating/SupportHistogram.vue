<template>
  <div class="support-view">
    <h2 v-if="!aggregate">
      {{
        edge && property === "causal_strength"
          ? "Causal Ratings"
          : "Support Ratings"
      }}
    </h2>
    <h2 v-else>Support Ratings</h2>
    <div v-if="loading">Loading ratings...</div>
    <div v-if="error">{{ error }}</div>
    <div v-else class="chart-container">
      <canvas ref="chart" @click="onChartClick"></canvas>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted, nextTick } from "vue";
import api from "../../api/axios";
import Chart from "chart.js/auto";

export default {
  name: "SupportHistogram",
  props: {
    // When aggregate is true, 'nodes' prop is used as before.
    nodes: {
      type: Array,
      default: () => [],
    },
    // For node ratings
    nodeId: {
      type: [Number, String],
      default: null,
    },
    // For edge ratings
    edge: {
      type: Object,
      default: null,
    },
    // Pass the rating type (e.g. "support" or "causal_strength")
    property: {
      type: String,
      default: null,
    },
    aggregate: {
      type: Boolean,
      default: true,
    },
  },
  setup(props, { emit, expose }) {
    const ratings = ref(null);
    const loading = ref(false);
    const error = ref(null);
    const chart = ref(null);
    let chartInstance = null;

    const scaleMap = {
      A: 4,
      B: 3,
      C: 2,
      D: 1,
      E: 0,
    };
    const xLabels = ["1", "2", "3", "4", "5"];

    const getBarColors = () => {
      const rootStyles = getComputedStyle(document.documentElement);
      return [
        rootStyles.getPropertyValue("--rating-E-color").trim(),
        rootStyles.getPropertyValue("--rating-D-color").trim(),
        rootStyles.getPropertyValue("--rating-C-color").trim(),
        rootStyles.getPropertyValue("--rating-B-color").trim(),
        rootStyles.getPropertyValue("--rating-A-color").trim(),
      ];
    };

    const fetchRatings = async () => {
      if (!props.aggregate && props.nodeId === "new") {
        console.info("Skipping ratings fetch for new node.");
        return;
      }
      loading.value = true;
      error.value = null;
      try {
        if (props.aggregate) {
          // Aggregated mode: multiple nodes.
          const nodeIds = props.nodes.map((node) => node.node_id);
          const response = await api.get(
            `/nodes/ratings/median`,
            { params: { node_ids: nodeIds } },
          );
          ratings.value = response.data;
        } else {
          // Non-aggregated mode.
          if (props.nodeId) {
            // Node ratings mode
            const response = await api.get(
              `/nodes/${props.nodeId}/ratings`,
            );
            ratings.value = response.data.ratings;
          } else if (props.edge) {
            // Edge ratings mode (for causal_strength)
            const response = await api.get(
              `/edges/${props.edge.source}/${props.edge.target}/ratings`,
              {
                params: {
                  rating_type: props.property,
                },
              },
            );
            // console.log("Rating response:", response.data);
            ratings.value = response.data.ratings;
          } else {
            throw new Error("Either nodeId or edge prop must be provided.");
          }
        }
        updateHistogram();
      } catch (e) {
        error.value = "Error fetching ratings";
        console.error(e);
      } finally {
        loading.value = false;
      }
    };

    const updateHistogram = async () => {
      await nextTick();
      if (!chart.value) {
        console.warn("Chart canvas not rendered yet");
        // setTimeout(updateHistogram, 10);
        return;
      }
      const buckets = [0, 0, 0, 0, 0];
      if (props.aggregate) {
        Object.values(ratings.value || {}).forEach((entry) => {
          const ratingLetter = entry.median_rating;
          if (ratingLetter && scaleMap.hasOwnProperty(ratingLetter)) {
            buckets[scaleMap[ratingLetter]]++;
          }
        });
      } else {
        (ratings.value || []).forEach((entry) => {
          const ratingLetter = entry.rating;
          if (ratingLetter && scaleMap.hasOwnProperty(ratingLetter)) {
            buckets[scaleMap[ratingLetter]]++;
          }
        });
      }
      const ctx = chart.value.getContext("2d");
      const barColors = getBarColors();
      if (chartInstance) {
        chartInstance.data.datasets[0].data = buckets;
        chartInstance.data.datasets[0].backgroundColor = barColors;
        chartInstance.update();
      } else {
        chartInstance = new Chart(ctx, {
          type: "bar",
          data: {
            labels: xLabels,
            datasets: [
              {
                data: buckets,
                backgroundColor: barColors,
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: {
                title: {
                  display: props.aggregate,
                  text: "Median Rating",
                },
              },
              y: {
                beginAtZero: true,
                title: { display: true, text: "Count" },
              },
            },
          },
        });
      }
    };

    watch(
      () => (props.aggregate ? props.nodes : props.nodeId || props.edge),
      (newVal) => {
        if (
          (props.aggregate && newVal.length) ||
          (!props.aggregate && newVal)
        ) {
          fetchRatings();
        } else if (chartInstance) {
          chartInstance.destroy();
          chartInstance = null;
        }
      },
      { immediate: true },
    );

    onMounted(() => {
      if (
        (props.aggregate && props.nodes.length) ||
        (!props.aggregate && (props.nodeId || props.edge))
      )
        fetchRatings();
    });

    const onChartClick = (evt) => {
      if (!chartInstance) return;
      const activePoint = chartInstance.getElementsAtEventForMode(
        evt,
        "nearest",
        { intersect: true },
        false,
      );
      if (activePoint[0]) {
        const idx = activePoint[0].index;
        // Convert index back to a rating letter, e.g. buckets[0] -> 'E'
        const ratingLetter = Object.keys(scaleMap).find(
          (key) => scaleMap[key] === idx,
        );
        if (ratingLetter) {
          emit("filter-by-rating", ratingLetter);
        }
      }
    };

    expose({ fetchRatings });
    return {
      ratings,
      loading,
      error,
      chart,
      aggregate: props.aggregate,
      onChartClick,
    };
  },
};
</script>

<style scoped>
.support-view {
  padding: 10px 0;
  text-align: center;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border-radius: 4px;
  height: clamp(150px, 30%, 100vh);
}

.support-view h2 {
  margin: 0px 30px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-color);
}

.chart-container {
  flex: 1;
}

canvas {
  width: 100% !important;
  height: 100% !important;
  display: block;
}
</style>
