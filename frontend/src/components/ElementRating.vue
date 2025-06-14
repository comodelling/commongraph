<template>
  <div class="element-rating">
    <!-- Histogram above the buttons, with ref -->
    <SupportHistogram
      v-if="
        element &&
        element.node_id !== 'new' &&
        (element.node_id || (element.edge && property === 'causal_strength'))
      "
      ref="histogram"
      :node-id="element.node_id"
      :edge="element.edge"
      :property="property"
      :aggregate="false"
    />

    <!-- Buttons -->
    <div class="buttons-row">
      <button
        class="rating-button rating-E"
        :class="{ selected: currentRating === 'E' }"
        @click="rate('E')"
        title="Not at all"
      >
        1
      </button>
      <button
        class="rating-button rating-D"
        :class="{ selected: currentRating === 'D' }"
        @click="rate('D')"
        title="Not really"
      >
        2
      </button>
      <button
        class="rating-button rating-C"
        :class="{ selected: currentRating === 'C' }"
        @click="rate('C')"
        title="Maybe"
      >
        3
      </button>
      <button
        class="rating-button rating-B"
        :class="{ selected: currentRating === 'B' }"
        @click="rate('B')"
        title="Somewhat"
      >
        4
      </button>
      <button
        class="rating-button rating-A"
        :class="{ selected: currentRating === 'A' }"
        @click="rate('A')"
        title="Strongly"
      >
        5
      </button>
    </div>

    <!-- Arrow SVG and rating prompt remain unchanged -->
    <div class="arrow">
      <svg viewBox="0 0 300 10" preserveAspectRatio="none">
        <path
          d="M0 5 H280 M280 5 L270 0 M280 5 L270 10"
          fill="none"
          stroke="var(--text-color)"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </div>
    <template v-if="property === 'support'">
      <p>How much do you <b>support</b> this change?</p>
    </template>
    <template v-else-if="property === 'necessity'">
      <p>How <b>necessary</b> is C for O to happen?</p>
    </template>
    <template v-else-if="property === 'sufficiency'">
      <p>How <b>sufficient</b> is C for O to happen?</p>
    </template>
    <template v-else-if="property === 'causal_strength'">
      <p>To what extent does C <b> contribute </b> to O?</p>
    </template>
    <template v-else>
      <p>No valid property provided: {{ property }}</p>
    </template>
  </div>
</template>

<script>
import { ref, onMounted } from "vue";
import api from "../axios";
import { useAuth } from "../composables/useAuth";
import SupportHistogram from "./SupportHistogram.vue";

export default {
  components: { SupportHistogram },
  props: {
    element: {
      type: Object,
      required: false,
      default: null,
    },
    property: {
      type: String,
      required: true,
    },
  },
  setup(props) {
    const currentRating = ref(null);
    const histogram = ref(null);
    const { getAccessToken } = useAuth();
    const token = getAccessToken();

    const fetchRating = async () => {
      if (!token) return;
      try {
        let response;
        if (props.element && props.element.node_id) {
          response = await api.get(
            `${import.meta.env.VITE_BACKEND_URL}/nodes/${props.element.node_id}/ratings/me`,
            {
              params: { rating_type: props.property },
              headers: { Authorization: `Bearer ${token}` },
            },
          );
        } else if (
          props.element &&
          props.element.edge &&
          props.element.edge.source &&
          props.element.edge.target
        ) {
          response = await api.get(
            `${import.meta.env.VITE_BACKEND_URL}/edges/${props.element.edge.source}/${props.element.edge.target}/ratings/me`,
            {
              params: {
                rating_type: props.property,
              },
              headers: { Authorization: `Bearer ${token}` },
            },
          );
        }
        if (response && response.data) {
          // console.log("Rating response:", response.data);
          currentRating.value = response.data.rating;
        }
      } catch (error) {
        console.error("Failed to fetch rating:", error);
      }
    };

    const rate = async (val) => {
      currentRating.value = val;
      if (!token) {
        alert("You must be logged in to rate.");
        return;
      }
      var response = null;
      try {
        const ratingData = {
          rating_type: props.property,
          rating: val,
        };
        if (props.element && props.element.node_id) {
          ratingData.node_id = props.element.node_id;
          ratingData.entity_type = "node";

          response = await api.post(
            `${import.meta.env.VITE_BACKEND_URL}/nodes/${props.element.node_id}/ratings`,
            ratingData,
            { headers: { Authorization: `Bearer ${token}` } },
          );
        } else if (
          props.element &&
          props.element.edge &&
          props.element.edge.source &&
          props.element.edge.target
        ) {
          ratingData.source_id = props.element.edge.source;
          ratingData.target_id = props.element.edge.target;
          ratingData.entity_type = "edge";
          response = await api.post(
            `${import.meta.env.VITE_BACKEND_URL}/edges/${props.element.edge.source}/${props.element.edge.target}/ratings`,
            ratingData,
            { headers: { Authorization: `Bearer ${token}` } },
          );
        }
        // console.log("Rating data:", ratingData);

        currentRating.value = response.data.rating;
        // After updating the rating, refresh the histogram data
        if (histogram.value && histogram.value.fetchRatings) {
          histogram.value.fetchRatings();
        }
      } catch (error) {
        console.error("Failed to submit rating:", error);
      }
    };

    onMounted(() => fetchRating());
    return { currentRating, rate, property: props.property, histogram };
  },
};
</script>

<style scoped>
.element-rating {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 14px;
}

.support-view {
  padding: 0;
  width: 100%;
  margin: 0 10px 0 0;
}
.buttons-row {
  display: flex;
  justify-content: center;
  margin: -27px 0 0 41px;
}
.rating-button {
  margin: 0 2px;
  width: 60px;
  font-size: 17px;
  padding: 5px;
  border-radius: 5px;
  border: 3px solid transparent;
  color: var(--text-color);
  opacity: 0.8;
}
.rating-button.rating-A {
  border-color: var(--rating-A-color);
}
.rating-button.rating-B {
  border-color: var(--rating-B-color);
}
.rating-button.rating-C {
  border-color: var(--rating-C-color);
}
.rating-button.rating-D {
  border-color: var(--rating-D-color);
}
.rating-button.rating-E {
  border-color: var(--rating-E-color);
}
.rating-button.selected {
  border-color: #fff;
  box-shadow: 0px 0px 5px rgba(0, 0, 0, 0.5);
  opacity: 1;
}
.arrow {
  width: 320px;
  height: 10px;
  margin-bottom: 8px;
  margin-left: 20px;
  opacity: 0.5;
}
.arrow svg {
  width: 100%;
  height: 100%;
}
</style>
