<template>
  <div class="search-bar">
    <input
      v-model="searchQuery"
      @input="updateSearchQuery"
      @keyup.enter="search"
      :placeholder="computedPlaceholder"
    />
    <button v-if="showButton" @click="search" class="search-button">🔍</button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { parseSearchQuery } from '../../utils/searchParser.js';
import { useConfig } from '../../composables/useConfig';

const props = defineProps({
  initialQuery: { type: String, default: '' },
  placeholder: { type: String, default: 'Explore this graph...' },
  showButton: { type: Boolean, default: true },
});
const emit = defineEmits(['search']);

// Load configuration once
const { platformName, load } = useConfig();
load();

// Reactive search query
const searchQuery = ref(props.initialQuery);

// Compute placeholder based on platformName
const computedPlaceholder = computed(() => {
  return props.placeholder === 'Explore this graph...'
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
  emit('search', parsedQuery);
}
</script>

<style scoped>
.search-bar {
  display: flex;
  align-items: center;
  max-width: 800px;
  width: 600px;
  min-width: 200px;
  overflow: hidden;
}

.search-bar input {
  flex-grow: 1;
  padding: 10px;
  border: none;
  outline: none;
  border: 1px solid var(--border-color);
  padding: 9px;
  border-radius: 3px 0 0 3px;
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
