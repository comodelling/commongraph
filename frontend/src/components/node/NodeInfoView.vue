<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md

SPDX-License-Identifier: AGPL-3.0-or-later
-->
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
    <!-- Custom option-based properties -->
    <template
      v-for="customProp in customPropertyEntries"
      :key="customProp.name"
    >
      <div class="field-row" v-if="hasCustomValue(customProp.name)">
        <strong
          :title="customProp.config.question || capitalise(customProp.name)"
        >
          {{ capitalise(customProp.name) }}:
        </strong>
        <span class="field-value">
          {{
            getCustomPropertyDisplay(
              customProp.config,
              getCustomValue(customProp.name),
            )
          }}
        </span>
      </div>
    </template>
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

type CustomPropertyEntry = {
  name: string;
  config: Record<string, any>;
};

const customPropertyEntries = computed<CustomPropertyEntry[]>(() => {
  if (!nodeTypes.value || !node.value.node_type) return [];
  const typeDef = nodeTypes.value[node.value.node_type] || {};
  const propertyOptions: Record<string, any> = typeDef.property_options || {};
  return Object.entries(propertyOptions)
    .filter(([name, config]) => {
      const optionMap = (config as Record<string, any>)?.options || {};
      return allowed.value.includes(name) && Object.keys(optionMap).length > 0;
    })
    .map(([name, config]) => ({ name, config: config as Record<string, any> }));
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

function formatCustomPropertyLabel(name: string, config: Record<string, any>) {
  // formatCustomPropertyLabel removed: label now always uses property name
}

function getCustomValue(propName: string): any {
  return (node.value as Record<string, any>)[propName];
}

function hasCustomValue(propName: string): boolean {
  const value = getCustomValue(propName);
  if (value === undefined || value === null) {
    return false;
  }
  if (typeof value === "string") {
    return value.trim().length > 0;
  }
  return true;
}

function getCustomPropertyDisplay(
  config: Record<string, any>,
  value: any,
): string {
  if (value === undefined || value === null) {
    return "";
  }
  const options = config?.options || {};
  const key = typeof value === "string" ? value : String(value);
  return options[key] ?? String(value);
}
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
