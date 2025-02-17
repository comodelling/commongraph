<template>
  <div class="search-page">
    <div class="search-header">
      <!-- Search bar and parameters stay fixed -->
      <SearchBar :initialQuery="title" @search="search" />
      <div class="filters">
        <strong> Type: </strong>
        <label>
          <input type="checkbox" v-model="nodeTypes.objective" /> Objectives
        </label>
        <label>
          <input type="checkbox" v-model="nodeTypes.action" /> Actions
        </label>
        <label>
          <input type="checkbox" v-model="nodeTypes.potentiality" />
          Potentialities
        </label>
        <label>
          <input type="checkbox" v-model="nodeTypes.change" /> Changes
        </label>
        <label>
          <input type="checkbox" v-model="nodeTypes.proposal" /> Proposals
        </label>
      </div>
      <div class="filters">
        <strong> Status: </strong>
        <label>
          <input type="checkbox" v-model="nodeStatus.draft" /> Draft
        </label>
        <label>
          <input type="checkbox" v-model="nodeStatus.live" /> Live
        </label>
        <label>
          <input type="checkbox" v-model="nodeStatus.completed" /> Completed
        </label>
        <label>
          <input type="checkbox" v-model="nodeStatus.unspecified" /> Unspecified
        </label>
        <label>
          <input type="checkbox" v-model="nodeStatus.legacy" /> Legacy
        </label>
      </div>
      <div class="filters">
        <strong> Tags: </strong>
        <input type="text" v-model="tagFilter" placeholder="e.g. tag1, tag2" />
      </div>
    </div>
    <div class="results">
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
  </div>
</template>

<script>
import api from "../axios";
import qs from "qs";
import { useRouter, useRoute } from "vue-router";
import SearchBar from "../components/SearchBar.vue";

export default {
  components: {
    SearchBar,
  },
  data() {
    return {
      title: "",
      nodes: [],
      nodeTypes: {
        objective: true,
        action: true,
        potentiality: false,
        change: false,
        proposal: false,
      },
      nodeStatus: {
        unspecified: true,
        draft: true,
        live: true,
        completed: true,
        legacy: false,
      },
      tagFilter: "",
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
        console.log("new query:", newQuery);
        if (!newQuery) return;
        const { title, nodeTypes, nodeStatus, tags } = newQuery;
        if (title !== this.title) {
          this.title = title || "";
          this.nodeTypes = nodeTypes ? JSON.parse(nodeTypes) : this.nodeTypes;
          this.nodeStatus = nodeStatus
            ? JSON.parse(nodeStatus)
            : this.nodeStatus;
          this.tagFilter = tags || "";
          this.performSearch();
        }
      },
    },
  },
  methods: {
    async search(query) {
      console.log("searching for nodes with query:", query);
      const nodeTypes = Object.keys(this.nodeTypes).filter(
        (type) => this.nodeTypes[type],
      );
      const nodeStatus = Object.keys(this.nodeStatus).filter(
        (type) => this.nodeStatus[type],
      );
      const tags = this.tagFilter
        .split(",")
        .map((tag) => tag.trim())
        .filter((tag) => tag);

      const params = {};
      if (query.trim()) params.title = query;
      if (
        nodeTypes.length &&
        nodeTypes.length !== Object.keys(this.nodeTypes).length
      )
        params.node_type = nodeTypes;
      if (
        nodeStatus.length &&
        nodeStatus.length !== Object.keys(this.nodeStatus).length
      )
        params.status = nodeStatus;
      if (tags.length) params.tags = tags;

      this.$router.push({
        name: "SearchPage",
        query: params,
      });
    },
    async performSearch() {
      try {
        const { title, nodeTypes, nodeStatus, tags } = this.$route.query;
        const tagsArray = tags
          ? tags
              .split(",")
              .map((tag) => tag.trim())
              .filter((tag) => tag)
          : [];

        console.log("searching for nodes with title:", title);
        console.log("searching for nodes with types:", nodeTypes);
        console.log("searching for nodes with status:", nodeStatus);
        console.log("searching for nodes with tags:", tagsArray);

        const startTime = performance.now();

        const response = await api.get(
          `${import.meta.env.VITE_BACKEND_URL}/nodes`,
          {
            params: {
              title: title,
              node_type: nodeTypes,
              status: nodeStatus,
              tags: tagsArray.length ? tagsArray : undefined,
            },
            paramsSerializer: (params) => {
              return qs.stringify(params, { arrayFormat: "repeat" });
            },
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
  /* Make sure header remains visible on scroll */
  position: sticky;
  top: 0;
  z-index: 10;
}

.results {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  padding-left: 100px;
}

.filters {
  margin-bottom: 5px;
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
