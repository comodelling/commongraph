<template>
  <div class="scope-autocomplete">
    <div class="input-wrapper">
      <input
        ref="inputRef"
        v-model="searchQuery"
        @input="onInput"
        @focus="onFocus"
        @blur="onBlur"
        @keydown.down.prevent="highlightNext"
        @keydown.up.prevent="highlightPrevious"
        @keydown.enter.prevent="selectHighlighted"
        @keydown.escape="closeDropdown"
        :placeholder="placeholder"
        :class="{ 'has-error': error, 'is-new': isNewScope }"
        class="scope-input"
        :title="isNewScope ? 'Press Enter to create new scope' : ''"
      />
    </div>

    <div v-if="showDropdown" class="dropdown" ref="dropdownRef">
      <div v-if="loading" class="dropdown-item loading">Searching...</div>
      <div
        v-else-if="filteredScopes.length === 0 && searchQuery"
        class="dropdown-item no-results"
      >
        No matching scopes. Press Enter to create "{{ searchQuery }}"
      </div>
      <div
        v-for="(scope, index) in filteredScopes"
        :key="scope.scope_id"
        :class="['dropdown-item', { highlighted: index === highlightedIndex }]"
        @mousedown.prevent="selectScope(scope)"
        @mouseenter="highlightedIndex = index"
      >
        {{ scope.name }}
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from "vue";
import api from "../../api/axios";
import { useLogging } from "../../composables/useLogging";

export default {
  name: "ScopeAutocomplete",
  props: {
    modelValue: {
      type: String,
      default: "",
    },
    placeholder: {
      type: String,
      default: "Type to search scopes...",
    },
    error: {
      type: Boolean,
      default: false,
    },
  },
  emits: ["update:modelValue", "blur"],
  setup(props, { emit }) {
    // Logging system
    const { debugLog, infoLog, warnLog, errorLog, DEBUG } =
      useLogging("ScopeAutocomplete");

    const inputRef = ref(null);
    const dropdownRef = ref(null);
    const searchQuery = ref(props.modelValue || "");
    const allScopes = ref([]);
    const loading = ref(false);
    const showDropdown = ref(false);
    const highlightedIndex = ref(0);
    const debounceTimer = ref(null);

    // Check if current value is a new scope (not in the list)
    const isNewScope = computed(() => {
      if (!searchQuery.value.trim()) return false;
      return !allScopes.value.some(
        (s) => s.name.toLowerCase() === searchQuery.value.toLowerCase(),
      );
    });

    // Filter scopes based on search query
    const filteredScopes = computed(() => {
      if (!searchQuery.value.trim()) {
        return allScopes.value.slice(0, 10); // Show first 10 when empty
      }
      const query = searchQuery.value.toLowerCase();
      return allScopes.value
        .filter((scope) => scope.name.toLowerCase().includes(query))
        .slice(0, 10);
    });

    // Fetch scopes from API with debouncing
    const fetchScopes = async (query = "") => {
      loading.value = true;
      try {
        const params = query ? { q: query, limit: 10 } : { limit: 50 };
        const response = await api.get("/scopes", { params });
        allScopes.value = response.data;
      } catch (error) {
        errorLog("Failed to fetch scopes:", error);
        allScopes.value = [];
      } finally {
        loading.value = false;
      }
    };

    // Debounced input handler
    const onInput = () => {
      clearTimeout(debounceTimer.value);
      debounceTimer.value = setTimeout(() => {
        fetchScopes(searchQuery.value);
      }, 300); // 300ms debounce

      emit("update:modelValue", searchQuery.value);
    };

    const onFocus = () => {
      showDropdown.value = true;
      if (allScopes.value.length === 0) {
        fetchScopes();
      }
    };

    const onBlur = () => {
      // Delay to allow click on dropdown items
      setTimeout(() => {
        showDropdown.value = false;
        emit("blur");
      }, 200);
    };

    const selectScope = (scope) => {
      searchQuery.value = scope.name;
      emit("update:modelValue", scope.name);
      showDropdown.value = false;
      inputRef.value?.blur();
    };

    const highlightNext = () => {
      if (highlightedIndex.value < filteredScopes.value.length - 1) {
        highlightedIndex.value++;
      }
    };

    const highlightPrevious = () => {
      if (highlightedIndex.value > 0) {
        highlightedIndex.value--;
      }
    };

    const selectHighlighted = () => {
      if (filteredScopes.value.length > 0 && highlightedIndex.value >= 0) {
        selectScope(filteredScopes.value[highlightedIndex.value]);
      } else {
        // If no scope highlighted, accept the current input as new scope
        emit("update:modelValue", searchQuery.value);
        showDropdown.value = false;
        inputRef.value?.blur();
      }
    };

    const closeDropdown = () => {
      showDropdown.value = false;
    };

    const focus = () => {
      inputRef.value?.focus();
    };

    // Watch for external changes to modelValue
    watch(
      () => props.modelValue,
      (newVal) => {
        if (newVal !== searchQuery.value) {
          searchQuery.value = newVal || "";
        }
      },
    );

    onMounted(() => {
      // Initial fetch
      fetchScopes();
    });

    return {
      inputRef,
      dropdownRef,
      searchQuery,
      allScopes,
      loading,
      showDropdown,
      highlightedIndex,
      filteredScopes,
      isNewScope,
      onInput,
      onFocus,
      onBlur,
      selectScope,
      highlightNext,
      highlightPrevious,
      selectHighlighted,
      closeDropdown,
      focus,
    };
  },
};
</script>

<style scoped>
.scope-autocomplete {
  position: relative;
  width: 100%;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.scope-input {
  width: 100%;
  padding: 4px 8px;
  border: 1px solid #ccc;
  border-radius: 3px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.scope-input:focus {
  border-color: #4a90e2;
}

.scope-input.has-error {
  border-color: red;
}

.scope-input.is-new {
  border-color: #f39c12;
  background-color: #fffbf0;
}

/* Dark mode background for new scope indicator */
body.dark .scope-input.is-new {
  background-color: rgba(243, 156, 18, 0.15);
}

.dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  max-height: 200px;
  overflow-y: auto;
  background: white;
  border: 1px solid #ccc;
  border-top: none;
  border-radius: 0 0 3px 3px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  margin-top: -1px;
}

/* Dark mode dropdown */
body.dark .dropdown {
  background: #2d2d2d;
  border-color: #555;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.dropdown-item {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.15s;
}

.dropdown-item:hover,
.dropdown-item.highlighted {
  background-color: #fafafa;
}

/* Dark mode dropdown items */
body.dark .dropdown-item:hover,
body.dark .dropdown-item.highlighted {
  background-color: #404040;
}

.dropdown-item.loading,
.dropdown-item.no-results {
  color: #666;
  font-style: italic;
  cursor: default;
}

/* Dark mode text colors */
body.dark .dropdown-item.loading,
body.dark .dropdown-item.no-results {
  color: #aaa;
}

.dropdown-item.no-results {
  background-color: #fffbf0;
}

/* Dark mode no-results background */
body.dark .dropdown-item.no-results {
  background-color: rgba(243, 156, 18, 0.15);
}

.dropdown-item.loading:hover,
.dropdown-item.no-results:hover {
  background-color: inherit;
}
</style>
