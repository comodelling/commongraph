<template>
  <div class="search-bar">
    <input
      v-model="searchQuery"
      @input="updateSearchQuery"
      @keyup.enter="search"
      :placeholder="placeholder"
    />
    <button v-if="showButton" @click="search" class="search-button">🔍</button>
  </div>
</template>

<script>
export default {
  props: {
    initialQuery: {
      type: String,
      default: "",
    },
    placeholder: {
      type: String,
      default: "Search for nodes...",
    },
    showButton: {
      type: Boolean,
      default: true,
    },
  },
  data() {
    return {
      searchQuery: this.initialQuery,
    };
  },
  methods: {
    updateSearchQuery(event) {
      this.searchQuery = event.target.value;
    },
    search() {
      this.$emit("search", this.searchQuery);
    },
  },
};
</script>

<style scoped>
.search-bar {
  display: flex;
  align-items: center;
  max-width: 500px;
  min-width: 200px;
  border: 1px solid #ccc;
  border-radius: 3px;
  overflow: hidden;
}

.search-bar input {
  flex-grow: 1;
  padding: 8px;
  border: none;
  outline: none;
}

.search-button {
  background-color: rgb(39, 98, 162);
  border: none;
  color: white;
  cursor: pointer;
  font-size: 16px;
  border-radius: 1px;
  padding: 8px 12px;
  transition: var(--background-color) 0.2s ease;
}

.search-button:hover {
  background-color: rgb(39, 98, 162);
}
</style>
