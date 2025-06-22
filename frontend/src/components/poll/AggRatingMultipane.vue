<template>
  <div class="agg-rating-multipane tab-card">
    <div class="pane-header">
        <div class="title-group">
            <h3>User evaluations</h3>
        </div>
        <div class="tabs">
            <button
            v-for="label in pollLabels"
            :key="label"
            :class="{ active: currentTab === label }"
            @click="currentTab = label"
            >
            {{ label }}
            </button>
        </div>
    </div>
    <!-- <hr class="header-separator" /> -->
    <div class="tab-content">
      <RatingHistogram
        :key="currentTab"
        :nodes="nodes"
        :poll-label="currentTab"
        :poll-config="pollConfigs[currentTab]"
        aggregate
        @filter-by-rating="$emit('filter-by-rating', $event)"
      />
      <span
        class="info-icon-bottom"
        :title='"Median aggregates of user evaluations for search results."'
      >ℹ️</span>
    </div>
  </div>
</template>

<script>
import { ref, computed } from "vue";
import RatingHistogram from "./RatingHistogram.vue";

export default {
  name: "AggRatingMultipane",
  components: { RatingHistogram },
  props: {
    nodes: { type: Array, required: true },
    pollConfigs: { type: Object, required: true },
    infoText: { type: String, default: "" }
  },
  emits: ["filter-by-rating"],
  setup(props) {
    const pollLabels = computed(() => Object.keys(props.pollConfigs));
    const currentTab = ref(pollLabels.value[0] || "");
    return { pollLabels, currentTab };
  },
};
</script>

<style scoped>


/* HEADER: title left, tabs flush right */
.pane-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5em 1em;
}
.pane-header h3 {
  margin: 0;
  margin-left: 15px;
  font-size: 1.1em;
}
/* ensure tabs container is flush right */
.pane-header .tabs {
  display: flex;
  gap: 0.5em;
  margin: 0;
  padding: 0;
}

/* keep separator */
.header-separator {
  border: none;
  border-bottom: 1px solid var(--border-color);
  margin: 0;
}

.info-icon-bottom {
  position: absolute;
  bottom: 0.5em;
  right: 0.5em;
  font-size: 0.85em;
  cursor: help;
  opacity: 0.7;
}
</style>