<template>
  <div class="main-page">
    <div class="content">
      <h1>ObjectiveNet</h1>
      <input v-model="searchQuery" placeholder="Search for proposals..." />
      <button @click="search">Search</button>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      searchQuery: '',
    };
  },
  methods: {
    search() {
      console.log('Searching for:', this.searchQuery);
    },
  },
};
</script>

<style scoped>
.main-page {
  border: 1px solid #ccc;         /* Border for main page */
  padding: 20px;                  /* Padding for content */
  padding-left: 100px;
  display: flex;                  /* Use flexbox for horizontal layout */
  flex-grow: 1;                   /* Make the proposal detail take available space */
  text-align: center;

}
</style>