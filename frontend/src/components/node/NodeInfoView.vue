<template>
  <div class="node-info-view">
    <!-- Title -->
    <div class="field-row" v-if="isAllowed('title')">
      <strong>Title:</strong>
      <span class="field-value">{{ node.title }}</span>
    </div>
    <!-- Type -->
    <div class="field-row">
      <strong :title="nodeTypeTooltip">Type:</strong>
      <span class="field-value">{{ capitalise(node.node_type) }}</span>
    </div>
    <!-- Scope -->
    <div class="field-row" v-if="isAllowed('scope')">
      <strong :title="tooltips.node.scope">Scope:</strong>
      <span class="field-value">{{ node.scope }}</span>
    </div>
    <!-- Status -->
    <div class="field-row" v-if="isAllowed('status')">
      <strong :title="tooltips.node.status">Status:</strong>
      <span class="field-value">{{ formatStatus(node.status) }}</span>
    </div>

    <!-- References -->
    <div
      class="field-row"
      v-if="isAllowed('references') && node.references?.length"
    >
      <strong :title="tooltips.node.references">References:</strong>
      <div class="field-value">
        <ul class="references-list">
          <li
            v-for="reference in node.references.filter((ref) => ref.trim())"
            :key="reference"
          >
            {{ reference.trim() }}
          </li>
        </ul>
      </div>
    </div>
    <!-- Description -->
    <div class="field-row" v-if="isAllowed('description') && node.description">
      <strong :title="tooltips.node.description">Description:</strong>
      <span class="field-value">{{ node.description }}</span>
    </div>
    <!-- Tags -->
    <div class="field-row" v-if="isAllowed('tags') && node.tags?.length">
      <strong :title="tooltips.node.tags">Tags:</strong>
      <div class="field-value tags-container">
        <span v-for="tag in node.tags" :key="tag" class="tag">{{ tag }}</span>
      </div>
    </div>
    <!-- License Notice -->
    <p class="license-notice" v-if="shouldShowLicenseNotice">
      Node descriptions are available under the
      <a
        :href="getLicenseUrl(license)"
        target="_blank"
        rel="noopener noreferrer"
      >
        {{ license }}
      </a>
      license.
    </p>
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

const { nodeTypes, load, license, getLicenseUrl } = useConfig();
onMounted(load);

const allowed = computed(() => {
  // Ensure nodeTypes have been loaded and node.node_type exists.
  if (!nodeTypes.value || !node.value.node_type) return [];
  return nodeTypes.value[node.value.node_type].properties || [];
});

const descriptionAllowed = computed(() =>
  allowed.value.includes("description"),
);
const hasDescriptionValue = computed(() => {
  const desc = node.value.description;
  return typeof desc === "string" && desc.trim().length > 0;
});

const shouldShowLicenseNotice = computed(() => {
  return Boolean(
    license.value && descriptionAllowed.value && hasDescriptionValue.value,
  );
});

function isAllowed(prop: string): boolean {
  return allowed.value.includes(prop);
}

function formatStatus(status?: string): string {
  if (!status) {
    return tooltips.node.status;
  }
  return capitalise(status);
}

function capitalise(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

const nodeTypeTooltip = computed(() => {
  return (tooltips.node as any)[node.value.node_type] || tooltips.node.type;
});
</script>

<style scoped>
.field-row {
  display: flex;
  align-items: flex-start;
  margin: 8px 0;
  gap: 10px;
}

.field-row strong {
  min-width: 80px;
  flex-shrink: 0;
}

.field-value {
  flex: 1;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

/* License notice styling */
.license-notice {
  font-size: 0.75rem;
  color: #999;
  margin-top: 20px;
  line-height: 1.3;
}

.license-notice a {
  color: #0066cc;
  text-decoration: none;
  font-weight: 500;
}

.license-notice a:hover {
  text-decoration: underline;
}
</style>
