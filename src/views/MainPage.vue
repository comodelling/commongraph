<template>
  <div class="main-page">
    <div class="content">
      <h1>ObjectiveNet</h1>
      <input v-model="searchQuery" placeholder="Search for proposals..." />
      <button @click="search">Search</button>
      <div v-if="groupedNodes">
        <div v-for="(nodes, scope) in groupedNodes" :key="scope" class="scope-group">
          <h3>{{ scope }}</h3>
          <ul>
            <li v-for="node in nodes" :key="node.id" class="node-item">
              <a :href="`${node.node_id}`">{{ node.title }}</a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
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
  methods: {
    //TODO: warn against empty search query
    //TODO: display messages depending on results
    //TODO: look into linked nodes too.
    async search() {
      try {
        console.log('Base URL:', import.meta.env.VITE_BACKEND_URL);
        console.log('Search Query:', this.searchQuery);
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
};
</script>

<style scoped>
.main-page {
  border: 1px solid #ccc;
  padding: 20px;
  padding-left: 100px;
  display: flex;                  /* Use flexbox for horizontal layout */
  flex-grow: 1;                   /* Make the proposal detail take available space */
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

.node-item:hover {
  background-color: #f0f0f0;
}
</style>