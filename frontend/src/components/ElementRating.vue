<template>
  <div class="element-rating">
    <!-- Rating Prompt -->
    <template v-if="property === 'support'">
      <p>How much do you <b>support</b> this change?</p>
    </template>
    <template v-else-if="property === 'necessity'">
      <p>How <b>necessary</b> is C for O to happen?</p>
    </template>
    <template v-else-if="property === 'sufficiency'">
      <p>How <b>sufficient</b> is C for O to happen?</p>
    </template>
    <template v-else>
      <p>No valid property provided: {{ property }}</p>
    </template>

    <!-- Buttons -->
    <div class="buttons-row">
      <button
        class="rating-button rating-E"
        :class="{ selected: currentRating === 'E' }"
        @click="rate('E')"
      >
        1
      </button>
      <button
        class="rating-button rating-D"
        :class="{ selected: currentRating === 'D' }"
        @click="rate('D')"
      >
        2
      </button>
      <button
        class="rating-button rating-C"
        :class="{ selected: currentRating === 'C' }"
        @click="rate('C')"
      >
        3
      </button>
      <button
        class="rating-button rating-B"
        :class="{ selected: currentRating === 'B' }"
        @click="rate('B')"
      >
        4
      </button>
      <button
        class="rating-button rating-A"
        :class="{ selected: currentRating === 'A' }"
        @click="rate('A')"
      >
        5
      </button>
    </div>

    <!-- Arrow SVG -->
    <div class="arrow">
      <svg viewBox="0 0 300 10" preserveAspectRatio="none">
        <path
          d="M0 5 H280 M280 5 L270 0 M280 5 L270 10"
          fill="none"
          stroke="white"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </div>
  </div>
</template>

<script>
import { ref } from "vue";
export default {
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
    const rate = (val) => {
      currentRating.value = val;
      // Emitting or API call can go here if needed.
    };
    return {
      currentRating,
      rate,
      property: props.property,
    };
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

.buttons-row {
  display: flex;
  justify-content: center;
  margin: 2px 0;
}

.rating-button {
  margin: 0 1px;
  width: 60px;
  font-size: 17px;
  padding: 5px;
  border-radius: 5px;
  border: 3px solid transparent;
  /* box-sizing: border-box; */
  color: var(--text-color);
  opacity: 0.8;
}

/* Apply a background based on rating class */
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

.rating-button.rating-A.selected {
  background-color: var(--rating-A-color);
}
.rating-button.rating-B.selected {
  background-color: var(--rating-B-color);
}
.rating-button.rating-C.selected {
  background-color: var(--rating-C-color);
}
.rating-button.rating-D.selected {
  background-color: var(--rating-D-color);
}
.rating-button.rating-E.selected {
  background-color: var(--rating-E-color);
}

/* Optionally, style selected buttons (e.g., add a border or shadow) */
.rating-button.selected {
  border-color: #fff;
  /* For example, you might add a box-shadow or adjust opacity */
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
