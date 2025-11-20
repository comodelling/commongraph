<template>
  <div
    class="tag-selector"
    :class="{ disabled }"
    ref="containerRef"
    @click="focusInput"
  >
    <div class="tags-row">
      <span
        v-for="(tag, index) in tags"
        :key="`${tag}-${index}`"
        class="tag-chip"
        role="button"
        tabindex="0"
        title="Click to edit tag"
        @click="startTagEdit(tag, index)"
        @keydown.enter.prevent="startTagEdit(tag, index)"
      >
        <span class="chip-text">{{ tag }}</span>
        <button
          type="button"
          class="remove-tag"
          @click.stop="removeTag(index)"
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
        title="Type to search or create tags."
        @input="onInput"
        @keydown="handleKeydown"
        @keydown.backspace="handleBackspace"
        @focus="openDropdown"
        @blur="onBlur"
        class="tag-input"
      />
    </div>
    <!-- <p class="helper-text">
      Click an existing tag to change it, or press Enter to add a new one.
    </p> -->
    <div v-if="loadError" class="error-banner">
      Failed to load suggestions.
      <button type="button" class="retry-button" @click.stop="retryFetch">
        Retry
      </button>
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
import { ref, computed, watch, onMounted, nextTick } from "vue";
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
    editRequest: {
      type: Object,
      default: null,
    },
  },
  emits: ["update:modelValue", "blur", "keydown", "edit-request-consumed"],
  setup(props, { emit }) {
    const { debugLog } = useLogging("TagSelector");
    const containerRef = ref(null);
    const inputRef = ref(null);
    const inputValue = ref("");
    const tags = ref([...props.modelValue]);
    const pendingInsertIndex = ref(null);
    const editingTagOriginal = ref(null);
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
      const updated = [...tags.value];
      if (
        pendingInsertIndex.value !== null &&
        pendingInsertIndex.value <= updated.length
      ) {
        updated.splice(pendingInsertIndex.value, 0, tagToAdd);
      } else {
        updated.push(tagToAdd);
      }
      tags.value = updated;
      emit("update:modelValue", updated);
      inputValue.value = "";
      showDropdown.value = true;
      if (!suggestions.value.length) {
        fetchSuggestions();
      }
      highlightedIndex.value = canCreateNewTag.value ? -1 : 0;
      pendingInsertIndex.value = null;
      editingTagOriginal.value = null;
    };

    const removeTag = (index) => {
      const updated = tags.value.filter((_, idx) => idx !== index);
      tags.value = updated;
      emit("update:modelValue", updated);
      if (
        pendingInsertIndex.value !== null &&
        index <= pendingInsertIndex.value
      ) {
        pendingInsertIndex.value = Math.max(0, pendingInsertIndex.value - 1);
      }
      nextTick(() => focusInput());
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
        const activeEl =
          typeof document !== "undefined" ? document.activeElement : null;
        const wrapper = containerRef.value;
        const stillInside = activeEl && wrapper && wrapper.contains(activeEl);
        if (stillInside) {
          return;
        }
        if (pendingInsertIndex.value !== null) {
          restoreEditingTag();
        }
        showDropdown.value = false;
        emit("blur");
      }, 150);
    };

    const cancelTagEditing = () => {
      if (pendingInsertIndex.value === null) return;
      if (
        editingTagOriginal.value === null ||
        editingTagOriginal.value === undefined
      ) {
        pendingInsertIndex.value = null;
        editingTagOriginal.value = null;
        inputValue.value = "";
        return;
      }
      const updated = [...tags.value];
      updated.splice(pendingInsertIndex.value, 0, editingTagOriginal.value);
      tags.value = updated;
      emit("update:modelValue", updated);
      pendingInsertIndex.value = null;
      inputValue.value = "";
      editingTagOriginal.value = null;
    };

    const restoreEditingTag = () => {
      cancelTagEditing();
    };

    const beginTagEdit = (tag, index) => {
      if (props.disabled) return false;
      if (
        typeof index !== "number" ||
        index < 0 ||
        index >= tags.value.length
      ) {
        return false;
      }
      pendingInsertIndex.value = index;
      editingTagOriginal.value = tag;
      const updated = [...tags.value];
      updated.splice(index, 1);
      tags.value = updated;
      emit("update:modelValue", updated);
      inputValue.value = tag || "";
      showDropdown.value = true;
      highlightedIndex.value = canCreateNewTag.value ? -1 : 0;
      scheduleFetch(tag);
      nextTick(() => focusInput());
      return true;
    };

    const startTagEdit = (tag, index) => {
      beginTagEdit(tag, index);
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
      } else if (event.key === "Escape") {
        if (inputValue.value) {
          inputValue.value = "";
          highlightedIndex.value = canCreateNewTag.value ? -1 : 0;
        } else {
          cancelTagEditing();
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
        pendingInsertIndex.value = null;
        editingTagOriginal.value = null;
      }
    };

    watch(
      () => props.modelValue,
      (newVal) => {
        tags.value = Array.isArray(newVal) ? [...newVal] : [];
        if (pendingInsertIndex.value !== null) {
          pendingInsertIndex.value = Math.min(
            pendingInsertIndex.value,
            tags.value.length,
          );
        }
      },
    );

    watch(
      () => props.editRequest,
      (request) => {
        if (!request || typeof request.index !== "number") {
          return;
        }
        const idx = request.index;
        if (idx < 0 || idx >= tags.value.length) {
          emit("edit-request-consumed");
          return;
        }
        const tagValue = tags.value[idx];
        beginTagEdit(tagValue, idx);
        emit("edit-request-consumed");
      },
      { immediate: true },
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
      containerRef,
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
      startTagEdit,
    };
  },
};
</script>

<style scoped>
.tag-selector {
  position: relative;
  border: 1px solid var(--tag-surface-border, #ccc);
  border-radius: 4px;
  padding: 4px 6px;
  min-height: 38px;
  background: var(--tag-surface-bg, #fff);
  color: var(--text-color, #1c1c1c);
}
.tag-selector.disabled {
  background: var(--tag-disabled-bg, #f5f5f5);
  pointer-events: none;
  opacity: 0.7;
}
.tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: flex-start;
}
.tag-chip {
  background: var(--tag-chip-bg, #edf2ff);
  color: var(--tag-chip-text, #273445);
  border-radius: 999px;
  padding: 3px 6px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.84rem;
  border: 1px solid var(--tag-chip-border, #cfd8f3);
  cursor: pointer;
  transition: background 0.15s ease;
  flex: 0 0 auto;
  width: auto;
  max-width: 100%;
  line-height: 1.2;
}
.tag-chip:focus,
.tag-chip:hover {
  outline: none;
  background: var(--tag-chip-hover-bg, #dfe8ff);
}
.chip-text {
  max-width: 180px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 0 1 auto;
}
.tag-chip button {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 0.95rem;
  line-height: 1;
  padding: 0;
  color: inherit;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  margin-left: 2px;
}
.tag-input {
  border: none;
  outline: none;
  min-width: 90px;
  padding: 14px 8px;
  flex: 1;
  font-size: 0.9rem;
  background: var(--tag-input-bg, transparent);
  color: var(--tag-input-text, inherit);
}
.helper-text {
  margin: 4px 0 0;
  font-size: 0.8rem;
  color: var(--tag-helper-text, #666);
}
.error-banner {
  margin: 6px 0;
  padding: 6px 8px;
  background: var(--tag-error-bg, #fee);
  border: 1px solid var(--tag-error-border, #f99);
  border-radius: 4px;
  font-size: 0.85rem;
  display: inline-flex;
  gap: 6px;
  align-items: center;
}
.retry-button {
  border: 1px solid var(--tag-error-border, #f99);
  background: var(--tag-surface-bg, #fff);
  border-radius: 3px;
  padding: 2px 6px;
  cursor: pointer;
  font-size: 0.8rem;
}
.suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--tag-dropdown-bg, #fff);
  border: 1px solid var(--tag-dropdown-border, #ccc);
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
  color: var(--tag-chip-text, #273445);
}
.suggestion-item.create-option {
  font-weight: 600;
}
.suggestion-item.highlighted,
.suggestion-item:hover {
  background: var(--tag-dropdown-hover-bg, #f0f4ff);
}
.suggestion-item.loading,
.suggestion-item.no-results {
  font-style: italic;
  color: var(--tag-helper-text, #666);
  cursor: default;
}
</style>
