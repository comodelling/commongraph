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
      this.$router.push({ name: "SearchPage", query: { title: query } });
    },
  },
};
</script>

<style scoped>
.main-page {
  padding: 30px 120px;
  /* padding-left: 100px; */
}
</style>
