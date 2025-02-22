<template>
  <div class="support-view">
    <h2>Support Histogram</h2>
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
  name: "SupportView",
  props: {
    nodes: {
      type: Array,
      default: () => [],
    },
  },
  setup(props) {
    const ratings = ref({});
    const loading = ref(false);
    const error = ref(null);
    const chart = ref(null);
    let chartInstance = null;

    // New mapping: E (lowest = 1) gets bucket index 0, A (highest = 5) gets index 4.
    const scaleMap = {
      A: 4,
      B: 3,
      C: 2,
      D: 1,
      E: 0,
    };

    // x-axis labels from lowest (1) to highest (5)
    const xLabels = ["1", "2", "3", "4", "5"];

    // Retrieve computed CSS custom property values for bar colours in the correct order.
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
      ratings.value = {};

      try {
        const nodeIds = props.nodes.map((node) => node.node_id);
        const response = await api.get(
          `${import.meta.env.VITE_BACKEND_URL}/rating/nodes/median`,
          { params: { node_ids: nodeIds } },
        );
        // Expected response: { <node_id>: { median_rating: "A" } }
        ratings.value = response.data;
        updateHistogram();
      } catch (e) {
        error.value = "Error fetching ratings";
      } finally {
        loading.value = false;
      }
    };

    const updateHistogram = () => {
      // Initialize buckets for ratings 1 to 5 (bucket 0 for rating "E", bucket 4 for "A")
      const buckets = [0, 0, 0, 0, 0];
      Object.values(ratings.value).forEach((entry) => {
        const ratingLetter = entry.median_rating;
        if (ratingLetter && scaleMap.hasOwnProperty(ratingLetter)) {
          buckets[scaleMap[ratingLetter]]++;
        }
      });
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
              legend: {
                display: false,
              },
            },
            scales: {
              x: {
                title: {
                  display: true,
                  text: "Median Rating",
                },
              },
              y: {
                beginAtZero: true,
                title: {
                  display: true,
                  text: "Count",
                },
              },
            },
          },
        });
      }
    };

    watch(
      () => props.nodes,
      (newVal) => {
        if (newVal.length) {
          fetchRatings();
        } else if (chartInstance) {
          chartInstance.destroy();
          chartInstance = null;
        }
      },
      { immediate: true },
    );

    // In case the component mounts after styles are ready.
    onMounted(() => {
      if (props.nodes.length) fetchRatings();
    });

    return {
      ratings,
      loading,
      error,
      chart,
    };
  },
};
</script>

<style scoped>
.support-view {
  padding: 20px;
  text-align: center;

  height: 50%;
  min-height: 0; /* allow flex children to shrink */
  display: flex;
  flex-direction: column;
  /* border: 1px solid blue; */
}

.chart-container {
  flex: 1; /* take available vertical space */
  min-height: 75px; /* allow shrinking to prevent overflow */
  min-width: 75px; /* allow flex children to shrink */
  /* border: 1px solid green; */
}

/* Make the canvas fill the container */
canvas {
  width: 100% !important;
  height: 100% !important;
  display: block;
}
</style>
