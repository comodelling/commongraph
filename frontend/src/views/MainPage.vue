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
      <div v-if="quote" class="quote-container">
        <blockquote>{{ quote.quote }}</blockquote>
        <p>
          &mdash; {{ quote.author
          }}<span v-if="quote.where">, in {{ quote.where }}</span>
        </p>
        <small v-if="quote.comments">({{ quote.comments }})</small>
      </div>
    </div>
  </div>
</template>

<script>
import { onMounted } from "vue";
import SearchBar from "../components/common/SearchBar.vue";
import { buildSearchParams } from "../utils/searchParser.js";
import { useConfig } from "../composables/useConfig";
import api from "../api/axios.js";

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
  mounted() {
    this.fetchQuote();
  },
  methods: {
    goToSearch(parsedQuery) {
      const params = buildSearchParams(parsedQuery);
      this.$router.push({ name: "SearchPage", query: params });
    },
    async fetchQuote() {
      try {
        const response = await api.get(`/quote`);
        this.quote = response.data;
        console.log("Quote fetched:", this.quote);
      } catch (error) {
        console.error("Error fetching quote:", error);
      }
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

.quote-container blockquote {
  margin: 0;
  font-style: italic;
}

.quote-container p {
  margin: 0;
}
</style>
