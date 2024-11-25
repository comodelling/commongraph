<template>
  <div class="search-page">
    <div class="content">
      <h1>Search Results</h1>
      <SearchBar :initialQuery="searchQuery" @search="(query) => search(query)" />
      <div v-if="groupedNodes">
        <div v-for="(nodes, scope) in groupedNodes" :key="scope" class="scope-group">
          <h3>{{ scope }}</h3>
          <ul>
            <li v-for="node in nodes" :key="node.id" class="node-item">
              <a :href="`/focus/${node.node_id}`">{{ node.title }}</a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { useRouter, useRoute } from 'vue-router';
import SearchBar from '../components/SearchBar.vue';

export default {
  components: {
    SearchBar,
  },
  data() {
    return {
      searchQuery: '',
      nodes: [],
    };
  },
  computed: {
    groupedNodes() {
      return this.nodes.reduce((groups, node) => {
        const scope = node.scope || 'Uncategorized';
        if (!groups[scope]) {
          groups[scope] = [];
        }
        groups[scope].push(node);
        return groups;
      }, {});
    },
  },
  watch: {
    '$route.params.searchQuery': {
      immediate: true,
      handler(newQuery) {
        if (newQuery !== this.searchQuery) {
          this.searchQuery = newQuery || '';
          this.search(this.searchQuery);
        }
      },
    },
  },
  methods: {
    async search(query) {
      if (query === this.searchQuery) {
        return;
      }
      this.searchQuery = query;
      if (!this.searchQuery.trim()) {
        this.nodes = [];
        return;
      }
      try {
        if (this.searchQuery !== this.$route.params.searchQuery) {
          this.$router.push({ name: 'SearchPage', params: { searchQuery: this.searchQuery } });
        }
        const response = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/nodes`, {
          params: {
            title: this.searchQuery,
            node_type: "proposal",
          },
        });
        this.nodes = response.data;
      } catch (error) {
        console.error('Error fetching nodes:', error);
      }
    },
  },
  setup() {
    const router = useRouter();
    const route = useRoute();
    return { router, route };
  },
};
</script>

<style scoped>
.search-page {
  padding: 20px;
  padding-left: 100px;
  display: flex;
  flex-grow: 1;
  text-align: left;
}

.scope-group {
  margin-bottom: 20px;
}

.node-item {
  cursor: pointer;
  transition: background-color 0.3s;
  margin-bottom: 5px;
  font-size: 14px;
}

.node-item a {
  text-decoration: none;
}

.node-item a:hover {
  text-decoration: underline;
}

.node-item:hover {
  background-color: #f0f0f0;
}
</style>