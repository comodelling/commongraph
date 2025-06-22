<template>
  <div class="element-poll">
    <!-- Question from config -->
    <h3 class="poll-question">{{ pollConfig.question }}</h3>

    <!-- Histogram of past ratings: always mounted, just hidden until the “me” rating has loaded -->
    <RatingHistogram
      ref="histogram"
      :element="element"
      :pollLabel="pollLabel"
      :pollConfig="pollConfig"
      :aggregate="false"
    />

    <div v-if="!currentRatingLoaded" class="loading">Loading your rating…</div>

    <!-- Discrete buttons -->
    <div v-if="pollConfig.scale === 'discrete'" class="buttons-row">
      <button
        v-for="(label, key, idx) in pollConfig.options"
        :key="key"
        class="rating-button"
        :class="{ selected: String(currentRating) === key }"
        @click="rate(key)"
        :style="{ backgroundColor: buttonColors[idx] }"
        :title="label"
      >
        {{ key }}
      </button>
    </div>

    <!-- Continuous slider -->
    <div v-else-if="pollConfig.scale === 'continuous'" class="slider-container">
      <input
        type="range"
        :min="rangeMin"
        :max="rangeMax"
        :step="rangeStep"
        v-model.number="sliderValue"
        @change="rate(sliderValue)"
      />
      <div class="slider-value">{{ sliderValue }}</div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from "vue";
import api from "../../api/axios";
import { useAuth } from "../../composables/useAuth";
import RatingHistogram from "./RatingHistogram.vue";
import { triColorGradient } from "../../utils/colorUtils";

export default {
  name: "ElementPollPane",
  components: { RatingHistogram },
  props: {
    element: { type: Object, required: true },
    pollLabel: { type: String, required: true },
    pollConfig: { type: Object, required: true },
  },
  setup(props) {
    const currentRating = ref(null);
    const currentRatingLoaded = ref(false);
    const histogram = ref(null);
    const { getAccessToken } = useAuth();
    const token = getAccessToken();

    // continuous slider defaults
    const rangeMin = computed(() => props.pollConfig.range?.[0] ?? 0);
    const rangeMax = computed(() => props.pollConfig.range?.[1] ?? 100);
    const rangeStep = computed(() => props.pollConfig.step ?? 1);
    const sliderValue = ref((rangeMin.value + rangeMax.value) / 2);

    const optionKeys = computed(() =>
      Object.keys(props.pollConfig.options).map(x=>Number(x)).sort((a,b)=>a-b)
    );
    const buttonColors = computed(()=>{
      const n = optionKeys.value.length;
      return triColorGradient("#cc8400", "#cccccc", "#008000", n);
    });


    // load my existing rating
    const fetchRating = async () => {
      if (!token) return;
      try {
        const params = { poll_label: props.pollLabel };
        let response;
        if (props.element.node_id) {
          response = await api.get(
            `/nodes/${props.element.node_id}/ratings/me`,
            { params, headers: { Authorization: `Bearer ${token}` } }
          );
        } else {
          const { source, target } = props.element.edge;
          response = await api.get(
            `/edges/${source}/${target}/ratings/me`,
            { params, headers: { Authorization: `Bearer ${token}` } }
          );
        }
        if (response.data) {
          currentRating.value = Number(response.data.rating);
          if (props.pollConfig.scale === "continuous") {
            sliderValue.value = Number(currentRating.value);
          }
        }
      } catch {
        /* ignore missing */
      } finally {
        currentRatingLoaded.value = true;
      }
    };

    // submit a new rating
    const rate = async (val) => {
      if (!token) {
        alert("Please log in to rate.");
        return;
      }
      const num = Number(val);
      currentRating.value = num;
      const payload = {
        poll_label: props.pollLabel,
        rating: val,
        entity_type: props.element.node_id ? "node" : "edge",
      };
      if (props.element.node_id) {
        payload.node_id = props.element.node_id;
        await api.post(`/nodes/${props.element.node_id}/ratings`, payload, {
          headers: { Authorization: `Bearer ${token}` },
        });
      } else {
        const { source, target } = props.element.edge;
        payload.source_id = source;
        payload.target_id = target;
        await api.post(
          `/edges/${source}/${target}/ratings`,
          payload,
          { headers: { Authorization: `Bearer ${token}` } }
        );
      }
      // refresh histogram
      await histogram.value?.fetchRatings();
    };

    onMounted(fetchRating);
    watch(
      [() => props.element, () => props.pollLabel],
      () => {
        histogram.value?.fetchRatings();
      },
      { immediate: true, deep: true }
    );
    return {
      currentRating,
      currentRatingLoaded,
      rate,
      pollLabel: props.pollLabel,
      pollConfig: props.pollConfig,
      histogram,
      rangeMin,
      rangeMax,
      rangeStep,
      sliderValue,
      buttonColors,
      optionKeys,
    };
  },
};
</script>

<style scoped>
.element-poll {
  margin-bottom: 1em;
}
.poll-question {
  margin-bottom: 0.5em;
}
.buttons-row {
  display: flex;
  gap: 0.5em;
}
  .rating-button {
    flex: 1;             /* all buttons share available space */
    min-width: 0;        /* allow flexing below content width */
    padding: 0.5em 0;
    text-align: center;
    border: 2px solid #888;
    border-radius: 4px;
    background: green;
    color: white;
    cursor: pointer;
  }
.rating-button.selected {
  background: var(--accent-color);
  color: white;
}
.slider-container {
  display: flex;
  align-items: center;
  gap: 1em;
}
.slider-value {
  min-width: 2em;
  text-align: center;
}
</style>