<template>
  <div class="search-bar" :class="{ 'search-focused': isFocused }">
    <input
      ref="searchInput"
      v-model="searchQuery"
      @input="updateSearchQuery"
      @keyup.enter="search"
      @focus="handleFocus"
      @blur="handleBlur"
      :placeholder="computedPlaceholder"
    />
    <button v-if="showButton" @click="search" class="search-button">🔍</button>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { parseSearchQuery } from "../../utils/searchParser.js";
import { useConfig } from "../../composables/useConfig";

const props = defineProps({
  initialQuery: { type: String, default: "" },
  placeholder: { type: String, default: "Explore this graph..." },
  showButton: { type: Boolean, default: true },
});
const emit = defineEmits(["search", "focus-change"]);

// Load configuration once
const { platformName, load } = useConfig();
load();

// Reactive search query and focus state
const searchQuery = ref(props.initialQuery);
const isFocused = ref(false);
const searchInput = ref(null);

// Compute placeholder based on platformName
const computedPlaceholder = computed(() => {
  return props.placeholder === "Explore this graph..."
    ? `Search in ${platformName.value}`
    : props.placeholder;
});

// Update query on input
function updateSearchQuery(event) {
  searchQuery.value = event.target.value;
}

// Emit search event with parsed query
function search() {
  const parsedQuery = parseSearchQuery(searchQuery.value);
  emit("search", parsedQuery);
}

// Handle focus events
function handleFocus() {
  isFocused.value = true;
  emit("focus-change", true);
}

function handleBlur() {
  isFocused.value = false;
  emit("focus-change", false);
}
</script>

<style scoped>
.search-bar {
  display: flex;
  align-items: center;
  max-width: 600px;
  width: 450px;
  min-width: 230px;
  overflow: hidden;
  transition: width 0.2s ease; /* Smooth width transitions */
}

/* Dynamic width expansion when focused */
.search-bar.search-focused {
  width: 100%; /* Expand to fill available space when focused */
  max-width: none;
}

/* Mobile responsive search bar */
@media (max-width: 768px) {
  .search-bar {
    width: 100%;
    min-width: 200px; /* Reasonable minimum with button */
    max-width: none;
  }
}

@media (max-width: 480px) {
  .search-bar {
    min-width: 150px; /* Smaller but still usable with button */
  }
}

.search-bar input {
  flex-grow: 1;
  padding: 10px;
  border: none;
  outline: none;
  border: 1px solid var(--border-color);
  padding: 9px;
  border-radius: 3px 0 0 3px; /* Restore original border radius */
  min-width: 0; /* Allow input to shrink */
}

/* Mobile input improvements */
@media (max-width: 600px) {
  .search-bar input {
    font-size: 14px; /* Smaller font to prevent placeholder cutoff */
  }
}

@media (max-width: 480px) {
  .search-bar input {
    padding: 8px 6px; /* Reduced padding for small screens */
    font-size: 14px; /* Maintain readable size */
  }

  .search-button {
    padding: 6px 8px; /* Smaller button */
    font-size: 14px;
  }
}

.search-button {
  background-color: rgb(39, 98, 162);
  border: none;
  cursor: pointer;
  font-size: 16px;
  border-radius: 0 3px 3px 0;
  padding: 7px 11px 8px 9px;
  transition: var(--background-color) 0.2s ease;
}

.search-button:hover {
  background-color: rgb(39, 98, 162);
}
</style>
