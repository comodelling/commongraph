<template>
  <div class="search-page">
    <div class="content">
      <!-- <h1>Search Results</h1> -->
      <SearchBar :initialQuery="searchQuery" @search="(query) => search(query)" />
      <div class="filters">
        <strong> Node Type: </strong>
        <label>
          <input type="checkbox" v-model="nodeTypes.objective" /> Objectives
        </label>
        <label>
          <input type="checkbox" v-model="nodeTypes.action" /> Actions
        </label>
        <label>
          <input type="checkbox" v-model="nodeTypes.change" /> Changes
        </label>
        <label>
          <input type="checkbox" v-model="nodeTypes.proposal" /> Proposals
        </label>
      </div>
      <h2>Search Results</h2>
      <div v-if="!nodes.length && searchQuery">
        <p>No results found for "{{ searchQuery }}"</p>
      </div>
      <div v-if="groupedNodes">
        <div v-for="(nodes, scope) in groupedNodes" :key="scope" class="scope-group">
          <h4>{{ scope }}</h4>
          <ul>
            <li v-for="node in nodes" :key="node.id" class="node-item">
              <a :href="`/node/${node.node_id}`">{{ node.title }}</a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import qs from 'qs';
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
      nodeTypes: {
        objective: true,
        change: false,
        action: false,
        proposal: false,
      },
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
      const nodeTypes = Object.keys(this.nodeTypes).filter(type => this.nodeTypes[type]);
      if (!nodeTypes.length) {
        console.warn('Select a node type to search');
        this.nodes = [];
        return;
      }
      this.searchQuery = query;
      if (!this.searchQuery.trim()) {
        console.warn('Empty search query, will fetch all objectives');
      }
      try {
        if (this.searchQuery !== this.$route.params.searchQuery) {
          this.$router.push({ name: 'SearchPage', params: { searchQuery: this.searchQuery } });
        }

        console.log('searching for nodes with types:', nodeTypes);
        const response = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/nodes`, {
          params: {
            title: this.searchQuery,
            node_types: nodeTypes, //nodeTypes,
          },
          paramsSerializer: params => {
            return qs.stringify(params, { arrayFormat: 'repeat' });
          },
          // paramsSerializer: params => {
          //    return new URLSearchParams(params).toString();
          // }
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

.filters {
  margin-bottom: 20px;
  font-size: 11px;
}

.scope-group {
  margin-bottom: 20px;
}

.node-item {
  cursor: pointer;
  transition: background-color 0.3s;
  margin-bottom: 5px;
  font-size: 12px;
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