<template>
  <div class="node-info-view">
    <!-- Title + Favourite Button -->
    <div class="title-row" v-if="isAllowed('title')">
      <h2 class="title">{{ node.title }}</h2>
      <button
        v-if="!isBrandNewNode"
        class="favourite-btn"
        :title="isFavourite ? 'Remove from favourites' : 'Add to favourites'"
        @click="toggleFavourite"
        style=" margin: 0; padding: 0.5em;font-size: 1.5rem; color: gold; background: none; border: none; cursor: pointer;"
      >
        {{ isFavourite ? '★' : '☆' }}
      </button>
    </div>
    <!-- Type -->
    <div>
      <strong :title="nodeTypeTooltip">Type:</strong>
      {{ capitalise(node.node_type) }}<br>
    </div>
    <!-- Scope -->
    <div v-if="isAllowed('scope')">
      <strong :title="tooltips.node.scope">Scope:</strong>
      {{ node.scope }}<br>
    </div>
    <!-- Status -->
    <div v-if="isAllowed('status')">
      <strong :title="tooltips.node.status">Status:</strong>
      {{ formatStatus(node.status) }}<br>
    </div>

    <!-- References -->
    <div v-if="isAllowed('references') && node.references?.length">
      <strong :title="tooltips.node.references">References:</strong><br>
      <ul class="references-list">
        <li
          v-for="reference in node.references.filter(ref => ref.trim())"
          :key="reference"
        >
          {{ reference.trim() }}
        </li>
      </ul>
    </div>
    <!-- Description -->
    <div v-if="isAllowed('description')">
      <strong :title="tooltips.node.description">Description:</strong>
      {{ node.description ? node.description : "" }}
    </div>
    <!-- Tags -->
    <div class="tags-container" v-if="isAllowed('tags') && node.tags?.length">
      <strong :title="tooltips.node.tags">Tags:</strong>
      <span v-for="tag in node.tags" :key="tag" class="tag">{{ tag }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, toRefs } from "vue";
import { useConfig } from "../../composables/useConfig";
import tooltips from "../../assets/tooltips.json";

interface Node {
  node_id: number | string;
  node_type: string;
  title?: string;
  scope?: string;
  status?: string;
  description?: string;
  tags?: string[];
  references?: string[];
}

const props = defineProps<{
  node: Node;
  isFavourite?: boolean;
  isBrandNewNode?: boolean;
  toggleFavourite?: () => void;
}>();
const { node, isFavourite, isBrandNewNode, toggleFavourite } = toRefs(props);

const { nodeTypes, load } = useConfig();
onMounted(load);

const allowed = computed(() => {
  // Ensure nodeTypes have been loaded and node.node_type exists.
  if (!nodeTypes.value || !node.value.node_type) return [];
  return nodeTypes.value[node.value.node_type].properties || [];
});

function isAllowed(prop: string): boolean {
  return allowed.value.includes(prop);
}

function formatStatus(status?: string): string {
  if (!status || status === "unspecified") {
    return tooltips.node.status;
  }
  return capitalise(status);
}

function capitalise(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

const nodeTypeTooltip = computed(() => {
  return tooltips.node[node.value.node_type] || tooltips.node.type;
});
</script>

<style scoped>
.title-row {
  display: flex;
  align-items: center;
  gap: 0.5em;
}

.favourite-btn:hover {
  opacity: 0.8;
}
</style>