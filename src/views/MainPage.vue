<template>
  <div class="main-page">
    <div class="content">
      <h1>ObjectiveNet</h1>
      <input v-model="searchQuery" placeholder="Search for proposals..." />
      <button @click="goToSearch">Search</button>
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
    goToSearch() {
      if (this.searchQuery.trim()) {
        this.$router.push({ name: 'SearchPage', params: { searchQuery: this.searchQuery } });
      } else {
        alert('Please enter a search query.');
      }
    },
  },
};
</script>

<style scoped>
.main-page {
  padding: 20px;
  padding-left: 100px;
  display: flex;
  flex-grow: 1;
  text-align: left;
}
</style>