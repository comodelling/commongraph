<template>
  <div class="tag-selector" :class="{ disabled }" @click="focusInput">
    <div class="tags-row">
      <span v-for="tag in tags" :key="tag" class="tag-chip">
        <span>{{ tag }}</span>
        <button
          type="button"
          class="remove-tag"
          @click.stop="removeTag(tag)"
          :disabled="disabled"
          aria-label="Remove tag"
        >
          ×
        </button>
      </span>
      <input
        ref="inputRef"
        v-model="inputValue"
        :placeholder="placeholder"
        :disabled="disabled"
        @input="onInput"
        @keydown="handleKeydown"
        @keydown.backspace="handleBackspace"
        @focus="openDropdown"
        @blur="onBlur"
        class="tag-input"
      />
    </div>
    <p class="helper-text">
      Type to search existing tags or press Enter to create a new one.
    </p>
    <div v-if="loadError" class="error-banner">
      Failed to load suggestions.
      <button type="button" @click.stop="retryFetch">Retry</button>
    </div>
    <ul v-if="showDropdown" class="suggestions">
      <li v-if="loading" class="suggestion-item loading">Searching...</li>
      <li
        v-else-if="!filteredSuggestions.length && !canCreateNewTag"
        class="suggestion-item no-results"
      >
        No matching tags.
      </li>
      <li
        v-if="canCreateNewTag"
        class="suggestion-item create-option"
        :class="{ highlighted: highlightedIndex === -1 }"
        @mousedown.prevent="selectSuggestion()"
        @mouseenter="highlightedIndex = -1"
      >
        Create "{{ inputValue.trim() }}"
      </li>
      <li
        v-for="(suggestion, idx) in filteredSuggestions"
        :key="suggestion"
        class="suggestion-item"
        :class="{ highlighted: idx === highlightedIndex }"
        @mousedown.prevent="selectSuggestion(suggestion)"
        @mouseenter="highlightedIndex = idx"
      >
        {{ suggestion }}
      </li>
    </ul>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from "vue";
import api from "../../api/axios";
import { useLogging } from "../../composables/useLogging";

export default {
  name: "TagSelector",
  props: {
    modelValue: {
      type: Array,
      default: () => [],
    },
    placeholder: {
      type: String,
      default: "Add tags...",
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    limit: {
      type: Number,
      default: 25,
    },
  },
  emits: ["update:modelValue", "blur", "keydown"],
  setup(props, { emit }) {
    const { debugLog } = useLogging("TagSelector");
    const inputRef = ref(null);
    const inputValue = ref("");
    const tags = ref([...props.modelValue]);
    const suggestions = ref([]);
    const showDropdown = ref(false);
    const loading = ref(false);
    const loadError = ref(false);
    const highlightedIndex = ref(0);
    const debounceTimer = ref(null);

    const filteredSuggestions = computed(() => {
      if (!suggestions.value.length) return [];
      const lowerInput = inputValue.value.trim().toLowerCase();
      return suggestions.value
        .filter(
          (tag) =>
            !tags.value.some(
              (existing) => existing.toLowerCase() === tag.toLowerCase(),
            ),
        )
        .filter((tag) => !lowerInput || tag.toLowerCase().includes(lowerInput));
    });

    const fetchSuggestions = async (query = "") => {
      loading.value = true;
      loadError.value = false;
      try {
        const response = await api.get("/tags", {
          params: {
            q: query || undefined,
            limit: props.limit,
          },
        });
        suggestions.value = response.data || [];
      } catch (err) {
        debugLog("Failed to load tags:", err);
        suggestions.value = [];
        loadError.value = true;
      } finally {
        loading.value = false;
      }
    };

    const scheduleFetch = (query) => {
      clearTimeout(debounceTimer.value);
      debounceTimer.value = setTimeout(() => {
        fetchSuggestions(query);
      }, 200);
    };

    const onInput = () => {
      showDropdown.value = true;
      scheduleFetch(inputValue.value);
    };

    const canCreateNewTag = computed(() => {
      const value = inputValue.value.trim();
      if (!value) return false;
      const lower = value.toLowerCase();
      const existsInSelection = tags.value.some(
        (existing) => existing.toLowerCase() === lower,
      );
      if (existsInSelection) return false;
      const existsInSuggestions = suggestions.value.some(
        (suggestion) => suggestion.toLowerCase() === lower,
      );
      return !existsInSuggestions;
    });

    const selectSuggestion = (value) => {
      const tagToAdd = (value || inputValue.value || "").trim();
      if (!tagToAdd) {
        showDropdown.value = false;
        return;
      }
      if (
        tags.value.some(
          (existing) => existing.toLowerCase() === tagToAdd.toLowerCase(),
        )
      ) {
        inputValue.value = "";
        showDropdown.value = false;
        return;
      }
      const updated = [...tags.value, tagToAdd];
      tags.value = updated;
      emit("update:modelValue", updated);
      inputValue.value = "";
      showDropdown.value = true;
      if (!suggestions.value.length) {
        fetchSuggestions();
      }
      highlightedIndex.value = canCreateNewTag.value ? -1 : 0;
    };

    const removeTag = (tag) => {
      const updated = tags.value.filter((candidate) => candidate !== tag);
      tags.value = updated;
      emit("update:modelValue", updated);
    };

    const focusInput = () => {
      inputRef.value?.focus();
    };

    const openDropdown = () => {
      showDropdown.value = true;
      if (!suggestions.value.length) {
        fetchSuggestions();
      }
    };

    const onBlur = () => {
      setTimeout(() => {
        showDropdown.value = false;
        emit("blur");
      }, 150);
    };

    const handleKeydown = (event) => {
      emit("keydown", event);
      if (event.key === "ArrowDown") {
        if (highlightedIndex.value < filteredSuggestions.value.length - 1) {
          highlightedIndex.value += 1;
        }
      } else if (event.key === "ArrowUp") {
        if (highlightedIndex.value > (canCreateNewTag.value ? -1 : 0)) {
          highlightedIndex.value -= 1;
        }
      } else if (event.key === "Enter" || event.key === "Tab") {
        event.preventDefault();
        if (highlightedIndex.value === -1 && canCreateNewTag.value) {
          selectSuggestion();
        } else if (filteredSuggestions.value.length) {
          selectSuggestion(filteredSuggestions.value[highlightedIndex.value]);
        } else {
          selectSuggestion();
        }
      }
    };

    const handleBackspace = (event) => {
      if (!inputValue.value && tags.value.length && event.key === "Backspace") {
        const updated = tags.value.slice(0, -1);
        tags.value = updated;
        emit("update:modelValue", updated);
      }
    };

    watch(
      () => props.modelValue,
      (newVal) => {
        tags.value = Array.isArray(newVal) ? [...newVal] : [];
      },
    );

    watch(canCreateNewTag, (canCreate) => {
      if (!canCreate && highlightedIndex.value === -1) {
        highlightedIndex.value = filteredSuggestions.value.length ? 0 : 0;
      }
    });

    watch(
      () => filteredSuggestions.value.length,
      (length) => {
        if (length === 0 && highlightedIndex.value > 0) {
          highlightedIndex.value = 0;
        } else if (length > 0 && highlightedIndex.value >= length) {
          highlightedIndex.value = length - 1;
        }
      },
    );

    onMounted(() => {
      fetchSuggestions();
    });

    return {
      inputRef,
      inputValue,
      tags,
      suggestions,
      filteredSuggestions,
      showDropdown,
      loading,
      loadError,
      highlightedIndex,
      canCreateNewTag,
      selectSuggestion,
      removeTag,
      focusInput,
      focus: focusInput,
      openDropdown,
      onBlur,
      handleKeydown,
      handleBackspace,
      retryFetch: () => fetchSuggestions(inputValue.value),
    };
  },
};
</script>

<style scoped>
.tag-selector {
  position: relative;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 4px;
  min-height: 36px;
}
.tag-selector.disabled {
  background: #f5f5f5;
  pointer-events: none;
  opacity: 0.7;
}
.tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}
.tag-chip {
  background: #e8f0fe;
  color: #1a1d21;
  border-radius: 999px;
  padding: 2px 8px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.85rem;
}
.tag-chip button {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  padding: 0;
  color: inherit;
}
.tag-input {
  border: none;
  outline: none;
  min-width: 120px;
  padding: 4px 0;
  flex: 1;
}
.helper-text {
  margin: 4px 0 0;
  font-size: 0.8rem;
  color: #666;
}
.error-banner {
  margin: 6px 0;
  padding: 6px 8px;
  background: #fee;
  border: 1px solid #f99;
  border-radius: 4px;
  font-size: 0.85rem;
  display: inline-flex;
  gap: 6px;
  align-items: center;
}
.suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ccc;
  border-top: none;
  max-height: 220px;
  overflow-y: auto;
  z-index: 10;
  border-radius: 0 0 4px 4px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.suggestion-item {
  padding: 8px;
  cursor: pointer;
  font-size: 0.9rem;
}
.suggestion-item.create-option {
  font-weight: 600;
}
.suggestion-item.highlighted,
.suggestion-item:hover {
  background: #f0f4ff;
}
.suggestion-item.loading,
.suggestion-item.no-results {
  font-style: italic;
  color: #666;
  cursor: default;
}
</style>
