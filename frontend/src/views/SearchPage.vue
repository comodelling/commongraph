<!-- filepath: /Users/mario/CODE/objectivenet/frontend/src/views/SearchPage.vue -->
<template>
  <div class="search-page">
    <div class="search-header">
      <!-- Center the search bar -->
      <div class="centered-search">
        <SearchBar :initialQuery="title" @search="search" />
      </div>
    </div>
    <div class="search-content">
      <div class="results-column">
        <h2>Search Results</h2>
        <div v-if="!nodes.length && title">
          <p>No results found for "{{ title }}"</p>
        </div>
        <div v-if="groupedNodes">
          <div
            v-for="(nodes, scope) in groupedNodes"
            :key="scope"
            class="scope-group"
          >
            <h4>{{ scope }}</h4>
            <ul>
              <li v-for="node in nodes" :key="node.id" class="node-item">
                <a :href="`/node/${node.node_id}`">{{ node.title }}</a>
              </li>
            </ul>
          </div>
        </div>
      </div>
      <div class="visualization-column">
        <SupportView :nodes="nodes" />
      </div>
    </div>
  </div>
</template>

<script>
import api from "../axios";
import qs from "qs";
import { useRouter, useRoute } from "vue-router";
import SearchBar from "../components/SearchBar.vue";
import SupportView from "../components/SupportHistogram.vue";

export default {
  components: { SearchBar, SupportView },
  data() {
    return {
      title: "",
      nodes: [],
    };
  },
  computed: {
    groupedNodes() {
      return this.nodes.reduce((groups, node) => {
        const scope = node.scope || "Uncategorized";
        if (!groups[scope]) {
          groups[scope] = [];
        }
        groups[scope].push(node);
        return groups;
      }, {});
    },
  },
  watch: {
    "$route.query": {
      immediate: true,
      handler(newQuery) {
        console.log("New query:", newQuery);
        if (!newQuery) return;
        const { title } = newQuery;
        this.title = title || "";
        this.performSearch();
      },
    },
  },
  methods: {
    search(parsedQuery) {
      console.log("Parsed query:", parsedQuery);
      const params = {};
      if (parsedQuery.text.length) {
        params.title = parsedQuery.text.join(" ");
      }
      if (parsedQuery.type.length) {
        params.node_type = parsedQuery.type;
      }
      if (parsedQuery.status.length) {
        params.status = parsedQuery.status;
      }
      if (parsedQuery.tag.length) {
        params.tags = parsedQuery.tag;
      }
      if (parsedQuery.scope) {
        params.scope = parsedQuery.scope;
      }
      this.$router.push({ name: "SearchPage", query: params });
    },
    async performSearch() {
      try {
        const { title, node_type, status, tags, scope } = this.$route.query;
        const tagsArray = tags
          ? typeof tags === "string"
            ? tags
                .split(",")
                .map((tag) => tag.trim())
                .filter((tag) => tag)
            : tags
          : [];
        console.log("Searching for nodes with:", {
          title,
          node_type,
          status,
          tags: tagsArray,
          scope,
        });
        const startTime = performance.now();
        const response = await api.get(
          `${import.meta.env.VITE_BACKEND_URL}/nodes`,
          {
            params: {
              title: title,
              node_type: node_type,
              status: status,
              tags: tagsArray.length ? tagsArray : undefined,
              scope: scope,
            },
            paramsSerializer: (params) =>
              qs.stringify(params, { arrayFormat: "repeat" }),
          },
        );
        const endTime = performance.now();
        console.log(`Search completed in ${endTime - startTime} milliseconds`);
        this.nodes = response.data;
      } catch (error) {
        console.error("Error fetching nodes:", error);
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
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.search-header {
  padding: 20px;
  padding-left: 100px;
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--background-color);
}

.centered-search {
  display: flex;
  justify-content: center;
}

.centered-search > * {
  width: 600px; /* set desired width */
}

.search-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.results-column {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  padding-left: 100px;
  border-right: 1px solid #ddd;
  /* border: 1px solid blue; */
}

.visualization-column {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  /* height: 100vh; */
  /* border: 1px solid red; */
}

.scope-group {
  margin-bottom: 20px;
}

.node-item {
  cursor: pointer;
  transition: var(--background-color) 0.3s;
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
