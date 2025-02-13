<template>
  <div class="element-rating">
    <p>Rate this element:</p>
    <!-- This example uses simple buttons; you can later replace this with a more robust rating system -->
    <button @click="rate(A)">A</button>
    <button @click="rate(B)">B</button>
    <button @click="rate(C)">C</button>
    <button @click="rate(D)">D</button>
    <button @click="rate(E)">E</button>
    <p v-if="currentRating">Current rating: {{ currentRating }}</p>
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
  },
  setup() {
    const currentRating = ref(null);
    const rate = (val) => {
      currentRating.value = val;
      // Here you could also emit an event or call an API to persist the rating
    };
    return {
      currentRating,
      rate,
    };
  },
};
</script>

<style scoped>
.element-rating {
  /* border-top: 1px solid var(--border-color); */
  margin-top: 15px;
  /* padding-top: 10px; */
  font-size: 13px;
}
.element-rating button {
  margin-right: 5px;
}
</style>
