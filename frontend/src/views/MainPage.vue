<template>
  <div class="main-page">
    <div class="content">
      <h1>{{ platformName }}</h1>
      <div class="search-container">
        <SearchBar
          class="wide-search"
          @search="goToSearch"
          style="max-width: 600px; width: 450px"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { onMounted } from "vue";
import SearchBar from "../components/common/SearchBar.vue";
import { buildSearchParams } from "../utils/searchParser.js";
import { useConfig } from "../composables/useConfig";

export default {
  components: { SearchBar },
  data() {
    return {
      quote: null,
    };
  },
  setup() {
    const { platformName, load } = useConfig();
    onMounted(load);
    return { platformName };
  },
  methods: {
    goToSearch(parsedQuery) {
      const params = buildSearchParams(parsedQuery);
      this.$router.push({ name: "SearchPage", query: params });
    },
  },
};
</script>

<style scoped>
.main-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
}

.content {
  text-align: center;
  margin: 0 20px;
}

.search-container {
  display: flex;
  justify-content: center;
  margin-bottom: 100px;
}

</style>
