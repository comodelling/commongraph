<template>
  <div class="main-page">
    <div class="content">
      <h1>ObjectiveNet</h1>
      <!-- Pass the custom class directly to SearchBar -->
      <SearchBar
        class="wide-search"
        @search="goToSearch"
        style="max-width: 600px; width: 450px"
      />
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
  display: flex;
  align-items: center;
  justify-content: center;
  height: 80vh;
  text-align: center;
}
</style>
