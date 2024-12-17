<template>
  <div class="main-page">
    <div class="content">
      <h1>ObjectiveNet</h1>
      <SearchBar @search="goToSearch" />
    </div>
  </div>
</template>

<script>
import SearchBar from "../components/SearchBar.vue";

export default {
  components: {
    SearchBar,
  },
  methods: {
    goToSearch(query) {
      this.$router.push({ name: "SearchPage", params: { searchQuery: query } });
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
