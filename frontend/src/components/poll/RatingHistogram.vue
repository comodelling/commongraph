<template>
  <div class="support-view">
    <div class="chart-container">
      <canvas ref="chart" @click="onChartClick"></canvas>
      <div v-if="loading" class="loading-overlay">Loading ratings…</div>
    </div>
    <div v-if="error" class="error-message">{{ error }}</div>
  </div>
</template>

<script>
import { ref, watch, onMounted, nextTick, computed } from "vue";
import api from "../../api/axios";
import qs from "qs";
import Chart from "chart.js/auto";
import { triColorGradient } from "../../utils/colorUtils";
import { useLogging } from "../../composables/useLogging";

export default {
  name: "RatingHistogram",
  props: {
    // element is required only when not in aggregate mode
    element: {
      type: Object,
      required: false,
      default: () => ({}),
    },
    pollLabel: {
      type: String,
      required: true,
    },
    pollConfig: {
      type: Object,
      required: true,
    },
    aggregate: {
      type: Boolean,
      default: true,
    },
    // only used when aggregate=true
    nodes: {
      type: Array,
      default: () => [],
    },
  },
  setup(props, { emit, expose }) {
    // Logging system
    const { debugLog, infoLog, warnLog, errorLog, DEBUG } =
      useLogging("RatingHistogram");

    const ratings = ref([]);
    const loading = ref(false);
    const error = ref(null);
    const chart = ref(null);
    let chartInstance = null;

    const isDiscrete = computed(() => props.pollConfig.scale === "discrete");
    const optionKeys = computed(() =>
      isDiscrete.value
        ? Object.keys(props.pollConfig.options)
            .map((k) => Number(k))
            .sort((a, b) => a - b)
            .map(String)
        : [],
    );
    const xLabels = computed(() =>
      isDiscrete.value ? optionKeys.value : /* fallback for continuous */ [],
    );

    const bucketCount = computed(() => {
      const n = ratings.value.length;
      return Math.min(50, Math.max(3, n));
    });
    const continuousMin = computed(() => props.pollConfig.range?.[0] ?? 0);
    const continuousMax = computed(() => props.pollConfig.range?.[1] ?? 100);

    function getBarColors(count) {
      // Orange → grey → green
      return triColorGradient("#cc8400", "#cccccc", "#008000", count);
    }
    const fetchRatings = async () => {
      loading.value = true;
      error.value = null;

      try {
        if (props.aggregate) {
          // In aggregate mode, pull medians for all node_ids
          if (!props.nodes.length) {
            ratings.value = [];
          } else {
            const resp = await api.get("/nodes/ratings/median", {
              params: {
                node_ids: props.nodes.map((n) => n.node_id),
                poll_label: props.pollLabel,
              },
              paramsSerializer: (p) =>
                qs.stringify(p, { arrayFormat: "repeat" }),
            });
            // console.log("Median ratings response:", resp.data);
            ratings.value = Object.values(resp.data)
              .map((item) => item[props.pollLabel])
              .filter((val) => val != null)
              .map((val) => ({ median_rating: val }));
          }
        } else {
          // Single‐element mode
          let resp;
          if (props.element.node_id) {
            resp = await api.get(`/nodes/${props.element.node_id}/ratings`, {
              params: { poll_label: props.pollLabel },
            });
          } else {
            const { source, target } = props.element.edge;
            resp = await api.get(`/edges/${source}/${target}/ratings`, {
              params: { poll_label: props.pollLabel },
            });
          }
          const data = resp.data;
          // Ensure we assign an Array
          if (Array.isArray(data)) {
            ratings.value = data;
          } else if (data && Array.isArray(data.ratings)) {
            ratings.value = data.ratings;
          } else {
            ratings.value = [];
          }
        }

        updateHistogram();
      } catch (e) {
        errorLog("Error fetching ratings:", e);
        error.value = "Error fetching ratings";
      } finally {
        loading.value = false;
      }
    };

    const updateHistogram = async () => {
      await nextTick();
      if (!chart.value) return;

      if (isDiscrete.value) {
        // Discrete histogram
        const buckets = optionKeys.value.map(() => 0);
        ratings.value.forEach((r) => {
          const v = r.rating ?? r.median_rating;
          const idx = optionKeys.value.indexOf(String(v));
          if (idx >= 0) buckets[idx]++;
        });
        const labels = xLabels.value;
        const root = getComputedStyle(document.documentElement);
        const colors = getBarColors(buckets.length);

        const ctx = chart.value.getContext("2d");
        if (chartInstance) {
          chartInstance.data.labels = labels;
          chartInstance.data.datasets[0].data = buckets;
          chartInstance.data.datasets[0].backgroundColor = colors;
          chartInstance.update();
        } else {
          chartInstance = new Chart(ctx, {
            type: "bar",
            data: {
              labels,
              datasets: [
                {
                  data: buckets,
                  backgroundColor: colors,
                },
              ],
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              scales: {
                x: { title: { display: props.aggregate, text: "Rating" } },
                y: {
                  beginAtZero: true,
                  title: { display: true, text: "Count" },
                },
              },
              plugins: { legend: { display: false } },
            },
          });
        }
      } else {
        // Continuous histogram: use configured range
        const minR = continuousMin.value;
        const maxR = continuousMax.value;
        const span = maxR - minR || 1;
        const nbuckets = bucketCount.value;
        const bucketWidth = span / nbuckets;
        const buckets = Array(nbuckets).fill(0);

        ratings.value.forEach((r) => {
          const v = r.rating ?? r.median_rating;
          const idx = Math.min(
            nbuckets - 1,
            Math.floor(((v - minR) / span) * nbuckets),
          );
          buckets[idx]++;
        });

        // Create numeric data points centered in each bucket
        const dataPoints = buckets.map((count, i) => ({
          x: minR + (i + 0.5) * bucketWidth,
          y: count,
        }));

        const root = getComputedStyle(document.documentElement);
        // const barColor = root.getPropertyValue("--accent-color").trim() || "#888";
        const colors = getBarColors(nbuckets);

        const ctx = chart.value.getContext("2d");
        if (chartInstance) {
          chartInstance.data.datasets[0].data = dataPoints;
          chartInstance.data.datasets[0].backgroundColor = colors;
          chartInstance.options.scales.x.min = minR;
          chartInstance.options.scales.x.max = maxR;
          chartInstance.options.scales.x.ticks.stepSize = bucketWidth;
          chartInstance.update();
        } else {
          chartInstance = new Chart(ctx, {
            type: "bar",
            data: {
              // When using a linear x-axis, Chart.js ignores labels and uses the x values in dataPoints
              datasets: [
                {
                  data: dataPoints,
                  backgroundColor: colors,
                },
              ],
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              scales: {
                x: {
                  type: "linear",
                  min: minR,
                  max: maxR,
                  title: { display: props.aggregate, text: "Rating" },
                  ticks: { stepSize: bucketWidth },
                },
                y: {
                  beginAtZero: true,
                  title: { display: true, text: "Count" },
                },
              },
              plugins: { legend: { display: false } },
            },
          });
        }
      }
    };

    onMounted(fetchRatings);
    watch(
      () => props.nodes,
      () => props.aggregate && fetchRatings(),
      () => props.pollLabel,
      () => {
        fetchRatings();
      },
      { deep: true },
    );

    expose({ fetchRatings });

    const onChartClick = (evt) => {
      if (!chartInstance) return;
      const points = chartInstance.getElementsAtEventForMode(
        evt,
        "nearest",
        { intersect: true },
        false,
      );
      if (points[0]) {
        const idx = points[0].index;
        // map back 0→5,1→4…
        const rating = 5 - idx;
        emit("filter-by-rating", rating);
      }
    };

    return { loading, error, chart, onChartClick };
  },
};
</script>

<style scoped>
.chart-container {
  position: relative;
  width: 100%;
  max-height: 150px;
  /* min-height: 100px; */
}
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}
.error-message {
  margin-top: 0.5em;
  color: red;
}
</style>
