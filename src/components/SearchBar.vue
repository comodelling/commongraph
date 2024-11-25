<template>
    <div class="search-bar">
      <input v-model="searchQuery" @input="updateSearchQuery" @keyup.enter="search" placeholder="Search for proposals..." />
      <button @click="search">Search</button>
    </div>
  </template>
  
  <script>
  export default {
    props: {
      initialQuery: {
        type: String,
        default: '',
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
        this.$emit('search', this.searchQuery);
      },
    },
  };
  </script>
  
  <style scoped>
  .search-bar {
    display: flex;
    align-items: center;
    width: 400px; /* Adjust the width as needed */
  }
  .search-bar input {
    flex-grow: 1;
    margin-right: 10px;
    padding: 5px;
    /* font-size: 16px; */
    width: 400px; /* Set a specific width for the input field */
  }
  .search-bar button {
    padding: 6px 10px;
    /* font-size: 16px; */
  }
  </style>