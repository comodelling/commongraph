<template>
  <div class="support-view">
    <h2 v-if="!aggregate">Suport Ratings</h2>
    <h2 v-else>Support Ratings</h2>
    <div v-if="loading">Loading ratings...</div>
    <div v-if="error">{{ error }}</div>
    <div v-else class="chart-container">
      <canvas ref="chart"></canvas>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted } from "vue";
import api from "../axios";
import Chart from "chart.js/auto";

export default {
  name: "SupportHistogram",
  props: {
    // When aggregate is true, 'nodes' prop is used as before.
    nodes: {
      type: Array,
      default: () => [],
    },
    // When aggregate is false, we assume a single node is to be visualized.
    nodeId: {
      type: Number,
      default: null,
    },
    aggregate: {
      type: Boolean,
      default: true,
    },
  },
  setup(props) {
    const ratings = ref(null); // Either an object mapping nodeId->rating or an array of ratings.
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
      loading.value = true;
      error.value = null;
      try {
        if (props.aggregate) {
          // Aggregated mode: multiple nodes.
          const nodeIds = props.nodes.map((node) => node.node_id);
          const response = await api.get(
            `${import.meta.env.VITE_BACKEND_URL}/rating/nodes/median`,
            { params: { node_ids: nodeIds } },
          );
          ratings.value = response.data; // Expected to be an object mapping node_id -> { median_rating: "X" }
        } else {
          // Non-aggregated mode: single node.
          if (!props.nodeId) {
            throw new Error(
              "nodeId prop must be provided when aggregate is false.",
            );
          }
          const response = await api.get(
            `${import.meta.env.VITE_BACKEND_URL}/ratings/node/`,
            { params: { node_id: props.nodeId } },
          );
          // Expecting response.data.ratings as an array of objects, each with a rating property.
          ratings.value = response.data.ratings;
        }
        updateHistogram();
      } catch (e) {
        error.value = "Error fetching ratings";
        console.error(e);
      } finally {
        loading.value = false;
      }
    };

    const updateHistogram = () => {
      const buckets = [0, 0, 0, 0, 0];
      if (props.aggregate) {
        // ratings.value is an object mapping node ids to { median_rating: rating }
        Object.values(ratings.value || {}).forEach((entry) => {
          const ratingLetter = entry.median_rating;
          if (ratingLetter && scaleMap.hasOwnProperty(ratingLetter)) {
            buckets[scaleMap[ratingLetter]]++;
          }
        });
      } else {
        // ratings.value is an array of rating objects.
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
            plugins: {
              legend: { display: false },
            },
            scales: {
              x: {
                title: {
                  display: props.aggregate ? true : false,
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

    // In aggregated mode, watch the nodes prop; otherwise watch nodeId.
    watch(
      () => (props.aggregate ? props.nodes : props.nodeId),
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
        (!props.aggregate && props.nodeId)
      )
        fetchRatings();
    });

    return {
      ratings,
      loading,
      error,
      chart,
      aggregate: props.aggregate,
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
